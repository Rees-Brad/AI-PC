"""Local web application for the Campaign Agent."""

from __future__ import annotations

import json
import os
import re
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import unquote
from wsgiref.simple_server import make_server

from ai_pc_shared.llm.client import make_client

from ai_campaign.prompts import build_system_prompt

MAX_REQUEST_BYTES = 1_000_000
MAX_CAMPAIGN_BYTES = 100_000
MAX_PROPOSAL_BYTES = 1_000_000
CAMPAIGN_TOOL = {
    "name": "propose_campaign_files",
    "description": (
        "Propose complete Markdown campaign files for the user to review. "
        "Never claim these files were saved; the user must approve them."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            },
        },
        "required": ["summary", "files"],
    },
}


class CampaignApp:
    def __init__(self) -> None:
        self.campaign_root = Path(
            os.environ.get("AI_CAMPAIGN_ROOT", "~/ai-pc-campaigns")
        ).expanduser().resolve()
        self.campaign_root.mkdir(parents=True, exist_ok=True)
        self.model = os.environ.get("AI_CAMPAIGN_MODEL", "claude-sonnet-4-5")

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ["REQUEST_METHOD"]
        path = unquote(environ.get("PATH_INFO", "/"))
        try:
            if method == "GET" and path == "/":
                from importlib.resources import files

                body = files("ai_campaign").joinpath("static/index.html").read_bytes()
                return self._respond(start_response, HTTPStatus.OK, body, "text/html")
            if method == "GET" and path == "/api/campaigns":
                campaigns = sorted(
                    child.name
                    for child in self.campaign_root.iterdir()
                    if child.is_dir() and not child.is_symlink()
                )
                return self._json(start_response, HTTPStatus.OK, {"campaigns": campaigns})
            if method == "POST" and path == "/api/chat":
                payload = self._read_json(environ)
                result = self.chat(payload)
                return self._json(start_response, HTTPStatus.OK, result)
            if method == "POST" and path == "/api/apply":
                payload = self._read_json(environ)
                result = self.apply_proposal(payload)
                return self._json(start_response, HTTPStatus.OK, result)
            return self._json(start_response, HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except (ValueError, KeyError) as error:
            return self._json(start_response, HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except Exception as error:  # Keep the local UI useful when API setup is incomplete.
            return self._json(
                start_response,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": str(error) or "Campaign Agent request failed"},
            )

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get(
            "ANTHROPIC_AUTH_TOKEN"
        ):
            raise ValueError(
                "Anthropic authentication is not configured. Set ANTHROPIC_API_KEY "
                "in the terminal that starts the Campaign Agent, then restart the "
                "server. Do not enter the key in this chat."
            )

        mode = payload.get("mode")
        if mode not in {"review", "create", "update"}:
            raise ValueError("Choose Reviewer, Campaign Creation, or Update mode.")

        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("A conversation message is required.")
        clean_messages = [
            {"role": message["role"], "content": message["content"]}
            for message in messages[-40:]
            if isinstance(message, dict)
            and message.get("role") in {"user", "assistant"}
            and isinstance(message.get("content"), str)
        ]
        if not clean_messages or clean_messages[-1]["role"] != "user":
            raise ValueError("The latest conversation turn must be a user message.")

        campaign_name = payload.get("campaign", "")
        campaign_text = self._campaign_text(campaign_name) if campaign_name else ""
        review_document = payload.get("review_document", "")
        session_record = payload.get("session_record", "")
        if not all(isinstance(value, str) for value in (review_document, session_record)):
            raise ValueError("Review documents and session records must be text.")
        if len(review_document) + len(session_record) > MAX_CAMPAIGN_BYTES:
            raise ValueError("Supplied campaign material exceeds the 100 KB limit.")

        system = build_system_prompt(
            mode=mode,
            campaign_name=campaign_name,
            campaign_text=campaign_text,
            review_document=review_document,
            session_record=session_record,
        )
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": 3000,
            "system": system,
            "messages": clean_messages,
        }
        if mode in {"create", "update"}:
            kwargs["tools"] = [CAMPAIGN_TOOL]

        client = make_client()
        response = client.messages.create(**kwargs)
        proposal = None
        tool_use = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use is not None:
            proposal = self._validate_proposal(tool_use.input)
            follow_up = [*clean_messages, {"role": "assistant", "content": response.content}]
            follow_up.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": "Proposal prepared for user review; files have not been written.",
                        }
                    ],
                }
            )
            final_response = client.messages.create(
                model=self.model,
                max_tokens=3000,
                system=system,
                messages=follow_up,
            )
            text = "\n".join(
                block.text for block in final_response.content if block.type == "text"
            )
        else:
            text = "\n".join(block.text for block in response.content if block.type == "text")

        return {"reply": text, "proposal": proposal}

    def apply_proposal(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("mode") not in {"create", "update"}:
            raise ValueError("Campaign files can only be applied in Creation or Update mode.")
        campaign_name = self._safe_campaign_name(payload.get("campaign", ""))
        files = self._validate_proposal({"files": payload.get("files", []), "summary": ""})[
            "files"
        ]
        campaign_dir = self._campaign_path(campaign_name)
        if campaign_dir.is_symlink():
            raise ValueError("Refusing to write into a symbolic-link campaign folder.")
        prepared: list[tuple[Path, str]] = []
        for item in files:
            target_path = campaign_dir / item["path"]
            current = campaign_dir
            for part in Path(item["path"]).parts:
                current = current / part
                if current.is_symlink():
                    raise ValueError("Refusing to write through a symbolic link.")
            target = target_path.resolve()
            if not target.is_relative_to(campaign_dir):
                raise ValueError("A proposed path escapes the selected campaign folder.")
            if target.suffix.lower() != ".md":
                raise ValueError("Campaign proposals may only write Markdown files.")
            prepared.append((target, item["content"]))

        for target, content in prepared:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        return {"written": [str(path.relative_to(campaign_dir)) for path, _ in prepared]}

    def _campaign_text(self, campaign_name: str) -> str:
        safe_name = self._safe_campaign_name(campaign_name)
        campaign_dir = self._campaign_path(safe_name)
        if not campaign_dir.exists():
            return ""
        markdown_files = sorted(campaign_dir.rglob("*.md"))
        parts: list[str] = []
        total = 0
        for path in markdown_files:
            if path.is_symlink():
                continue
            content = path.read_text(encoding="utf-8")
            remaining = MAX_CAMPAIGN_BYTES - total
            if remaining <= 0:
                break
            content = content[:remaining]
            parts.append(f"\n--- {path.relative_to(campaign_dir)} ---\n{content}")
            total += len(content)
        return "".join(parts)

    def _campaign_path(self, name: str) -> Path:
        unresolved_path = self.campaign_root / name
        if unresolved_path.is_symlink():
            raise ValueError("Campaign folder cannot be a symbolic link.")
        path = unresolved_path.resolve()
        if not path.is_relative_to(self.campaign_root):
            raise ValueError("Campaign folder must be inside the configured campaign root.")
        return path

    @staticmethod
    def _safe_campaign_name(value: Any) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
            raise ValueError("Use a campaign folder name with letters, numbers, '-' or '_'.")
        return value

    @staticmethod
    def _validate_proposal(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict) or not isinstance(value.get("files"), list):
            raise ValueError("The agent returned an invalid file proposal.")
        if not value["files"] or len(value["files"]) > 50:
            raise ValueError("A proposal must contain between 1 and 50 files.")
        files = []
        total_size = 0
        seen: set[str] = set()
        for item in value["files"]:
            if not isinstance(item, dict):
                raise ValueError("Each proposed file must include a path and content.")
            path = item.get("path")
            content = item.get("content")
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("Each proposed file must include a path and text content.")
            normalized = Path(path)
            if normalized.is_absolute() or ".." in normalized.parts or not path.strip():
                raise ValueError("Proposed file paths must stay inside the campaign folder.")
            if path in seen:
                raise ValueError("A proposal cannot contain duplicate file paths.")
            seen.add(path)
            total_size += len(content.encode("utf-8"))
            files.append({"path": path, "content": content})
        if total_size > MAX_PROPOSAL_BYTES:
            raise ValueError("The proposed files exceed the 1 MB limit.")
        return {"summary": str(value.get("summary", "")), "files": files}

    @staticmethod
    def _read_json(environ: dict[str, Any]) -> dict[str, Any]:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError as error:
            raise ValueError("Invalid request size.") from error
        if length < 1 or length > MAX_REQUEST_BYTES:
            raise ValueError("Request must be between 1 byte and 1 MB.")
        try:
            payload = json.loads(environ["wsgi.input"].read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Request body must be valid JSON.") from error
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    @staticmethod
    def _json(start_response: Any, status: HTTPStatus, data: dict[str, Any]) -> list[bytes]:
        return CampaignApp._respond(
            start_response,
            status,
            json.dumps(data).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    @staticmethod
    def _respond(
        start_response: Any, status: HTTPStatus, body: bytes, content_type: str
    ) -> list[bytes]:
        start_response(
            f"{status.value} {status.phrase}",
            [
                ("Content-Type", content_type),
                ("Content-Length", str(len(body))),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
        return [body]


def main() -> None:
    app = CampaignApp()
    address = os.environ.get("AI_CAMPAIGN_HOST", "127.0.0.1")
    port = int(os.environ.get("AI_CAMPAIGN_PORT", "8765"))
    with make_server(address, port, app) as server:
        print(f"Campaign Agent ready at http://{address}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
