#!/usr/bin/env python3
"""
AthenaOSINT - Advanced Open Source Intelligence Framework

Main CLI entry point for the AthenaOSINT framework.
"""

import sys
import click
from colorama import init, Fore, Style
from pathlib import Path

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import load_config
from core.engine import AthenaEngine
from core.validators import validate_target, detect_target_type
from loguru import logger


# Configure logger
config = load_config()
logger.add(
    config.get('LOGS_DIR') / "athena_{time}.log",
    rotation="10 MB",
    retention="7 days",
    level=config.get('LOG_LEVEL')
)


def print_banner():
    """Print the AthenaOSINT banner."""
    banner = f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     █████╗ ████████╗██╗  ██╗███████╗███╗   ██╗ █████╗       ║
║    ██╔══██╗╚══██╔══╝██║  ██║██╔════╝████╗  ██║██╔══██╗      ║
║    ███████║   ██║   ███████║█████╗  ██╔██╗ ██║███████║      ║
║    ██╔══██║   ██║   ██╔══██║██╔══╝  ██║╚██╗██║██╔══██║      ║
║    ██║  ██║   ██║   ██║  ██║███████╗██║ ╚████║██║  ██║      ║
║    ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝      ║
║                                                               ║
║            Advanced Open Source Intelligence Framework       ║
║                     Version 1.0.0                            ║
╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)


@click.group()
@click.version_option(version='1.0.0', prog_name='AthenaOSINT')
def athena():
    """
    AthenaOSINT - Advanced OSINT Framework
    
    A comprehensive tool for gathering open source intelligence
    from multiple sources with intelligent analysis and automation.
    """
    pass


