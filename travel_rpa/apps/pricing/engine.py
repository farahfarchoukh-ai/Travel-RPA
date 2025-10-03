import csv
import yaml
from decimal import Decimal
from pathlib import Path
from typing import List, Dict, Any


class PricingEngine:
    def __init__(self):
        self.tariffs = self._load_tariffs()
        self.rules = self._load_rules()
    
    def _load_tariffs(self) -> Dict:
        tariffs = {}
        data_dir = Path(__file__).parent.parent.parent / 'data'
        with open(data_dir / 'tariffs.csv') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (
                    row['scope'],
                    row['plan'],
                    int(row['band_min']),
                    int(row['band_max'])
                )
                tariffs[key] = {
                    'premium': Decimal(row['premium_usd']),
                    'currency': row['currency'],
                    'coverage_limit': int(row['coverage_limit'])
                }
        return tariffs
    
    def _load_rules(self) -> Dict:
        data_dir = Path(__file__).parent.parent.parent / 'data'
        with open(data_dir / 'rules.yml') as f:
            return yaml.safe_load(f)
    
    def calculate_premium(
        self,
        scope: str,
        plan: str,
        days: int,
        travellers: List[Dict[str, Any]],
        sports_flag: bool = False
    ) -> Dict[str, Any]:
        
        band = self._get_day_band(days)
        if not band:
            raise ValueError(f"Invalid days: {days}. Must be 1-92.")
        
        key = (scope, plan, band['min'], band['max'])
        tariff = self.tariffs.get(key)
        if not tariff:
            raise ValueError(f"No tariff found for {scope}, {plan}, {days} days")
        
        base_premium = tariff['premium']
        
        traveller_premiums = []
        for traveller in travellers:
            base_i = base_premium
            
            age = traveller.get('age_at_travel', 0)
            is_senior = (
                self.rules['age_load']['senior_age_min'] <= age <= 
                self.rules['age_load']['senior_age_max']
            )
            age_load_i = (
                base_i * Decimal(str(self.rules['age_load']['senior_multiplier']))
                if is_senior else Decimal('0')
            )
            
            sports_load_i = (
                (base_i + age_load_i) * Decimal(str(self.rules['sports_load']['multiplier']))
                if sports_flag else Decimal('0')
            )
            
            traveller_total = base_i + age_load_i + sports_load_i
            traveller_premiums.append({
                'base': base_i,
                'age_load': age_load_i,
                'sports_load': sports_load_i,
                'total': traveller_total
            })
        
        subtotal = sum(t['total'] for t in traveller_premiums)
        
        num_travellers = len(travellers)
        group_discount_rate = self._get_group_discount_rate(num_travellers)
        group_discount = subtotal * Decimal(str(group_discount_rate))
        net = subtotal - group_discount
        
        tax_rate = Decimal(str(self.rules.get('default_tax_rate', 0)))
        tax_amount = net * tax_rate
        
        fees = (
            Decimal(str(self.rules['fees'].get('issue_fee_usd', 0))) +
            Decimal(str(self.rules['fees'].get('payment_fee_usd', 0)))
        )
        
        gross = net + tax_amount + fees
        
        rounding_rule = self.rules.get('rounding_rule', 2)
        final = round(gross, rounding_rule)
        
        return {
            'base_per_traveller': base_premium,
            'traveller_breakdown': traveller_premiums,
            'subtotal': subtotal,
            'group_discount': group_discount,
            'group_discount_rate': group_discount_rate,
            'net': net,
            'tax': tax_amount,
            'tax_rate': tax_rate,
            'fees': fees,
            'total': final,
            'currency': tariff['currency']
        }
    
    def _get_day_band(self, days: int) -> Dict[str, int]:
        if 1 <= days <= 7:
            return {'min': 1, 'max': 7}
        elif 8 <= days <= 15:
            return {'min': 8, 'max': 15}
        elif 16 <= days <= 31:
            return {'min': 16, 'max': 31}
        elif 32 <= days <= 45:
            return {'min': 32, 'max': 45}
        elif 46 <= days <= 92:
            return {'min': 46, 'max': 92}
        return None
    
    def _get_group_discount_rate(self, num_travellers: int) -> float:
        for tier in self.rules['group_discount_tiers']:
            min_t = tier['min_travellers']
            max_t = tier.get('max_travellers')
            if max_t is None:
                if num_travellers >= min_t:
                    return tier['discount_rate']
            elif min_t <= num_travellers <= max_t:
                return tier['discount_rate']
        return 0.0
