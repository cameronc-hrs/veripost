"""Parser for Mastercam post processor format.

TODO: Implement once Mastercam corpus is available (Phase 2 — multi-platform expansion).
"""

from app.core.models.post_processor import ParsedPost
from app.core.parsing.base import BaseParser


class MastercamParser(BaseParser):
    """Placeholder parser for Mastercam post processors."""

    platform = "mastercam"

    def detect(self, content: str) -> bool:
        indicators = ["Mastercam", ".mcpost", ".pst"]
        return any(marker in content for marker in indicators)

    async def parse(self, content: str, post_id: str) -> ParsedPost:
        return ParsedPost(
            post_id=post_id,
            raw_content=content,
            summary="Mastercam post processor (parsing not yet implemented)",
            errors=["Mastercam parser is a placeholder — not yet implemented"],
        )
