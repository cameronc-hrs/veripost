"""Base parser interface for post processor files."""

from abc import ABC, abstractmethod

from app.core.models.post_processor import ParsedPost


class BaseParser(ABC):
    """Abstract base class for all platform-specific parsers."""

    platform: str = "unknown"

    @abstractmethod
    async def parse(self, content: str, post_id: str) -> ParsedPost:
        """Parse raw post processor content into a structured representation."""
        ...

    @abstractmethod
    def detect(self, content: str) -> bool:
        """Return True if this parser can handle the given content."""
        ...
