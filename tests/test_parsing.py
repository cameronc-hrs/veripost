"""Parser unit tests."""

import pytest
from app.core.parsing.camworks import CAMWorksParser
from app.core.parsing import detect_parser


@pytest.fixture
def camworks_parser():
    return CAMWorksParser()


SAMPLE_UPG = """\
; Universal Post Generator
; CAMWorks Post Processor

[GENERAL]
Machine = VMC-3axis
Controller = Fanuc 0i

[FORMAT]
Precision = 4
Units = Metric
"""


def test_camworks_detect(camworks_parser):
    assert camworks_parser.detect(SAMPLE_UPG) is True
    assert camworks_parser.detect("random text content") is False


@pytest.mark.asyncio
async def test_camworks_parse(camworks_parser):
    result = await camworks_parser.parse(SAMPLE_UPG, post_id="test-001")
    assert result.post_id == "test-001"
    assert "GENERAL" in result.section_names
    assert "FORMAT" in result.section_names
    assert result.variables.get("Machine") == "VMC-3axis"
    assert result.variables.get("Controller") == "Fanuc 0i"


def test_auto_detect():
    parser = detect_parser(SAMPLE_UPG)
    assert parser is not None
    assert parser.platform == "camworks"


def test_auto_detect_unknown():
    parser = detect_parser("nothing recognizable here")
    assert parser is None
