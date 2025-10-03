import re
from datetime import datetime
from typing import Dict, Optional


class MRZParser:
    
    def parse_passport(self, ocr_text: str) -> Optional[Dict]:
        lines = ocr_text.upper().split('\n')
        
        line1_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^P<', line.strip()):
                line1_idx = i
                break
        
        if line1_idx is None or line1_idx + 1 >= len(lines):
            return None
        
        line1 = lines[line1_idx].strip().ljust(44, '<')[:44]
        line2 = lines[line1_idx + 1].strip().ljust(44, '<')[:44]
        
        names_part = line1[5:44].replace('<', ' ').strip()
        name_parts = [p for p in names_part.split('  ') if p]
        
        last_name = name_parts[0] if name_parts else ''
        first_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        full_name = f"{first_name} {last_name}".strip()
        
        passport_number = line2[0:9].replace('<', '').strip()
        nationality = line2[10:13]
        
        dob_str = line2[13:19]
        dob = self._parse_mrz_date(dob_str)
        
        sex = line2[20]
        
        expiry_str = line2[21:27]
        expiry = self._parse_mrz_date(expiry_str)
        
        return {
            'passport_number': passport_number,
            'full_name': full_name,
            'first_name': first_name,
            'last_name': last_name,
            'date_of_birth': dob,
            'nationality': nationality,
            'sex': sex,
            'expiry_date': expiry,
            'mrz_line1': line1,
            'mrz_line2': line2
        }
    
    def _parse_mrz_date(self, date_str: str) -> Optional[str]:
        if not date_str or len(date_str) != 6:
            return None
        
        try:
            yy = int(date_str[0:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:6])
            
            yyyy = 2000 + yy if yy <= 50 else 1900 + yy
            
            return f"{yyyy:04d}-{mm:02d}-{dd:02d}"
        except:
            return None
