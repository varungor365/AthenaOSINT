"""
Core engine for AthenaOSINT.

This module contains the main orchestration logic and data models
for running OSINT scans and generating reports.
"""

import json
import csv
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
from colorama import Fore, Style
from loguru import logger
import importlib

from config import get_config


@dataclass
class Profile:
    """Data model for storing all gathered intelligence on a target."""
    
    target_query: str
    target_type: str = 'unknown'
    scan_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Core data fields
    emails: List[str] = field(default_factory=list)
    usernames: Dict[str, str] = field(default_factory=dict)  # {platform: username}
    phone_numbers: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    subdomains: List[str] = field(default_factory=list)
    
    # Advanced data
    breaches: List[Dict[str, Any]] = field(default_factory=list)
    metadata: List[Dict[str, Any]] = field(default_factory=list)
    social_posts: List[Dict[str, Any]] = field(default_factory=list)
    related_ips: List[str] = field(default_factory=list)
    related_entities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Raw data storage
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Scan metadata
    modules_run: List[str] = field(default_factory=list)
    scan_duration: float = 0.0
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    def add_email(self, email: str):
        """Add an email if not already present."""
        email = email.lower().strip()
        if email and email not in self.emails:
            self.emails.append(email)
    
    def add_username(self, platform: str, username: str):
        """Add a username for a platform."""
        if platform and username:
            self.usernames[platform.lower()] = username
    
    def add_domain(self, domain: str):
        """Add a domain if not already present."""
        domain = domain.lower().strip()
        if domain and domain not in self.domains:
            self.domains.append(domain)
    
    def add_subdomain(self, subdomain: str):
        """Add a subdomain if not already present."""
        subdomain = subdomain.lower().strip()
        if subdomain and subdomain not in self.subdomains:
            self.subdomains.append(subdomain)
    
    def add_phone(self, phone: str):
        """Add a phone number if not already present."""
        phone = phone.strip()
        if phone and phone not in self.phone_numbers:
            self.phone_numbers.append(phone)
    
    def add_ip(self, ip: str):
        """Add an IP address if not already present."""
        ip = ip.strip()
        if ip and ip not in self.related_ips:
            self.related_ips.append(ip)
    
    def add_breach(self, breach: Dict[str, Any]):
        """Add breach information."""
        if breach:
            self.breaches.append(breach)
    
    def add_metadata(self, metadata: Dict[str, Any]):
        """Add file metadata."""
        if metadata:
            self.metadata.append(metadata)
    
    def add_error(self, module: str, error: str):
        """Record an error during scanning."""
        self.errors.append({
            'module': module,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary."""
        return asdict(self)
    
    def get_summary(self) -> Dict[str, int]:
        """Get a summary count of all data."""
        return {
            'emails': len(self.emails),
            'usernames': len(self.usernames),
            'phone_numbers': len(self.phone_numbers),
            'domains': len(self.domains),
            'subdomains': len(self.subdomains),
            'breaches': len(self.breaches),
            'social_posts': len(self.social_posts),
            'related_ips': len(self.related_ips),
            'related_entities': len(self.related_entities),
            'modules_run': len(self.modules_run),
            'errors': len(self.errors)
        }

    def get_graph_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert profile data into a graph structure (nodes/edges)."""
        nodes = []
        edges = []
        
        # Central Node (Target)
        root_id = "root"
        nodes.append({'id': root_id, 'label': self.target_query, 'group': 'target'})
        
        # Helper to add node/edge safely
        added_ids = {root_id}
        
        def add_node(id, label, group, source_id=root_id):
            if id not in added_ids:
                nodes.append({'id': id, 'label': label, 'group': group})
                added_ids.add(id)
            # Add edge even if node exists (multiple connections)
            edges.append({'from': source_id, 'to': id})

        # Emails
        for email in self.emails:
            add_node(f"email_{email}", email, 'email')
            
        # Usernames
        for platform, username in self.usernames.items():
            node_id = f"user_{username}_{platform}"
            add_node(node_id, f"{username} ({platform})", 'username')
            
        # Domains
        for domain in self.domains:
            add_node(f"domain_{domain}", domain, 'domain')
            
        # Subdomains (connect to respective domain if possible, else root)
        for subdomain in self.subdomains:
            # simple logic: connect to root for now, or finding parent domain could be complex
            add_node(f"sub_{subdomain}", subdomain, 'subdomain')
            
        # IPs
        for ip in self.related_ips:
            add_node(f"ip_{ip}", ip, 'ip')
            
        return {'nodes': nodes, 'edges': edges}


class AthenaEngine:
    """Main orchestration engine for OSINT scans."""
    
    def __init__(
        self,
        target_query: str,
        target_type: str = 'unknown',
        use_intelligence: bool = False,
        quiet: bool = False
    ):
        """Initialize the AthenaEngine.
        
        Args:
            target_query: The target to investigate
            target_type: Type of target (email, domain, username, etc.)
            use_intelligence: Enable intelligent analysis
            quiet: Suppress progress messages
        """
        self.config = get_config()
        self.profile = Profile(target_query=target_query, target_type=target_type)
        self.use_intelligence = use_intelligence
        self.quiet = quiet
        self.start_time = None
        self.analyzer = None
        
        if use_intelligence:
            try:
                from intelligence.analyzer import IntelligenceAnalyzer
                self.analyzer = IntelligenceAnalyzer()
            except ImportError:
                logger.warning("Intelligence layer not available")
    
    def _print_status(self, message: str, status: str = 'info'):
        """Print colored status message."""
        if self.quiet:
            return
        
        colors = {
            'info': Fore.CYAN,
            'success': Fore.GREEN,
            'warning': Fore.YELLOW,
            'error': Fore.RED
        }
        
        symbols = {
            'info': '→',
            'success': '✓',
            'warning': '!',
            'error': '✗'
        }
        
        color = colors.get(status, Fore.WHITE)
        symbol = symbols.get(status, '•')
        
        print(f"{color}[{symbol}] {message}{Style.RESET_ALL}")
    
    def run_scan(self, module_list: List[str]):
        """Run OSINT scan with specified modules.
        
        Args:
            module_list: List of module names to execute
        """
        self.start_time = time.time()
        self._print_status(f"Starting scan with {len(module_list)} modules", 'info')
        
        for module_name in module_list:
            try:
                self._run_module(module_name)
            except Exception as e:
                error_msg = f"Module {module_name} failed: {str(e)}"
                logger.error(error_msg)
                self.profile.add_error(module_name, str(e))
                self._print_status(error_msg, 'error')
        
        # Calculate scan duration
        self.profile.scan_duration = time.time() - self.start_time
        
        # Run modules that require prior results (e.g. Scrapers)
        try:
             import modules.profile_scraper as profile_scraper
             profile_scraper.scan(self.profile.target_query, self.profile)
             self.profile.modules_run.append('profile_scraper')
             self._print_status("Profile Scraper analysis complete", 'success')
        except ImportError:
             pass
        except Exception as e:
             logger.error(f"Profile scraper failed: {e}")

        # Run intelligence analysis if enabled
        if self.use_intelligence:
            self._print_status("Running intelligence analysis...", 'info')
            
            # 1. Identity Resolution
            try:
                from intelligence.identity_resolver import IdentityResolver
                resolver = IdentityResolver()
                resolver.resolve_identity(self.profile)
                self._print_status("Identity resolution complete", 'success')
            except Exception as e:
                logger.error(f"Identity resolution failed: {e}")

            # 2. Pattern Analysis + AI
            if self.analyzer:
                try:
                    self.analyzer.analyze_profile(self.profile)
                    self._print_status("AI Pattern analysis complete", 'success')
                except Exception as e:
                    logger.error(f"Intelligence analysis failed: {e}")
                    self._print_status(f"Intelligence analysis failed: {e}", 'error')
        
        # Print summary
        self._print_summary()
    
    def _run_module(self, module_name: str):
        """Run a single OSINT module.
        
        Args:
            module_name: Name of the module to run
        """
        self._print_status(f"Running {module_name} module...", 'info')
        
        try:
            # Dynamically import the module
            module = importlib.import_module(f'modules.{module_name}')
            
            # Execute the scan function
            if hasattr(module, 'scan'):
                module.scan(self.profile.target_query, self.profile)
                self.profile.modules_run.append(module_name)
                self._print_status(f"{module_name} completed", 'success')
            else:
                raise AttributeError(f"Module {module_name} has no scan() function")
                
        except ImportError as e:
            error_msg = f"Module {module_name} not found or dependencies missing"
            logger.warning(f"{error_msg}: {e}")
            self._print_status(error_msg, 'warning')
            self.profile.add_error(module_name, "Module not available")
        except Exception as e:
            raise
    
    def _print_summary(self):
        """Print scan summary."""
        if self.quiet:
            return
        
        summary = self.profile.get_summary()
        
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"  SCAN SUMMARY")
        print(f"{'=' * 60}{Style.RESET_ALL}\n")
        
        print(f"  Target: {Fore.WHITE}{self.profile.target_query}{Style.RESET_ALL}")
        print(f"  Type: {Fore.WHITE}{self.profile.target_type}{Style.RESET_ALL}")
        print(f"  Duration: {Fore.WHITE}{self.profile.scan_duration:.2f}s{Style.RESET_ALL}\n")
        
        print(f"{Fore.CYAN}  Results:{Style.RESET_ALL}")
        print(f"    Emails: {Fore.GREEN}{summary['emails']}{Style.RESET_ALL}")
        print(f"    Usernames: {Fore.GREEN}{summary['usernames']}{Style.RESET_ALL}")
        print(f"    Phone Numbers: {Fore.GREEN}{summary['phone_numbers']}{Style.RESET_ALL}")
        print(f"    Domains: {Fore.GREEN}{summary['domains']}{Style.RESET_ALL}")
        print(f"    Subdomains: {Fore.GREEN}{summary['subdomains']}{Style.RESET_ALL}")
        print(f"    Breaches: {Fore.GREEN}{summary['breaches']}{Style.RESET_ALL}")
        print(f"    IPs: {Fore.GREEN}{summary['related_ips']}{Style.RESET_ALL}")
        
        if summary['errors'] > 0:
            print(f"\n  {Fore.YELLOW}Errors: {summary['errors']}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    
    def generate_report(
        self,
        output_format: str = 'json',
        custom_filename: Optional[str] = None
    ) -> Path:
        """Generate and save a report.
        
        Args:
            output_format: Format for the report ('json', 'html', 'csv')
            custom_filename: Custom filename without extension
            
        Returns:
            Path to the generated report file
        """
        reports_dir = self.config.get('REPORTS_DIR')
        
        # Generate filename
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = int(time.time())
            filename = f"athena_report_{timestamp}"
        
        # Generate report based on format
        if output_format == 'json':
            return self._generate_json_report(reports_dir, filename)
        elif output_format == 'html':
            return self._generate_html_report(reports_dir, filename)
        elif output_format == 'csv':
            return self._generate_csv_report(reports_dir, filename)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_json_report(self, output_dir: Path, filename: str) -> Path:
        """Generate JSON report."""
        filepath = output_dir / f"{filename}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.profile.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON report saved to {filepath}")
        return filepath
    
    def _generate_html_report(self, output_dir: Path, filename: str) -> Path:
        """Generate HTML report with styling."""
        filepath = output_dir / f"{filename}.html"
        
        html_content = self._build_html_content()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report saved to {filepath}")
        return filepath
    
    def _build_html_content(self) -> str:
        """Build HTML report content."""
        summary = self.profile.get_summary()
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AthenaOSINT Report - {self.profile.target_query}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header p {{ font-size: 1.2em; opacity: 0.9; }}
        .content {{ padding: 40px; }}
        .section {{
            margin-bottom: 40px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 30px;
        }}
        .section:last-child {{ border-bottom: none; }}
        .section h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
        }}
        .section h2::before {{
            content: '▸';
            margin-right: 10px;
            color: #764ba2;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .info-card h3 {{
            color: #764ba2;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .info-card p {{
            font-size: 1.5em;
            font-weight: bold;
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin: 5px 5px 5px 0;
        }}
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .badge-info {{ background: #d1ecf1; color: #0c5460; }}
        .list-item {{
            padding: 10px;
            background: #f8f9fa;
            margin: 5px 0;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 AthenaOSINT Report</h1>
            <p>Intelligence gathered on: {self.profile.target_query}</p>
        </div>
        
        <div class="content">
            <!-- Overview Section -->
            <div class="section">
                <h2>Overview</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>Target</h3>
                        <p>{self.profile.target_query}</p>
                    </div>
                    <div class="info-card">
                        <h3>Type</h3>
                        <p>{self.profile.target_type}</p>
                    </div>
                    <div class="info-card">
                        <h3>Scan Date</h3>
                        <p>{self.profile.scan_timestamp[:10]}</p>
                    </div>
                    <div class="info-card">
                        <h3>Duration</h3>
                        <p>{self.profile.scan_duration:.2f}s</p>
                    </div>
                </div>
                
                <h3>Modules Executed:</h3>
                <div>
                    {"".join([f'<span class="badge badge-info">{m}</span>' for m in self.profile.modules_run])}
                </div>
            </div>
"""
        
        # Add emails section
        if self.profile.emails:
            html += f"""
            <div class="section">
                <h2>Email Addresses ({len(self.profile.emails)})</h2>
                {"".join([f'<div class="list-item">{email}</div>' for email in self.profile.emails])}
            </div>
"""
        
        # Add usernames section
        if self.profile.usernames:
            html += f"""
            <div class="section">
                <h2>Usernames ({len(self.profile.usernames)})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Platform</th>
                            <th>Username</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join([f'<tr><td>{platform.title()}</td><td>{username}</td></tr>' for platform, username in self.profile.usernames.items()])}
                    </tbody>
                </table>
            </div>
"""
        
        # Add breaches section
        if self.profile.breaches:
            html += f"""
            <div class="section">
                <h2>Data Breaches ({len(self.profile.breaches)})</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Breach Name</th>
                            <th>Date</th>
                            <th>Compromised Data</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for breach in self.profile.breaches:
                data_classes = breach.get('data_classes', [])
                if isinstance(data_classes, list):
                    data_str = ', '.join(data_classes)
                else:
                    data_str = str(data_classes)
                    
                html += f"""
                        <tr>
                            <td>{breach.get('name', 'Unknown')}</td>
                            <td>{breach.get('date', 'Unknown')}</td>
                            <td>{data_str}</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
            </div>
"""
        
        # Add domains/subdomains
        if self.profile.domains or self.profile.subdomains:
            html += """
            <div class="section">
                <h2>Domains & Subdomains</h2>
"""
            if self.profile.domains:
                html += f"""
                <h3>Domains ({len(self.profile.domains)})</h3>
                {"".join([f'<div class="list-item">{domain}</div>' for domain in self.profile.domains])}
"""
            if self.profile.subdomains:
                html += f"""
                <h3>Subdomains ({len(self.profile.subdomains)})</h3>
                {"".join([f'<div class="list-item">{subdomain}</div>' for subdomain in self.profile.subdomains[:50]])}
                {f'<p><em>... and {len(self.profile.subdomains) - 50} more</em></p>' if len(self.profile.subdomains) > 50 else ''}
"""
            html += """
            </div>
"""
        
        # Close HTML
        html += f"""
            <!-- Raw Data Section -->
            <div class="section">
                <h2>Raw Data</h2>
                <pre>{json.dumps(self.profile.raw_data, indent=2)}</pre>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by AthenaOSINT v1.0.0 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>⚠️ This report contains sensitive information. Handle with care.</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_csv_report(self, output_dir: Path, filename: str) -> Path:
        """Generate CSV report."""
        filepath = output_dir / f"{filename}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'Target', 'Type', 'Category', 'Platform/Source',
                'Value', 'Date', 'Additional Info'
            ])
            
            # Write emails
            for email in self.profile.emails:
                writer.writerow([
                    self.profile.target_query, self.profile.target_type,
                    'Email', '', email, '', ''
                ])
            
            # Write usernames
            for platform, username in self.profile.usernames.items():
                writer.writerow([
                    self.profile.target_query, self.profile.target_type,
                    'Username', platform, username, '', ''
                ])
            
            # Write breaches
            for breach in self.profile.breaches:
                writer.writerow([
                    self.profile.target_query, self.profile.target_type,
                    'Breach', breach.get('name', ''),
                    breach.get('description', ''),
                    breach.get('date', ''),
                    ', '.join(breach.get('data_classes', []))
                ])
            
            # Write domains
            for domain in self.profile.domains:
                writer.writerow([
                    self.profile.target_query, self.profile.target_type,
                    'Domain', '', domain, '', ''
                ])
            
            # Write subdomains
            for subdomain in self.profile.subdomains:
                writer.writerow([
                    self.profile.target_query, self.profile.target_type,
                    'Subdomain', '', subdomain, '', ''
                ])
        
        logger.info(f"CSV report saved to {filepath}")
        return filepath