@athena.command()
@click.argument('target')
@click.option(
    '--modules', '-m',
    default='sherlock,holehe,leak_checker,subfinder,dnsdumpster,amass,nuclei,foca,profile_scraper',
    help='Comma-separated list of modules to run (default: all core modules)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'html', 'csv', 'all'], case_sensitive=False),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '--output', '-o',
    help='Custom output filename (without extension)'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress progress messages'
)
@click.option(
    '--use-intelligence',
    is_flag=True,
    help='Enable intelligent analysis after scan'
)
def run(target, modules, format, output, quiet, use_intelligence):
    """
    Run an OSINT scan on a target.
    
    TARGET can be an email address, username, domain, or phone number.
    
    Examples:
        athena run john.doe@example.com
        athena run johndoe --modules sherlock,holehe
        athena run example.com --format html
        athena run +1234567890 --use-intelligence
    """
    if not quiet:
        print_banner()
    
    # Validate target
    if not validate_target(target):
        click.echo(f"{Fore.RED}[✗] Invalid target format: {target}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Detect target type
    target_type = detect_target_type(target)
    if not quiet:
        click.echo(f"{Fore.CYAN}[→] Target detected as: {target_type}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}[→] Starting scan on: {target}{Style.RESET_ALL}\n")
    
    # Parse modules
    module_list = [m.strip() for m in modules.split(',') if m.strip()]
    
    try:
        # Initialize engine
        engine = AthenaEngine(
            target_query=target,
            target_type=target_type,
            use_intelligence=use_intelligence,
            quiet=quiet
        )
        
        # Run scan
        engine.run_scan(module_list)
        
        # Generate report(s)
        if format == 'all':
            formats = ['json', 'html', 'csv']
        else:
            formats = [format]
        
        for fmt in formats:
            report_path = engine.generate_report(output_format=fmt, custom_filename=output)
            if not quiet:
                click.echo(f"{Fore.GREEN}[✓] {fmt.upper()} report saved: {report_path}{Style.RESET_ALL}")
        
        if not quiet:
            click.echo(f"\n{Fore.GREEN}[✓] Scan completed successfully!{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        click.echo(f"\n{Fore.YELLOW}[!] Scan interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Scan failed")
        click.echo(f"{Fore.RED}[✗] Scan failed: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


@athena.command()
@click.argument('target')
@click.option(
    '--depth', '-d',
    type=int,
    default=2,
    help='Maximum depth for recursive scanning (default: 2)'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'html', 'csv'], case_sensitive=False),
    default='json',
    help='Output format (default: json)'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress progress messages'
)
def deepscan(target, depth, format, quiet):
    """
    Run a deep, recursive OSINT scan with intelligence analysis.
    
    This command uses AI-powered analysis to discover related targets
    and automatically scan them up to the specified depth.
    
    Examples:
        athena deepscan john.doe@example.com
        athena deepscan johndoe --depth 3
    """
    if not quiet:
        print_banner()
    
    # Validate target
    if not validate_target(target):
        click.echo(f"{Fore.RED}[✗] Invalid target format: {target}{Style.RESET_ALL}")
        sys.exit(1)
    
    # Validate depth
    max_depth = config.get('MAX_SCAN_DEPTH', 3)
    if depth > max_depth:
        click.echo(f"{Fore.YELLOW}[!] Depth limited to {max_depth} (configured maximum){Style.RESET_ALL}")
        depth = max_depth
    
    if not quiet:
        click.echo(f"{Fore.CYAN}[→] Starting deep scan on: {target}{Style.RESET_ALL}")
        click.echo(f"{Fore.CYAN}[→] Maximum depth: {depth}{Style.RESET_ALL}\n")
    
    try:
        from intelligence.automator import Automator
        
        # Initialize automator
        automator = Automator(max_depth=depth, quiet=quiet)
        
        # Run automated chain
        results = automator.run_automated_chain(target)
        
        if not quiet:
            click.echo(f"\n{Fore.GREEN}[✓] Deep scan completed!{Style.RESET_ALL}")
            click.echo(f"{Fore.CYAN}[→] Scanned {len(results)} targets total{Style.RESET_ALL}")
        
        # Generate combined report
        # TODO: Implement combined report generation
        
    except ImportError:
        click.echo(f"{Fore.RED}[✗] Intelligence layer not available{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Deep scan failed")
        click.echo(f"{Fore.RED}[✗] Deep scan failed: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


@athena.command()
def modules():
    """List all available OSINT modules."""
    print_banner()
    
    from modules import get_available_modules
    
    click.echo(f"{Fore.CYAN}Available OSINT Modules:{Style.RESET_ALL}\n")
    
    available = get_available_modules()
    
    for module_name, module_info in available.items():
        status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if module_info['available'] else f"{Fore.RED}✗{Style.RESET_ALL}"
        click.echo(f"  {status} {Fore.CYAN}{module_name:<20}{Style.RESET_ALL} - {module_info['description']}")
        click.echo(f"      Target type: {module_info['target_type']}")
        if not module_info['available']:
            click.echo(f"      {Fore.YELLOW}Requires: {module_info['requirements']}{Style.RESET_ALL}")
        click.echo()


@athena.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option(
    '--format', '-f',
    type=click.Choice(['json', 'html', 'csv'], case_sensitive=False),
    default='json',
    help='Output format (default: json)'
)
def extract_metadata(file_path, format):
    """Extract metadata from a file using ExifTool."""
    print_banner()
    
    click.echo(f"{Fore.CYAN}[→] Extracting metadata from: {file_path}{Style.RESET_ALL}\n")
    
    try:
        from modules.exiftool import scan_file
        from core.engine import Profile
        
        # Create empty profile
        profile = Profile(target_query=file_path)
        
        # Run extraction
        scan_file(file_path, profile)
        
        # Display results
        if profile.metadata:
            click.echo(f"{Fore.GREEN}[✓] Metadata extracted successfully{Style.RESET_ALL}\n")
            
            from tabulate import tabulate
            
            # Format metadata for display
            table_data = []
            for item in profile.metadata:
                for key, value in item.items():
                    table_data.append([key, value])
            
            click.echo(tabulate(table_data, headers=['Property', 'Value'], tablefmt='grid'))
        else:
            click.echo(f"{Fore.YELLOW}[!] No metadata found{Style.RESET_ALL}")
    
    except Exception as e:
        logger.exception("Metadata extraction failed")
        click.echo(f"{Fore.RED}[✗] Extraction failed: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


@athena.command()
def config_check():
    """Check configuration and API key status."""
    print_banner()
    
    click.echo(f"{Fore.CYAN}Configuration Status:{Style.RESET_ALL}\n")
    
    api_keys = [
        'HIBP_API_KEY',
        'DEHASHED_API_KEY',
        'INTELX_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'SHODAN_API_KEY',
        'VIRUSTOTAL_API_KEY',
        'HUNTER_API_KEY'
    ]
    
    from tabulate import tabulate
    
    table_data = []
    for key in api_keys:
        value = config.get(key)
        status = f"{Fore.GREEN}✓ Configured{Style.RESET_ALL}" if value else f"{Fore.YELLOW}✗ Not set{Style.RESET_ALL}"
        table_data.append([key, status])
    
    click.echo(tabulate(table_data, headers=['API Key', 'Status'], tablefmt='grid'))
    
    click.echo(f"\n{Fore.CYAN}Application Settings:{Style.RESET_ALL}\n")
    
    settings_data = [
        ['Log Level', config.get('LOG_LEVEL')],
        ['Max Scan Depth', config.get('MAX_SCAN_DEPTH')],
        ['Rate Limit', f"{config.get('RATE_LIMIT')} req/min"],
        ['Module Timeout', f"{config.get('MODULE_TIMEOUT')} seconds"],
        ['Data Directory', config.get('DATA_DIR')],
        ['Reports Directory', config.get('REPORTS_DIR')],
    ]
    
    click.echo(tabulate(settings_data, headers=['Setting', 'Value'], tablefmt='grid'))


if __name__ == '__main__':
    athena()
