"""
Module Registry.
Central source of truth for all OSINT modules, their categories, and capabilities.
"""

MODULE_REGISTRY = {
    # --- SOCIAL MEDIA INTELLIGENCE ---
    'sherlock': {
        'category': 'Social Media',
        'desc': 'Find usernames across 400+ social networks',
        'type': 'username',
        'risk': 'low',
        'emoji': '👤'
    },
    'ghunt': {
        'category': 'Social Media', 
        'desc': 'Extract deep Google Account info (Photo, Reviews)',
        'type': 'email',
        'risk': 'safe',
        'emoji': '🇬'
    },
    'maigret': {
        'category': 'Social Media',
        'desc': 'Advanced username enumeration with PDF reporting',
        'type': 'username',
        'risk': 'safe',
        'emoji': '🕵️'
    },
    'profile_scraper': {
        'category': 'Social Media',
        'desc': 'Extract bios/links from social profiles',
        'type': 'url',
        'risk': 'low',
        'emoji': '📱'
    },
    'carbon14': {
        'category': 'Social Media',
        'desc': 'Check if email is on dating sites',
        'type': 'email',
        'risk': 'safe',
        'emoji': '💘'
    },
    'witnessme': {
        'category': 'Social Media',
        'desc': 'Automated screenshot of profiles/sites',
        'type': 'url',
        'risk': 'safe',
        'emoji': '📸'
    },

    # --- EMAIL & PERSONAL INFO ---
    'holehe': {
        'category': 'Identity',
        'desc': 'Check email registration on 120+ sites',
        'type': 'email',
        'risk': 'safe',
        'emoji': '📧'
    },
    'leak_checker': {
        'category': 'Identity',
        'desc': 'Search HIBP and DeHashed for breaches',
        'type': 'email',
        'risk': 'safe',
        'emoji': '🔓'
    },
    'phoneinfoga': {
        'category': 'Identity',
        'desc': 'Advanced phone number scanning (Carrier, Loc)',
        'type': 'phone',
        'risk': 'safe',
        'emoji': '📞'
    },
    'email_permutator': {
        'category': 'Identity',
        'desc': 'Generate and verify valid email permutations',
        'type': 'name',
        'risk': 'low',
        'emoji': '🔄'
    },
    
    # --- NETWORK & CLOUD ---
    'shodan': {
        'category': 'Network',
        'desc': 'Search for connected devices/IoT',
        'type': 'ip',
        'risk': 'safe',
        'emoji': '📡'
    },
    'censys': {
        'category': 'Network',
        'desc': 'Analyze SSL certs and hidden servers',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🔍'
    },
    'amass': {
        'category': 'Network',
        'desc': 'Advanced subdomain enumeration',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🔢'
    },
    'dnsdumpster': {
        'category': 'Network',
        'desc': 'Visual DNS mapping',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🗺️'
    },
    'subfinder': {
        'category': 'Network',
        'desc': 'Fast passive subdomain discovery',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🦈'
    },
    'port_scanner': {
        'category': 'Network',
        'desc': 'Active port scan (Top 20 ports)',
        'type': 'ip',
        'risk': 'medium',
        'emoji': '🔌'
    },
    'cloud_hunter': {
        'category': 'Network',
        'desc': 'Find open S3/Azure/Google buckets',
        'type': 'brand',
        'risk': 'safe',
        'emoji': '☁️'
    },
    'urlscan': {
        'category': 'Network',
        'desc': 'Analyze website behavior safely',
        'type': 'url',
        'risk': 'safe',
        'emoji': '🕸️'
    },
    'dnstwist': {
        'category': 'Network',
        'desc': 'Find phishing domains/typosquatting',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🎣'
    },
    
    # --- DARK WEB & OPSEC ---
    'ahmia': {
        'category': 'Dark Web',
        'desc': 'Search largest .onion safe-search engine',
        'type': 'keyword',
        'risk': 'safe',
        'emoji': '🧅'
    },
    'onionscan': {
        'category': 'Dark Web',
        'desc': 'Scan .onion site for misconfigurations',
        'type': 'onion',
        'risk': 'high',
        'emoji': '🔦'
    },
    'smart_scraper': {
        'category': 'scraper',
        'description': 'AI-Powered Deep Web Scraper (ScrapeGraphAI)',
        'type': 'active',
        'risk': 'medium',
        'emoji': '🕷️'
    },
    'breach_harvester': {
        'category': 'harvest',
        'description': 'Autonomous Database Downloader',
        'type': 'active',
        'risk': 'high',
        'emoji': '📥'
    },
    'torbot': {
        'category': 'Dark Web',
        'description': 'Crawl .onion links to map structure',
        'type': 'onion',
        'risk': 'medium',
        'emoji': '🤖'
    },
    'firecrawl': {
        'category': 'scraper',
        'description': 'Turn websites into LLM-ready markdown',
        'type': 'url',
        'risk': 'medium',
        'emoji': '🔥'
    },
    'scrapling': {
        'category': 'scraper',
        'description': 'Undetectable High-Performance Scraper',
        'type': 'url',
        'risk': 'medium',
        'emoji': '🎭'
    },
    'onion_search': {
        'category': 'Dark Web',
        'description': 'Dark Web Search Engine Aggregator',
        'type': 'keyword',
        'risk': 'medium',
        'emoji': '🧅'
    },
    'maryam': {
        'category': 'Framework',
        'description': 'OWASP Maryam Wrapper',
        'type': 'domain',
        'risk': 'medium',
        'emoji': '🦄'
    },
    'websift': {
        'category': 'scraper',
        'description': 'Extract Contacts from Websites',
        'type': 'url',
        'risk': 'safe',
        'emoji': '🕸️'
    },
    'redeye': {
        'category': 'Dark Web',
        'description': 'Dark Web Market & Forum Monitor',
        'type': 'keyword',
        'risk': 'high',
        'emoji': '👹'
    },
    'sn0int': {
        'category': 'Framework',
        'description': 'sn0int OSINT Framework Wrapper',
        'type': 'domain',
        'risk': 'medium',
        'emoji': '🧶'
    },
    'instagram': {
        'category': 'Social Media',
        'description': 'Instagram Profile & Media Scraper',
        'type': 'username',
        'risk': 'medium',
        'emoji': '📸'
    },
    'facebook': {
        'category': 'Social Media',
        'description': 'Scrape Facebook Friend Lists',
        'type': 'username',
        'risk': 'high',
        'emoji': '📘'
    },
    'witnessme': {
        'category': 'Utils',
        'description': 'Automated Website Screenshotter',
        'type': 'url',
        'risk': 'safe',
        'emoji': '📸'
    },
    'port_scanner': {
        'category': 'Network',
        'description': 'Basic Port Scanner',
        'type': 'ip',
        'risk': 'medium',
        'emoji': '🔌'
    },
    'graph_exporter': {
        'category': 'Utils',
        'description': 'Export to GraphML (Maltego)',
        'type': 'none',
        'risk': 'safe',
        'emoji': '📊'
    },
    'rss_monitor': {
        'category': 'Automation',
        'description': 'RSS Feed Monitor (Medium/Blogs)',
        'type': 'username',
        'risk': 'safe',
        'emoji': '📰'
    },
    'proxy_scraper': {
        'category': 'Network',
        'description': 'Public Proxy Scraper',
        'type': 'none',
        'risk': 'safe',
        'emoji': '🛡️'
    },
    'spoof_check': {
        'category': 'Network',
        'description': 'Email Spoofing Check (SPF/DMARC)',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '📧'
    },
    'trufflehog': {
        'category': 'Scanner',
        'description': 'Secret & Key Scanner',
        'type': 'url',
        'risk': 'safe',
        'emoji': '🐷'
    },
    'doc_hunter': {
        'category': 'Recon',
        'description': 'Document & Metadata Hunter',
        'type': 'domain',
        'risk': 'medium',
        'emoji': '📄'
    },
    'linkedin': {
        'category': 'Social Media',
        'description': 'LinkedIn Dork Generator',
        'type': 'keyword',
        'risk': 'safe',
        'emoji': '👔'
    },
    'ghost_track': {
        'category': 'Real World',
        'description': 'IP & Phone Geolocation Tracker',
        'type': 'ip',
        'risk': 'safe',
        'emoji': '👻'
    },
    'pwndb': {
        'category': 'Dark Web',
        'desc': 'Search raw leaked passwords (Onion)',
        'type': 'email',
        'risk': 'safe',
        'emoji': '🔑'
    },
    'darksearch': {
        'category': 'Dark Web',
        'desc': 'API-based dark web search',
        'type': 'keyword',
        'risk': 'safe',
        'emoji': '🌑'
    },
    'darkfail': {
        'category': 'Dark Web',
        'desc': 'Check uptime of darknet markets',
        'type': 'none',
        'risk': 'safe',
        'emoji': '📉'
    },
    
    # --- FINANCE & BLOCKCHAIN ---
    'crypto_hunter': {
        'category': 'Finance',
        'desc': 'Analyze crypto addresses',
        'type': 'crypto',
        'risk': 'safe',
        'emoji': '₿'
    },
    'walletexplorer': {
        'category': 'Finance',
        'desc': 'Identify Bitcoin wallet owners',
        'type': 'crypto',
        'risk': 'safe',
        'emoji': '💰'
    },
    'kilos': {
        'category': 'Finance',
        'desc': 'Search darknet markets for goods',
        'type': 'keyword',
        'risk': 'safe',
        'emoji': '⚖️'
    },
    
    # --- DEV & SECURITY ---
    'gitrob': {
        'category': 'DevSec',
        'desc': 'Find secrets in GitHub repos',
        'type': 'username',
        'risk': 'safe',
        'emoji': '🐱'
    },
    'nuclei': {
        'category': 'DevSec',
        'desc': 'Vulnerability scanner',
        'type': 'domain',
        'risk': 'high',
        'emoji': '☢️'
    },
    'foca': {
        'category': 'DevSec',
        'desc': 'Document metadata analysis',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '📄'
    },
    'canary_checker': {
        'category': 'DevSec',
        'desc': 'Detect honeytokens/tracking',
        'type': 'url',
        'risk': 'safe',
        'emoji': '🐦'
    },
    
    # --- AUTOMATION & MISC ---
    'spiderfoot': {
        'category': 'Automation',
        'desc': 'Automates 100+ OSINT checks',
        'type': 'domain',
        'risk': 'medium',
        'emoji': '🕷️'
    },
    'photon': {
        'category': 'Automation',
        'desc': 'Fast web crawler (Extracts everything)',
        'type': 'url',
        'risk': 'medium',
        'emoji': '⚡'
    },
    'ocr': {
        'category': 'Utils',
        'desc': 'Extract text from images',
        'type': 'image',
        'risk': 'safe',
        'emoji': '📝'
    },
    'exiftool': {
        'category': 'Utils',
        'desc': 'Extract file metadata',
        'type': 'file',
        'risk': 'safe',
        'emoji': '📷'
    },
    'job_hunter': {
        'category': 'Utils',
        'desc': 'Infer tech stack from job posts',
        'type': 'company',
        'risk': 'safe',
        'emoji': '👔'
    },
    'auto_dorker': {
        'category': 'Automation',
        'desc': 'Automated Google Dorking',
        'type': 'keyword',
        'risk': 'safe',
        'emoji': '🔎'
    },
    'sentiment': {
        'category': 'Utils',
        'desc': 'Analyze text sentiment',
        'type': 'text',
        'risk': 'safe',
        'emoji': '🎭'
    },
    'theharvester': {
        'category': 'Network',
        'desc': 'Gather emails/subdomains/hosts',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🌾'
    },
    'wayback': {
        'category': 'Utils',
        'desc': 'Find archived URLs',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🏛️'
    },
    
    # --- ADVANCED ARSENAL ---
    'redghost': {
        'category': 'Social Media',
        'desc': 'Advanced Telegram OSINT & Recon',
        'type': 'username',
        'risk': 'medium',
        'emoji': '👻'
    },
    'passive_recon': {
        'category': 'Framework',
        'desc': 'Passive Open Source Intelligence Collection',
        'type': 'domain',
        'risk': 'safe',
        'emoji': '🕵️'
    },
    'go_recon': {
        'category': 'Recon',
        'desc': 'Advanced Go Arsenal (Chaos, Katana, GAU)',
        'type': 'domain',
        'risk': 'medium',
        'emoji': '🚀'
    },
    'bbot': {
        'category': 'Framework',
        'desc': 'BBOT Recursive OSINT Framework',
        'type': 'domain',
        'risk': 'medium',
        'emoji': '🐝'
    },
    'ghost_track': {
        'category': 'Real World',
        'desc': 'IP & Phone Geolocation Tracker',
        'type': 'ip',
        'risk': 'safe',
        'emoji': '👻'
    },
    'danxy': {
        'category': 'Framework',
        'desc': 'Danxy Multi-Tool Framework',
        'type': 'none',
        'risk': 'medium',
        'emoji': '🛠️'
    }
}
