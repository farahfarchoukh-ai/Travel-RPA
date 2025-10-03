from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Case, Traveller
from apps.extraction.mrz_parser import MRZParser
from apps.pricing.engine import PricingEngine
from apps.issuance.simulator import PlaywrightSimulator
import hashlib
from datetime import datetime, date
import pytz
import re


def verify_webhook_secret(request):
    secret = request.headers.get('X-Webhook-Secret')
    if secret != settings.N8N_WEBHOOK_SECRET:
        return False
    return True


@api_view(['POST'])
def ingest_email(request):
    if not verify_webhook_secret(request):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
    
    data = request.data
    
    idem_string = f"{data['message_id']}|{data.get('body', '')}"
    idempotency_key = hashlib.sha256(idem_string.encode()).hexdigest()
    
    if Case.objects.filter(idempotency_key=idempotency_key).exists():
        existing_case = Case.objects.get(idempotency_key=idempotency_key)
        return Response({
            'status': 'duplicate',
            'case_id': str(existing_case.case_id),
            'idempotency_key': idempotency_key
        })
    
    extracted = extract_policy_data(data.get('body', ''), data.get('subject', ''))
    
    if not extracted['intent_ok']:
        return Response({
            'route': 'ignore',
            'intent_ok': False
        })
    
    case = Case.objects.create(
        message_id=data['message_id'],
        thread_id=data.get('thread_id', data['message_id']),
        idempotency_key=idempotency_key,
        from_email=data.get('from', ''),
        subject=data.get('subject', ''),
        body=data.get('body', ''),
        received_at=data.get('received_at', datetime.now(pytz.UTC)),
        direction=extracted.get('direction'),
        scope=extracted.get('scope'),
        plan=extracted.get('plan'),
        coverage_limit=extracted.get('coverage_limit'),
        start_date=extracted.get('start_date'),
        end_date=extracted.get('end_date'),
        days=extracted.get('days'),
        sports_coverage=extracted.get('sports_coverage', False),
        intent_ok=True
    )
    
    ocr_results = data.get('ocr_results', [])
    mrz_parser = MRZParser()
    for ocr_text in ocr_results:
        parsed = mrz_parser.parse_passport(ocr_text)
        if parsed:
            Traveller.objects.create(
                case=case,
                full_name=parsed['full_name'],
                passport_number=parsed['passport_number'],
                date_of_birth=parsed['date_of_birth'],
                mrz_data=parsed
            )
    
    if extracted.get('direction') == 'INBOUND':
        required = ['direction', 'plan', 'days', 'start_date']
    else:
        required = ['direction', 'scope', 'plan', 'days', 'start_date']
    
    missing = []
    for field in required:
        val = extracted.get(field)
        if val is None:
            missing.append(field)
    
    if case.travellers.count() == 0:
        missing.extend(['passport_numbers', 'traveller_names'])
    
    case.missing_fields = missing
    
    if missing:
        case.route = 'missing'
        case.save()
        return Response({
            'route': 'missing',
            'case_id': str(case.case_id),
            'to': data.get('from', ''),
            'missing': missing,
            'original_subject': data.get('subject', ''),
            'thread_id': data.get('thread_id', '')
        })
    
    for traveller in case.travellers.all():
        if traveller.date_of_birth and case.start_date:
            if isinstance(case.start_date, str):
                start_date = datetime.strptime(case.start_date, '%Y-%m-%d').date()
            else:
                start_date = case.start_date
            
            if isinstance(traveller.date_of_birth, str):
                dob = datetime.strptime(traveller.date_of_birth, '%Y-%m-%d').date()
            else:
                dob = traveller.date_of_birth
            
            age = (start_date - dob).days // 365
            traveller.age_at_travel = age
            traveller.is_senior = 76 <= age <= 86
            traveller.save()
    
    engine = PricingEngine()
    travellers_data = [
        {'age_at_travel': t.age_at_travel} 
        for t in case.travellers.all()
    ]
    
    try:
        pricing = engine.calculate_premium(
            scope=case.scope,
            plan=case.plan,
            days=case.days,
            travellers=travellers_data,
            sports_flag=case.sports_coverage
        )
        
        case.premium_base = pricing['base_per_traveller']
        case.premium_subtotal = pricing['subtotal']
        case.premium_group_discount = pricing['group_discount']
        case.premium_net = pricing['net']
        case.premium_tax = pricing['tax']
        case.premium_fees = pricing['fees']
        case.premium_total = pricing['total']
        case.currency = pricing['currency']
        case.route = 'success'
        case.save()
        
        return Response({
            'route': 'success',
            'case_id': str(case.case_id),
            'extracted': extracted,
            'pricing': {
                'base_per_traveller': f"{pricing['base_per_traveller']:.2f}",
                'subtotal': f"{pricing['subtotal']:.2f}",
                'group_discount': f"{pricing['group_discount']:.2f}",
                'net': f"{pricing['net']:.2f}",
                'tax': f"{pricing['tax']:.2f}",
                'fees': f"{pricing['fees']:.2f}",
                'total': f"{pricing['total']:.2f}",
                'currency': pricing['currency']
            },
            'travellers': [
                {
                    'name': t.full_name,
                    'passport': t.passport_number,
                    'age': t.age_at_travel,
                    'is_senior': t.is_senior
                }
                for t in case.travellers.all()
            ]
        })
    except Exception as e:
        case.route = 'missing'
        case.missing_fields = ['pricing_error']
        case.save()
        return Response({
            'route': 'missing',
            'case_id': str(case.case_id),
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def simulate_issuance(request):
    if not verify_webhook_secret(request):
        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
    
    case_id = request.data.get('case_id')
    case = Case.objects.get(case_id=case_id)
    
    simulator = PlaywrightSimulator()
    result = simulator.simulate_issuance({
        'case_id': str(case.case_id),
        'plan': case.plan,
        'scope': case.scope,
        'days': case.days
    })
    
    return Response({
        'screenshot_url': result['screenshot_path'],
        'policy_number': result['simulated_policy_number'],
        'simulation_timestamp': result['timestamp']
    })


def extract_policy_data(body: str, subject: str) -> dict:
    intent_patterns = [
        r'travel\s+insurance',
        r'\binsurance\b',
        r'\bpolic(y|ies)\b',
        r'\bcover(age)?\b',
        r'\bissue',
        r'\barrange',
        r'\bprovide',
        r'\binsure',
        r'\bquote'
    ]
    intent_ok = any(re.search(pattern, body.lower()) for pattern in intent_patterns)
    
    direction = None
    scope = None
    if re.search(r'\binbound\b', body.lower()):
        direction = 'INBOUND'
        scope = 'INBOUND'
    elif re.search(r'\boutbound\b', body.lower()):
        direction = 'OUTBOUND'
    
    if scope != 'INBOUND':
        if re.search(r'(worldwide\s+excluding|world\s+except|excl\.?\s*(us|usa|canada)|excluding\s*(us|usa|canada)|excluding\s+country\s+of\s+residence)', body.lower()):
            scope = 'WW_EXCL_US_CA'
        elif re.search(r'worldwide', body.lower()):
            scope = 'WORLDWIDE'
    
    if scope is None and re.search(r'(europe|greece)', body.lower()):
        scope = 'WW_EXCL_US_CA'
    
    plan = None
    if re.search(r'\bplatinum\b', body.lower()):
        plan = 'Platinum'
    elif re.search(r'gold\s+plus', body.lower()):
        plan = 'Gold Plus'
    elif re.search(r'\bgold\b', body.lower()):
        plan = 'Gold'
    elif re.search(r'\bsilver\b', body.lower()):
        plan = 'Silver'
    
    coverage_match = re.search(r'\$?\s?(\d+),?(\d{3})', body)
    if coverage_match and not plan:
        coverage_str = coverage_match.group(1) + coverage_match.group(2)
        coverage = int(coverage_str)
        if coverage == 50000 or coverage == 50:
            plan = 'Silver'
        elif coverage == 100000 or coverage == 100:
            plan = 'Gold'
        elif coverage == 300000 or coverage == 300:
            plan = 'Gold Plus'
        elif coverage == 500000 or coverage == 500:
            plan = 'Platinum'
    
    days = None
    days_match = re.search(r'(\d+)\s+days?', body.lower())
    if days_match:
        days = int(days_match.group(1))
    
    if not days:
        duration_patterns = [
            (r'(\d+)\s+weeks?', 7),
            (r'(\d+)\s+months?', 30),
        ]
        for pattern, multiplier in duration_patterns:
            match = re.search(pattern, body.lower())
            if match:
                days = int(match.group(1)) * multiplier
                break
    
    start_date = None
    end_date = None
    date_matches = re.findall(r'(\d{4})-(\d{2})-(\d{2})', body)
    if len(date_matches) >= 2:
        start_date = f"{date_matches[0][0]}-{date_matches[0][1]}-{date_matches[0][2]}"
        end_date = f"{date_matches[1][0]}-{date_matches[1][1]}-{date_matches[1][2]}"
    
    if not start_date:
        date_patterns = [
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'dmy'),
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'ymd'),
        ]
        for pattern, format_type in date_patterns:
            matches = re.findall(pattern, body)
            if len(matches) >= 2:
                try:
                    if format_type == 'dmy':
                        start_date = f"{matches[0][2]}-{matches[0][1].zfill(2)}-{matches[0][0].zfill(2)}"
                        end_date = f"{matches[1][2]}-{matches[1][1].zfill(2)}-{matches[1][0].zfill(2)}"
                    elif format_type == 'ymd':
                        start_date = f"{matches[0][0]}-{matches[0][1].zfill(2)}-{matches[0][2].zfill(2)}"
                        end_date = f"{matches[1][0]}-{matches[1][1].zfill(2)}-{matches[1][2].zfill(2)}"
                    break
                except (IndexError, ValueError):
                    continue
    
    sports_coverage = bool(re.search(r'(sports?\s+coverage|sports?\s+activit|motorcycle)', body.lower()))
    
    return {
        'intent_ok': intent_ok,
        'direction': direction,
        'scope': scope,
        'plan': plan,
        'coverage_limit': None,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'sports_coverage': sports_coverage
    }
