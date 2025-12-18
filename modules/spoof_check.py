"""
SpoofCheck Module.
Checks SPF and DMARC records to determine if a domain can be spoofed.
"""
import dns.resolver
from loguru import logger
from core.engine import Profile

# Metadata
META = {
    'name': 'spoof_check',
    'description': 'Email Spoofing Check (SPF/DMARC)',
    'category': 'Network',
    'risk': 'safe', 
    'emoji': '📧'
}

def scan(target: str, profile: Profile):
    """
    Checks SPF/DMARC for target domain.
    """
    domain = target
    if '@' in target:
        domain = target.split('@')[-1]
    
    logger.info(f"[SpoofCheck] Checking {domain}...")
    
    results = {
        'spf': {'present': False, 'record': None, 'strong': False},
        'dmarc': {'present': False, 'record': None, 'strong': False},
        'spoofable': True
    }
    
    # 1. Check SPF
    try:
        answers = dns.resolver.resolve(domain, 'TXT')
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith('v=spf1'):
                results['spf']['present'] = True
                results['spf']['record'] = txt
                if '-all' in txt:
                    results['spf']['strong'] = True # Hard fail
                elif '~all' in txt:
                    results['spf']['strong'] = False # Soft fail
                else:
                    results['spf']['strong'] = False # Neutral/Allow
                break
    except Exception:
        pass

    # 2. Check DMARC
    try:
        dmarc_domain = f"_dmarc.{domain}"
        answers = dns.resolver.resolve(dmarc_domain, 'TXT')
        for rdata in answers:
            txt = rdata.to_text().strip('"')
            if txt.startswith('v=DMARC1'):
                results['dmarc']['present'] = True
                results['dmarc']['record'] = txt
                if 'p=reject' in txt or 'p=quarantine' in txt:
                    results['dmarc']['strong'] = True
                break
    except Exception:
        pass
        
    # 3. Verdict
    if results['spf']['strong'] and results['dmarc']['strong']:
        results['spoofable'] = False
        logger.success(f"[SpoofCheck] {domain} is protected against spoofing.")
    else:
        results['spoofable'] = True
        logger.warning(f"[SpoofCheck] {domain} is potentially SPOOFABLE.")
        
    profile.add_metadata({'email_security': results})
