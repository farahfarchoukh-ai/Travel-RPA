import pytest
from decimal import Decimal
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from apps.pricing.engine import PricingEngine


@pytest.fixture
def engine():
    return PricingEngine()


def test_silver_worldwide_7days_single(engine):
    result = engine.calculate_premium(
        scope='WORLDWIDE',
        plan='Silver',
        days=7,
        travellers=[{'age_at_travel': 30}],
        sports_flag=False
    )
    assert result['total'] == Decimal('30.00')
    assert result['group_discount'] == Decimal('0')
    assert result['tax'] == Decimal('0')


def test_senior_age_load(engine):
    result = engine.calculate_premium(
        scope='WORLDWIDE',
        plan='Silver',
        days=7,
        travellers=[{'age_at_travel': 80}],
        sports_flag=False
    )
    assert result['traveller_breakdown'][0]['age_load'] == Decimal('22.50')
    assert result['total'] == Decimal('52.50')


def test_sports_load(engine):
    result = engine.calculate_premium(
        scope='WORLDWIDE',
        plan='Silver',
        days=7,
        travellers=[{'age_at_travel': 30}],
        sports_flag=True
    )
    assert result['traveller_breakdown'][0]['sports_load'] == Decimal('15.00')
    assert result['total'] == Decimal('45.00')


def test_group_discount_11_travellers(engine):
    travellers = [{'age_at_travel': 30} for _ in range(15)]
    result = engine.calculate_premium(
        scope='WORLDWIDE',
        plan='Silver',
        days=7,
        travellers=travellers,
        sports_flag=False
    )
    assert result['subtotal'] == Decimal('450.00')
    assert result['group_discount'] == Decimal('22.50')
    assert result['total'] == Decimal('427.50')


def test_day_band_boundaries(engine):
    r7 = engine.calculate_premium('WORLDWIDE', 'Silver', 7, [{'age_at_travel': 30}])
    r8 = engine.calculate_premium('WORLDWIDE', 'Silver', 8, [{'age_at_travel': 30}])
    assert r7['base_per_traveller'] != r8['base_per_traveller']


def test_ww_excl_us_ca_scope(engine):
    result = engine.calculate_premium(
        scope='WW_EXCL_US_CA',
        plan='Silver',
        days=7,
        travellers=[{'age_at_travel': 30}],
        sports_flag=False
    )
    assert result['total'] == Decimal('25.00')
    assert result['currency'] == 'USD'
