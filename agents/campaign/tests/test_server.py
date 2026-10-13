from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_campaign.prompts import build_system_prompt
from ai_campaign.config import load_settings
from ai_campaign.server import CampaignApp


@pytest.fixture
def app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CampaignApp:
    monkeypatch.setenv("AI_CAMPAIGN_ROOT", str(tmp_path / "campaigns"))
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("AI_CAMPAIGN_MAX_CONTEXT_KB", "500")
    return CampaignApp()


def test_context_limit_uses_configured_kilobytes(app: CampaignApp) -> None:
    assert app.max_context_bytes == 500 * 1024


def test_reviewer_prompt_is_read_only() -> None:
    prompt = build_system_prompt(mode="review")

    assert "Do not create" in prompt
    assert "reference data" in prompt


def test_chat_explains_missing_anthropic_credentials(
    app: CampaignApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app.settings.anthropic_api_key = ""

    with pytest.raises(
        ValueError, match="Add ANTHROPIC_API_KEY.*restart the server"
    ):
        app.chat(
            {
                "mode": "review",
                "messages": [{"role": "user", "content": "Review this."}],
            }
        )


def test_loads_credentials_from_configured_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / "campaign.env"
    env_file.write_text("ANTHROPIC_API_KEY=loaded-from-file\n", encoding="utf-8")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AI_CAMPAIGN_ENV_FILE", str(env_file))

    settings = load_settings()

    assert settings.anthropic_api_key == "loaded-from-file"


def test_defaults_to_campaign_instance_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    campaign_dir = tmp_path / "ai-pc-campaigns"
    campaign_dir.mkdir()
    (campaign_dir / ".env").write_text(
        "ANTHROPIC_API_KEY=campaign-instance-key\n", encoding="utf-8"
    )
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("AI_CAMPAIGN_ENV_FILE", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    settings = load_settings()

    assert settings.anthropic_api_key == "campaign-instance-key"
    assert settings.ai_campaign_root == Path("~/ai-pc-campaigns")


def test_update_prompt_does_not_claim_scribe_connection() -> None:
    prompt = build_system_prompt(mode="update", session_record="The party met Ilyra.")

    assert "no direct Scribe connection is configured" in prompt
    assert "The party met Ilyra." in prompt


def test_reviewer_chat_does_not_offer_file_tool(
    app: CampaignApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    calls: list[dict] = []

    class FakeMessages:
        def create(self, **kwargs: dict) -> SimpleNamespace:
            calls.append(kwargs)
            return SimpleNamespace(content=[SimpleNamespace(type="text", text="Review")])

    monkeypatch.setattr(
        "ai_campaign.server.make_client",
        lambda **kwargs: SimpleNamespace(messages=FakeMessages()),
    )

    result = app.chat(
        {
            "mode": "review",
            "messages": [{"role": "user", "content": "Review this."}],
            "review_document": "Campaign notes",
        }
    )

    assert result == {"reply": "Review", "proposal": None}
    assert "tools" not in calls[0]
    assert "Campaign notes" in calls[0]["system"]


def test_campaign_chat_returns_proposal_without_writing_files(
    app: CampaignApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeMessages:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **kwargs: dict) -> SimpleNamespace:
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(
                    content=[
                        SimpleNamespace(
                            type="tool_use",
                            id="proposal-1",
                            input={
                                "summary": "Start the campaign outline.",
                                "files": [
                                    {"path": "campaign.md", "content": "# New Campaign\n"}
                                ],
                            },
                        )
                    ]
                )
            return SimpleNamespace(
                content=[SimpleNamespace(type="text", text="Review the proposed file.")]
            )

    fake_messages = FakeMessages()
    monkeypatch.setattr(
        "ai_campaign.server.make_client",
        lambda **kwargs: SimpleNamespace(messages=fake_messages),
    )

    result = app.chat(
        {
            "mode": "create",
            "campaign": "new-campaign",
            "messages": [{"role": "user", "content": "Make a campaign outline."}],
        }
    )

    assert result["reply"] == "Review the proposed file."
    assert result["proposal"]["files"] == [
        {"path": "campaign.md", "content": "# New Campaign\n"}
    ]
    assert not (app.campaign_root / "new-campaign" / "campaign.md").exists()


def test_applies_approved_markdown_proposal(app: CampaignApp) -> None:
    result = app.apply_proposal(
        {
            "mode": "create",
            "campaign": "green-hollow",
            "files": [{"path": "campaign.md", "content": "# Green Hollow\n"}],
        }
    )

    assert result == {"written": ["campaign.md"]}
    assert (app.campaign_root / "green-hollow" / "campaign.md").read_text() == (
        "# Green Hollow\n"
    )


@pytest.mark.parametrize(
    "campaign, file_path",
    [
        ("../outside", "campaign.md"),
        ("green-hollow", "../../outside.md"),
        ("green-hollow", "notes.txt"),
    ],
)
def test_rejects_unsafe_proposal_paths(
    app: CampaignApp, campaign: str, file_path: str
) -> None:
    with pytest.raises(ValueError):
        app.apply_proposal(
            {
                "mode": "update",
                "campaign": campaign,
                "files": [{"path": file_path, "content": "not safe"}],
            }
        )


def test_rejects_reviewer_file_writes(app: CampaignApp) -> None:
    with pytest.raises(ValueError, match="only be applied"):
        app.apply_proposal(
            {
                "mode": "review",
                "campaign": "green-hollow",
                "files": [{"path": "campaign.md", "content": "# Not allowed"}],
            }
        )