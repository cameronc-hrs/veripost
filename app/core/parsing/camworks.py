"""Parser for CAMWorks Universal Post Generator (UPG) format.

The UPG format is CAMWorks' proprietary post processor definition format.
This parser extracts sections, variables, and structure from .ctl / .post files.

TODO: Expand with real UPG format knowledge once corpus is collected (Week 1-2).
"""

import re

from app.core.models.post_processor import ParsedPost
from app.core.parsing.base import BaseParser


class CAMWorksParser(BaseParser):
    """Parser for CAMWorks UPG post processor files."""

    platform = "camworks"

    # Common UPG section markers (preliminary — refine with real corpus data)
    SECTION_PATTERN = re.compile(r"^\s*\[(\w+)\]", re.MULTILINE)
    VARIABLE_PATTERN = re.compile(r"^\s*(\w+)\s*=\s*(.+)$", re.MULTILINE)

    def detect(self, content: str) -> bool:
        """Detect if content looks like a CAMWorks UPG file."""
        indicators = [
            "Universal Post Generator",
            "CAMWorks",
            ".ctl",
            "[GENERAL]",
            "[FORMAT]",
        ]
        return any(marker in content for marker in indicators)

    async def parse(self, content: str, post_id: str) -> ParsedPost:
        """Parse a CAMWorks UPG post processor file."""
        sections = self.SECTION_PATTERN.findall(content)
        variables = dict(self.VARIABLE_PATTERN.findall(content))

        summary_parts = []
        if "GENERAL" in sections:
            summary_parts.append("Contains general configuration")
        if variables.get("Machine"):
            summary_parts.append(f"Machine: {variables['Machine']}")
        if variables.get("Controller"):
            summary_parts.append(f"Controller: {variables['Controller']}")

        summary = "; ".join(summary_parts) if summary_parts else "CAMWorks post processor file"

        return ParsedPost(
            post_id=post_id,
            raw_content=content,
            summary=summary,
            section_names=sections,
            variables=variables,
        )
