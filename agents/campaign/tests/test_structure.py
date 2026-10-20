from __future__ import annotations

from pathlib import Path

from ai_campaign.structure import campaign_summary, check_campaign, extract_links


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def messages(root: Path) -> list[tuple[str, str, str]]:
    return [(i.severity, i.file, i.message) for i in check_campaign(root)]


def test_valid_campaign_has_no_issues(campaign: Path) -> None:
    assert messages(campaign) == []


def test_broken_link_is_an_error_with_line(campaign: Path) -> None:
    path = campaign / "chapters/01-the-drowned-coast/chapter.md"
    path.write_text(path.read_text() + "- [Lost](adventures/02-lost.md)\n")
    issues = check_campaign(campaign)
    assert issues[0].severity == "error"
    assert issues[0].file == "chapters/01-the-drowned-coast/chapter.md"
    assert issues[0].line == 5
    assert "adventures/02-lost.md" in issues[0].message


def test_links_in_code_and_comments_and_external_links_are_ignored(tmp_path: Path) -> None:
    path = write(
        tmp_path / "a.md",
        "<!-- [x](missing.md) -->\n```\n[y](missing.md)\n```\n`[z](missing.md)`\n"
        "[web](https://example.com) [mail](mailto:a@b.c) [top](#goal) [real](b.md#part)\n",
    )
    assert [link.target for link in extract_links(path)] == ["#goal", "b.md#part"]
    assert extract_links(path)[1].resolved == tmp_path / "b.md"


def test_unlinked_and_unsupported_maps_are_reported(campaign: Path) -> None:
    (campaign / "maps/region.tiff").write_bytes(b"x")
    found = messages(campaign)
    assert ("warning", "maps/region.tiff", "Map is not linked from any section.") in found
    assert any("Unsupported map format" in m for _, f, m in found if f == "maps/region.tiff")


def test_sections_missing_from_outlines_are_reported(campaign: Path) -> None:
    write(campaign / "chapters/01-the-drowned-coast/encounters/02-ambush.md", "# Ambush\n")
    write(campaign / "chapters/02-the-deep/chapter.md", "# The Deep\n")
    found = messages(campaign)
    assert (
        "warning",
        "chapters/01-the-drowned-coast/encounters/02-ambush.md",
        "Not linked from its chapter.md.",
    ) in found
    assert (
        "warning",
        "chapters/02-the-deep/chapter.md",
        "Chapter is not linked from campaign.md.",
    ) in found


def test_numbering_problems_are_reported(campaign: Path) -> None:
    folder = campaign / "chapters/01-the-drowned-coast/adventures"
    write(folder / "01-duplicate.md", "# Dup\n")
    write(folder / "unnumbered.md", "# U\n")
    (campaign / "chapters/missing-outline").mkdir()
    found = messages(campaign)
    assert any("Shares number 01" in m for _, f, m in found if f.endswith("01-smugglers-cove.md")
               or f.endswith("01-duplicate.md"))
    assert any("no number prefix" in m for _, f, m in found if f.endswith("unnumbered.md"))
    assert ("error", "chapters/missing-outline/chapter.md",
            "The chapter outline file is missing.") in found


def test_index_entry_without_section_link_is_reported(campaign: Path) -> None:
    path = campaign / "items.md"
    path.write_text(path.read_text() + "\n## Tide Pearl\n- See [the map](maps/cove.png)\n"
                    "\n## [Crown](chapters/01-the-drowned-coast/chapter.md)\n")
    found = messages(campaign)
    assert (
        "warning",
        "items.md",
        "Index entry 'Tide Pearl' does not link to any campaign section.",
    ) in found
    assert not any("'[Crown]" in m for _, _, m in found)


def test_new_campaign_reports_missing_goal_and_adventure(tmp_path: Path) -> None:
    from ai_campaign.lifecycle import create_campaign

    create_campaign(tmp_path / "new", "New")
    found = messages(tmp_path / "new")
    assert ("warning", "campaign.md", "The campaign has no goal yet.") in found
    assert any("at least one adventure" in m for _, _, m in found)
    assert not any(severity == "error" for severity, _, _ in found)


def test_folder_without_marker_is_flagged(tmp_path: Path) -> None:
    write(tmp_path / "campaign.md", "# X\n")
    found = messages(tmp_path)
    assert any("No campaign marker" in m for _, _, m in found)


def test_session_summaries_are_not_link_checked(campaign: Path) -> None:
    write(campaign / "sessions/2026-10-20.md", "[gone](nowhere.md)\n")
    assert messages(campaign) == []
    assert campaign_summary(campaign)["sessions"] == ["2026-10-20.md"]


def test_summary_describes_structure(campaign: Path) -> None:
    summary = campaign_summary(campaign)
    assert summary["is_campaign"] is True
    assert summary["marker"]["role"] == "master"
    assert summary["chapters"] == [
        {
            "folder": "chapters/01-the-drowned-coast",
            "has_outline": True,
            "adventures": ["chapters/01-the-drowned-coast/adventures/01-smugglers-cove.md"],
            "encounters": ["chapters/01-the-drowned-coast/encounters/01-harbor-brawl.md"],
        }
    ]
    assert summary["maps"] == ["maps/cove.png", "maps/world.png"]
    assert summary["indexes"] == {"npcs.md": 1, "items.md": 0, "locations.md": 0}
    assert summary["open_items"] == {"open": 3, "done": 0}
    assert summary["missing_agent_files"] == []


def test_open_items_are_counted_and_their_links_checked(campaign: Path) -> None:
    path = campaign / "OPEN_ITEMS.md"
    path.write_text("# Open items\n\n- [x] Goal (done 2026-10-20)\n- [ ] Map\n"
                    "* [X] Done too\n- [ ] See [gone](chapters/gone.md)\n")
    assert campaign_summary(campaign)["open_items"] == {"open": 2, "done": 2}
    assert ("error", "OPEN_ITEMS.md", "Broken link to 'chapters/gone.md'.") in messages(campaign)


def test_guide_and_worklog_links_are_not_checked(campaign: Path) -> None:
    (campaign / "WORKLOG.md").write_text("Moved [old](chapters/old.md).\n")
    (campaign / "GETTING_STARTED.md").write_text("[x](nowhere.md)\n")
    assert messages(campaign) == []


def test_missing_rules_edition_is_reported(campaign: Path) -> None:
    path = campaign / "campaign.md"
    path.write_text(path.read_text().replace("## Rules\n\nD&D 5e (2024).\n\n", ""))
    assert any("rules edition is not recorded" in m for _, _, m in messages(campaign))
