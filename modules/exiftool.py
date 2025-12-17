"""
ExifTool module for AthenaOSINT.

This module extracts metadata from files using ExifTool.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Any
from colorama import Fore, Style
from loguru import logger


def scan_file(file_path: str, profile) -> None:
    """Extract metadata from a file using ExifTool.
    
    Args:
        file_path: Path to file to analyze
        profile: Profile object to update with results
    """
    if not Path(file_path).exists():
        logger.error(f"File not found: {file_path}")
        profile.add_error('exiftool', f"File not found: {file_path}")
        return
    
    print(f"{Fore.CYAN}[+] Running ExifTool module...{Style.RESET_ALL}")
    
    try:
        # Check if exiftool is installed
        check_cmd = ['exiftool', '-ver']
        result = subprocess.run(
            check_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            logger.warning("ExifTool not installed or not in PATH")
            profile.add_error('exiftool', 'Tool not installed')
            print(f"{Fore.YELLOW}[!] ExifTool not available{Style.RESET_ALL}")
            return
        
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.warning(f"ExifTool check failed: {e}")
        profile.add_error('exiftool', 'Tool not available')
        print(f"{Fore.YELLOW}[!] ExifTool not available{Style.RESET_ALL}")
        return
    
    try:
        # Run ExifTool with JSON output
        cmd = [
            'exiftool',
            '-json',
            '-a',  # Extract duplicate tags
            '-G',  # Show group names
            file_path
        ]
        
        print(f"  {Fore.CYAN}└─ Extracting metadata from {Path(file_path).name}...{Style.RESET_ALL}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = f"ExifTool failed with exit code {result.returncode}"
            logger.error(error_msg)
            profile.add_error('exiftool', error_msg)
            return
        
        # Parse JSON output
        metadata_list = json.loads(result.stdout)
        
        if not metadata_list:
            print(f"{Fore.YELLOW}[!] No metadata found{Style.RESET_ALL}")
            return
        
        metadata = metadata_list[0]  # ExifTool returns array with single object
        
        # Extract key information
        extracted_data = _extract_key_metadata(metadata, file_path)
        
        # Update profile
        profile.add_metadata(extracted_data)
        
        # Look for email addresses in metadata
        for key, value in metadata.items():
            if isinstance(value, str) and '@' in value:
                from core.validators import validate_email
                if validate_email(value):
                    profile.add_email(value)
        
        # Store raw metadata
        profile.raw_data['exiftool'] = {
            'file': file_path,
            'metadata': metadata
        }
        
        field_count = len([k for k in metadata.keys() if not k.startswith('SourceFile')])
        print(f"{Fore.GREEN}[✓] ExifTool extracted {field_count} metadata fields{Style.RESET_ALL}")
        logger.info(f"ExifTool complete: {field_count} fields extracted from {file_path}")
        
    except subprocess.TimeoutExpired:
        error_msg = "ExifTool timed out after 30 seconds"
        logger.error(error_msg)
        profile.add_error('exiftool', error_msg)
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse ExifTool output: {str(e)}"
        logger.error(error_msg)
        profile.add_error('exiftool', error_msg)
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")
        
    except Exception as e:
        error_msg = f"ExifTool scan failed: {str(e)}"
        logger.error(error_msg)
        profile.add_error('exiftool', str(e))
        print(f"{Fore.RED}[✗] {error_msg}{Style.RESET_ALL}")


def _extract_key_metadata(metadata: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """Extract and organize key metadata fields.
    
    Args:
        metadata: Raw metadata dictionary
        file_path: Original file path
        
    Returns:
        Organized metadata dictionary
    """
    extracted = {
        'file_name': Path(file_path).name,
        'file_path': file_path,
        'file_type': metadata.get('File:FileType', 'Unknown'),
        'mime_type': metadata.get('File:MIMEType', ''),
        'file_size': metadata.get('File:FileSize', ''),
    }
    
    # Camera/Device info
    camera_fields = ['Make', 'Model', 'Software', 'Creator', 'Author']
    for field in camera_fields:
        for key, value in metadata.items():
            if field.lower() in key.lower():
                extracted[f'device_{field.lower()}'] = value
                break
    
    # GPS coordinates
    if 'GPS:GPSLatitude' in metadata and 'GPS:GPSLongitude' in metadata:
        extracted['gps_latitude'] = metadata.get('GPS:GPSLatitude')
        extracted['gps_longitude'] = metadata.get('GPS:GPSLongitude')
        extracted['gps_location'] = f"{metadata.get('GPS:GPSLatitude')}, {metadata.get('GPS:GPSLongitude')}"
    
    # Timestamps
    timestamp_fields = [
        'CreateDate', 'ModifyDate', 'DateTimeOriginal',
        'FileModifyDate', 'FileCreateDate'
    ]
    for field in timestamp_fields:
        for key, value in metadata.items():
            if field.lower() in key.lower():
                extracted[f'timestamp_{field.lower()}'] = value
                break
    
    # Document metadata
    doc_fields = ['Title', 'Subject', 'Keywords', 'Comments', 'Company']
    for field in doc_fields:
        for key, value in metadata.items():
            if field.lower() in key.lower():
                extracted[f'document_{field.lower()}'] = value
                break
    
    # Additional interesting fields
    interesting_fields = [
        'XMP:CreatorTool', 'PDF:Producer', 'PDF:Creator',
        'EXIF:UserComment', 'ICC_Profile:ProfileDescription'
    ]
    for field in interesting_fields:
        if field in metadata:
            key = field.split(':')[1].lower() if ':' in field else field.lower()
            extracted[key] = metadata[field]
    
    return extracted


def scan(target: str, profile) -> None:
    """Wrapper for scan_file to match module interface.
    
    Args:
        target: File path to scan
        profile: Profile object to update
    """
    scan_file(target, profile)
