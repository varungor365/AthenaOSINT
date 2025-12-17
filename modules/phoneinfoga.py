"""
PhoneInfoga Lite Module.
Validates phone numbers and extracts carrier info using python-phonenumbers.
"""

import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from core.engine import Profile

META = {
    'description': 'Advanced phone number info (Carrier, Location)',
    'target_type': 'phone'
}

def scan(target: str, profile: Profile) -> None:
    try:
        # Parse number
        parsed = phonenumbers.parse(target, None)
        
        if not phonenumbers.is_valid_number(parsed):
            return

        result = {
            'valid': True,
            'national_format': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL),
            'international_format': phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            'carrier': carrier.name_for_number(parsed, "en"),
            'location': geocoder.description_for_number(parsed, "en"),
            'timezones': list(timezone.time_zones_for_number(parsed)),
            'type': 'Mobile' if phonenumbers.number_type(parsed) == phonenumbers.PhoneNumberType.MOBILE else 'Fixed/VoIP'
        }
        
        profile.add_pattern(f"Phone: {result['international_format']}", "high", "Verified Active Number")
        profile.locations.append(result['location'])
        
        profile.raw_data.setdefault('phone_data', []).append(result)
        
    except Exception as e:
        print(f"Phone scan error: {e}")
