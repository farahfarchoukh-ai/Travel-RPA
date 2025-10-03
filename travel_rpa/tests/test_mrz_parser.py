import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.extraction.mrz_parser import MRZParser


@pytest.fixture
def parser():
    return MRZParser()


def test_parse_valid_passport(parser):
    ocr_text = """
P<LBNALHAJ<<ALI<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
AB1234567<LBN9001015M2501011<<<<<<<<<<<<<<06
"""
    result = parser.parse_passport(ocr_text)
    
    assert result is not None
    assert result['passport_number'] == 'AB1234567'
    assert result['full_name'] == 'ALI ALHAJ'
    assert result['first_name'] == 'ALI'
    assert result['last_name'] == 'ALHAJ'
    assert result['nationality'] == 'LBN'
    assert result['sex'] == 'M'
    assert result['date_of_birth'] == '1990-01-01'


def test_parse_invalid_mrz(parser):
    ocr_text = "Some random text without MRZ"
    result = parser.parse_passport(ocr_text)
    assert result is None


def test_parse_mrz_date(parser):
    assert parser._parse_mrz_date('900101') == '1990-01-01'
    assert parser._parse_mrz_date('250101') == '2025-01-01'
    assert parser._parse_mrz_date('600101') == '1960-01-01'
    assert parser._parse_mrz_date('invalid') is None
