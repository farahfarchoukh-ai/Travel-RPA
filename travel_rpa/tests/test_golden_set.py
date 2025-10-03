import pytest
import json
from pathlib import Path
from django.test import Client
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

GOLDEN_DIR = Path(__file__).parent / 'golden'


def get_golden_cases():
    """Get all golden test case directories"""
    if not GOLDEN_DIR.exists():
        return []
    return sorted([d for d in GOLDEN_DIR.iterdir() if d.is_dir() and (d / 'email.json').exists()])


@pytest.mark.django_db
@pytest.mark.parametrize('case_dir', get_golden_cases(), ids=lambda d: d.name)
def test_golden_case(case_dir):
    """Test each golden case end-to-end"""
    with open(case_dir / 'email.json') as f:
        email = json.load(f)
    
    with open(case_dir / 'expected.json') as f:
        expected = json.load(f)
    
    client = Client()
    response = client.post(
        '/api/v1/ingest',
        data=json.dumps(email),
        content_type='application/json',
        HTTP_X_WEBHOOK_SECRET='test-secret'
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    
    assert data['route'] == expected['route'], f"Route mismatch: {data['route']} != {expected['route']}"
    
    if data['route'] == 'success':
        extracted = data['extracted']
        assert extracted['direction'] == expected['extracted']['direction']
        assert extracted['scope'] == expected['extracted']['scope']
        assert extracted['plan'] == expected['extracted']['plan']
        assert extracted['days'] == expected['extracted']['days']
        
        pricing = data['pricing']
        assert str(pricing['total']) == expected['pricing']['total'], \
            f"Total mismatch: {pricing['total']} != {expected['pricing']['total']}"
        assert str(pricing['subtotal']) == expected['pricing']['subtotal'], \
            f"Subtotal mismatch: {pricing['subtotal']} != {expected['pricing']['subtotal']}"
        assert str(pricing['group_discount']) == expected['pricing']['group_discount'], \
            f"Group discount mismatch: {pricing['group_discount']} != {expected['pricing']['group_discount']}"
        
        assert len(data['travellers']) == len(expected['travellers']), \
            f"Traveller count mismatch: {len(data['travellers'])} != {len(expected['travellers'])}"
    
    elif data['route'] == 'missing':
        assert 'missing' in data or 'missing_fields' in data, "Missing fields not returned for 'missing' route"


def test_golden_cases_exist():
    """Verify that golden test cases exist"""
    cases = get_golden_cases()
    assert len(cases) >= 2, f"Expected at least 2 golden test cases, found {len(cases)}"
    print(f"\nFound {len(cases)} golden test cases:")
    for case in cases:
        print(f"  - {case.name}")
