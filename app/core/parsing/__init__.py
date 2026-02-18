"""Parser registry — routes content to the correct platform parser."""

from app.core.parsing.base import BaseParser
from app.core.parsing.camworks import CAMWorksParser
from app.core.parsing.delmia import DELMIAParser
from app.core.parsing.mastercam import MastercamParser

# All registered parsers, in priority order
PARSERS: list[BaseParser] = [
    CAMWorksParser(),
    DELMIAParser(),
    MastercamParser(),
]

PARSER_MAP: dict[str, BaseParser] = {p.platform: p for p in PARSERS}


def get_parser(platform: str) -> BaseParser:
    """Get a parser by explicit platform name."""
    if platform not in PARSER_MAP:
        raise ValueError(f"Unknown platform: {platform}. Available: {list(PARSER_MAP.keys())}")
    return PARSER_MAP[platform]


def detect_parser(content: str) -> BaseParser | None:
    """Auto-detect the correct parser from file content."""
    for parser in PARSERS:
        if parser.detect(content):
            return parser
    return None
