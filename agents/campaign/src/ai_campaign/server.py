"""Local web application for the Campaign Agent."""

from __future__ import annotations

import base64
import binascii
import json
import re
from http import HTTPStatus
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote
from wsgiref.simple_server import make_server

from pypdf import PdfReader

from ai_campaign.config import Settings, load_settings
from ai_campaign.prompts import build_system_prompt
from ai_pc_shared.llm.client import make_client

MAX_PROPOSAL_BYTES = 1_000_000
CAMPAIGN_TOOL = {
    "name": "propose_campaign_files",
    "strict": True,
    "description": (
        "Return one non-empty files array of complete Markdown files, each with "
        "a relative .md path and string content, plus a concise summary. "
        "Never claim these files were saved; the user must approve them."
    ),
    "input_schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary": {"type": "string", "minLength": 1},
            "files": {
                "type": "array",
                "minItems": 1,
                "maxItems": 50,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "path": {"type": "string", "minLength": 1},
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
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.campaign_root = self.settings.ai_campaign_root.expanduser().resolve()
        self.campaign_root.mkdir(parents=True, exist_ok=True)
        self.model = self.settings.ai_campaign_model
        self.max_context_bytes = self.settings.ai_campaign_max_context_kb * 1024
        self.max_request_bytes = max(1_000_000, self.max_context_bytes * 4 + 1_000_000)

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ["REQUEST_METHOD"]
        path = unquote(environ.get("PATH_INFO", "/"))
        try:
            if method == "GET" and path == "/":
                from importlib.resources import files

                body = files("ai_campaign").joinpath("static/index.html").read_bytes()
                return self._respond(start_response, HTTPStatus.OK, body, "text/html")
            if method == "GET" and path == "/api/campaigns":
                query = parse_qs(environ.get("QUERY_STRING", ""))
                campaign_root = self._resolve_campaign_root(
                    query.get("root", [None])[0]
                )
                campaigns = sorted(
                    child.name
                    for child in campaign_root.iterdir()
                    if child.is_dir() and not child.is_symlink()
                )
                return self._json(start_response, HTTPStatus.OK, {"campaigns": campaigns})
            if method == "GET" and path == "/api/config":
                return self._json(
                    start_response,
                    HTTPStatus.OK,
                    {
                        "max_context_bytes": self.max_context_bytes,
                        "campaign_root": str(self.campaign_root),
                    },
                )
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
        if not self.settings.anthropic_api_key:
            raise ValueError(
                "Anthropic authentication is not configured. Add ANTHROPIC_API_KEY "
                "to the Campaign Agent .env file, or set AI_CAMPAIGN_ENV_FILE to "
                "the path of an existing .env file, then restart the server. Do "
                "not enter the key in this chat."
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
        campaign_root = self._resolve_campaign_root(payload.get("campaign_root"))
        campaign_text = (
            self._campaign_text(campaign_name, campaign_root) if campaign_name else ""
        )
        review_document = payload.get("review_document", "")
        starting_document = payload.get("starting_document", "")
        review_pdf = payload.get("review_document_pdf_base64")
        starting_pdf = payload.get("starting_document_pdf_base64")
        if review_pdf is not None:
            if mode != "review":
                raise ValueError("PDF documents can only be supplied in Reviewer Mode.")
            review_document = self._extract_pdf_text(review_pdf)
        if starting_pdf is not None:
            if mode != "create":
                raise ValueError("Starting documents can only be supplied in Creation mode.")
            starting_document = self._extract_pdf_text(starting_pdf)
        session_record = payload.get("session_record", "")
        if not all(
            isinstance(value, str)
            for value in (review_document, starting_document, session_record)
        ):
            raise ValueError("Review documents and session records must be text.")
        supplied_context_bytes = sum(
            len(value.encode("utf-8"))
            for value in (review_document, starting_document, session_record)
        )
        if supplied_context_bytes > self.max_context_bytes:
            limit_kb = self.settings.ai_campaign_max_context_kb
            raise ValueError(
                f"Supplied campaign material exceeds the {limit_kb} KB limit."
            )

        system = build_system_prompt(
            mode=mode,
            campaign_name=campaign_name,
            campaign_text=campaign_text,
            review_document=review_document,
            starting_document=starting_document,
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

        client = make_client(api_key=self.settings.anthropic_api_key)
        response = client.messages.create(**kwargs)
        proposal = None
        tool_use = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use is not None:
            proposal = self._validate_proposal(tool_use.input)
            text = "\n".join(
                block.text for block in response.content if block.type == "text"
            )
            if not text:
                summary = proposal["summary"].strip()
                text = "Proposal prepared for your review."
                if summary:
                    text = f"{text} {summary}"
                text = f"{text} The files have not been written."
        else:
            text = "\n".join(block.text for block in response.content if block.type == "text")

        return {"reply": text, "proposal": proposal}

    def _extract_pdf_text(self, encoded_pdf: Any) -> str:
        if not isinstance(encoded_pdf, str) or not encoded_pdf:
            raise ValueError("The uploaded PDF is empty or invalid.")
        max_encoded_bytes = ((self.max_context_bytes + 2) // 3) * 4
        if len(encoded_pdf) > max_encoded_bytes:
            limit_kb = self.settings.ai_campaign_max_context_kb
            raise ValueError(f"PDF files must be {limit_kb} KB or smaller.")
        try:
            pdf_bytes = base64.b64decode(encoded_pdf, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError("The uploaded PDF data is invalid.") from error
        if len(pdf_bytes) > self.max_context_bytes:
            limit_kb = self.settings.ai_campaign_max_context_kb
            raise ValueError(f"PDF files must be {limit_kb} KB or smaller.")
        if not pdf_bytes.startswith(b"%PDF-"):
            raise ValueError("The uploaded file is not a valid PDF.")

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            if reader.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")
            pages_text = []
            total_bytes = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                total_bytes += len(page_text.encode("utf-8"))
                if total_bytes > self.max_context_bytes:
                    limit_kb = self.settings.ai_campaign_max_context_kb
                    raise ValueError(
                        f"Extracted PDF text exceeds the {limit_kb} KB limit."
                    )
                if page_text.strip():
                    pages_text.append(page_text)
        except ValueError:
            raise
        except Exception as error:
            raise ValueError(
                "Could not read this PDF. Make sure it is valid and not damaged."
            ) from error

        extracted_text = "\n\n".join(pages_text).strip()
        if not extracted_text:
            raise ValueError(
                "No selectable text was found in this PDF. Scanned PDFs need OCR "
                "before they can be reviewed."
            )
        return extracted_text

    def apply_proposal(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("mode") not in {"create", "update"}:
            raise ValueError("Campaign files can only be applied in Creation or Update mode.")
        campaign_name = self._safe_campaign_name(payload.get("campaign", ""))
        files = self._validate_proposal({"files": payload.get("files", []), "summary": ""})[
            "files"
        ]
        campaign_root = self._resolve_campaign_root(payload.get("campaign_root"))
        campaign_dir = self._campaign_path(campaign_name, campaign_root)
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

    def _campaign_text(self, campaign_name: str, campaign_root: Path) -> str:
        safe_name = self._safe_campaign_name(campaign_name)
        campaign_dir = self._campaign_path(safe_name, campaign_root)
        if not campaign_dir.exists():
            return ""
        markdown_files = sorted(campaign_dir.rglob("*.md"))
        parts: list[str] = []
        total = 0
        for path in markdown_files:
            if path.is_symlink():
                continue
            content = path.read_text(encoding="utf-8")
            remaining = self.max_context_bytes - total
            if remaining <= 0:
                break
            content = content[:remaining]
            parts.append(f"\n--- {path.relative_to(campaign_dir)} ---\n{content}")
            total += len(content)
        return "".join(parts)

    def _resolve_campaign_root(self, value: Any = None) -> Path:
        if value is None or value == "":
            return self.campaign_root
        if not isinstance(value, str):
            raise ValueError("Campaign directory must be an absolute path.")
        unresolved_root = Path(value).expanduser()
        if not unresolved_root.is_absolute():
            raise ValueError("Campaign directory must be an absolute path.")
        if unresolved_root.is_symlink():
            raise ValueError("Campaign directory cannot be a symbolic link.")
        campaign_root = unresolved_root.resolve()
        if campaign_root == Path("/"):
            raise ValueError("Campaign directory cannot be the filesystem root.")
        campaign_root.mkdir(parents=True, exist_ok=True)
        if not campaign_root.is_dir():
            raise ValueError("Campaign directory must be a directory.")
        return campaign_root

    def _campaign_path(self, name: str, campaign_root: Path | None = None) -> Path:
        root = campaign_root or self.campaign_root
        unresolved_path = root / name
        if unresolved_path.is_symlink():
            raise ValueError("Campaign folder cannot be a symbolic link.")
        path = unresolved_path.resolve()
        if not path.is_relative_to(root):
            raise ValueError("Campaign folder must be inside the configured campaign root.")
        return path

    @staticmethod
    def _safe_campaign_name(value: Any) -> str:
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", value):
            raise ValueError("Use a campaign folder name with letters, numbers, '-' or '_'.")
        return value

    @staticmethod
    def _validate_proposal(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("The agent returned a proposal that was not an object.")
        if not isinstance(value.get("files"), list):
            raise ValueError("The proposal must include a 'files' array.")
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

    def _read_json(self, environ: dict[str, Any]) -> dict[str, Any]:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError as error:
            raise ValueError("Invalid request size.") from error
        if length < 1 or length > self.max_request_bytes:
            limit_mb = self.max_request_bytes / 1_000_000
            raise ValueError(f"Request must be between 1 byte and {limit_mb:g} MB.")
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
    settings = load_settings()
    app = CampaignApp(settings)
    address = settings.ai_campaign_host
    port = settings.ai_campaign_port
    with make_server(address, port, app) as server:
        print(f"Campaign Agent ready at http://{address}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
