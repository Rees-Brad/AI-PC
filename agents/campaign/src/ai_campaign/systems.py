"""The game systems the Campaign Agent supports, recognized from a campaign's rules text.

The license text here was written from the published documents' usual wording;
verify it against the System Reference Documents before publishing a campaign.
"""

from __future__ import annotations

import re

DND_5E_2024 = "D&D 5e (2024)"
DND_5E_2014 = "D&D 5e (2014)"
DND_3_5 = "D&D 3.5"

SRD_5_2_ATTRIBUTION = (
    "This work includes material from the System Reference Document 5.2 (\"SRD 5.2\") by "
    "Wizards of the Coast LLC, available at https://www.dndbeyond.com/srd. The SRD 5.2 is "
    "licensed under the Creative Commons Attribution 4.0 International License, available "
    "at https://creativecommons.org/licenses/by/4.0/legalcode."
)
SRD_5_1_ATTRIBUTION = (
    "This work includes material taken from the System Reference Document 5.1 (\"SRD 5.1\") "
    "by Wizards of the Coast LLC and available at "
    "https://dnd.wizards.com/resources/systems-reference-document. The SRD 5.1 is licensed "
    "under the Creative Commons Attribution 4.0 International License available at "
    "https://creativecommons.org/licenses/by/4.0/legalcode."
)
# The OGL needs more than a line of attribution: a published work must include the
# full license text, this Section 15 notice, and say what is Open Game Content.
SRD_3_5_SECTION_15 = (
    "System Reference Document Copyright 2000-2003, Wizards of the Coast, Inc.; Authors "
    "Jonathan Tweet, Monte Cook, Skip Williams, Rich Baker, Andy Collins, David Noonan, "
    "Rich Redman, Bruce R. Cordell, John D. Rateliff, Thomas Reid, James Wyatt, based on "
    "original material by E. Gary Gygax and Dave Arneson."
)
SRD_3_5_ATTRIBUTION = (
    "This work uses Open Game Content from the System Reference Document 3.5 (\"SRD 3.5\") "
    "under the Open Game License version 1.0a. A published copy must include the full text "
    "of the Open Game License 1.0a, identify which material is Open Game Content, and give "
    f"this Section 15 notice: {SRD_3_5_SECTION_15}"
)

_3_5 = re.compile(r"(?<![\d.])3\.5(?![\d])|\bv3\.5")


def rules_family(rules: str | None) -> str | None:
    """Which supported system a campaign's rules text names, or None for any other."""
    lowered = (rules or "").lower()
    if _3_5.search(lowered):
        return DND_3_5
    if "2024" in lowered or "5.2" in lowered:
        return DND_5E_2024
    if "2014" in lowered or "5.1" in lowered:
        return DND_5E_2014
    return None


def srd_attribution(rules: str) -> str | None:
    """The attribution statement for the open-licensed SRD that matches a rules edition."""
    return {
        DND_5E_2024: SRD_5_2_ATTRIBUTION,
        DND_5E_2014: SRD_5_1_ATTRIBUTION,
        DND_3_5: SRD_3_5_ATTRIBUTION,
    }.get(rules_family(rules) or "")
