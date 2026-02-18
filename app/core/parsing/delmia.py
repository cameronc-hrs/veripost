"""Parser for DELMIA post processor format.

TODO: Implement once DELMIA corpus is available (Phase 2 — multi-platform expansion).
"""

from app.core.models.post_processor import ParsedPost
from app.core.parsing.base import BaseParser


class DELMIAParser(BaseParser):
    """Placeholder parser for DELMIA post processors."""

    platform = "delmia"

    def detect(self, content: str) -> bool:
        indicators = ["DELMIA", "3DEXPERIENCE"]
        return any(marker in content for marker in indicators)

    async def parse(self, content: str, post_id: str) -> ParsedPost:
        return ParsedPost(
            post_id=post_id,
            raw_content=content,
            summary="DELMIA post processor (parsing not yet implemented)",
            errors=["DELMIA parser is a placeholder — not yet implemented"],
        )
