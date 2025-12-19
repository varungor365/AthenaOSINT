"""
Breach Processor Module
----------------------
Handles the ingestion, cleaning, sorting, and deduplication of credential combo lists (User:Pass).
Equivalent to 'Comboutils' features designed for data processing and analysis.
"""

import re
import os
from pathlib import Path
from typing import List, Tuple, Dict, Set
from loguru import logger

class BreachProcessor:
    """Processor for credential combo lists."""
    
    def __init__(self):
        self.common_separators = [':', ';', '|', ',']
        # Regex for basic email validation
        self.email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
    def detect_separator(self, line: str) -> str:
        """Detect the most likely separator in a line."""
        counts = {sep: line.count(sep) for sep in self.common_separators}
        # Return separator with max count, defaulting to ':'
        best_sep = max(counts, key=counts.get)
        if counts[best_sep] == 0:
            return ':'
        return best_sep

    def parse_line(self, line: str) -> Tuple[str, str]:
        """Parse a single line into (username/email, password)."""
        line = line.strip()
        if not line:
            return None, None
            
        sep = self.detect_separator(line)
        parts = line.split(sep, 1) # Split only on first occurrence
        
        if len(parts) == 2:
            return parts[0].strip(), parts[1].strip()
        return None, None

    def clean_combos(self, input_file: Path, output_file: Path) -> Dict[str, int]:
        """
        Clean a combo list file.
        - Removes duplicates
        - specific format enforcement (User:Pass)
        - Removes lines with no password or invalid format
        """
        stats = {
            'total_lines': 0,
            'valid_combos': 0,
            'duplicates_removed': 0,
            'invalid_format': 0
        }
        
        seen_combos: Set[str] = set()
        
        try:
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f_in, \
                 open(output_file, 'w', encoding='utf-8') as f_out:
                
                for line in f_in:
                    stats['total_lines'] += 1
                    user, password = self.parse_line(line)
                    
                    if user and password:
                        combo_str = f"{user}:{password}"
                        
                        if combo_str in seen_combos:
                            stats['duplicates_removed'] += 1
                        else:
                            seen_combos.add(combo_str)
                            f_out.write(f"{combo_str}\n")
                            stats['valid_combos'] += 1
                    else:
                        stats['invalid_format'] += 1
                        
            logger.info(f"Cleaned {input_file}: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to clean combos: {e}")
            return stats

    def sort_combos(self, input_file: Path, output_file: Path, sort_by: str = 'domain') -> bool:
        """
        Sort combo list.
        sort_by: 'domain' (email domain), 'length' (password length), 'alpha' (alphabetical user)
        """
        try:
            # For very large files, this should be done with external sort or chunking.
            # Assuming memory fits for typical use case, or we use chunking later.
            lines = []
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            if sort_by == 'domain':
                # Sort by domain part of email (if user is email), else alpha
                def domain_key(line):
                    parts = line.split(':', 1)
                    user = parts[0]
                    if '@' in user:
                        return user.split('@')[-1]
                    return user
                lines.sort(key=domain_key)
                
            elif sort_by == 'length':
                # Sort by password length (descending)
                def length_key(line):
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        return len(parts[1])
                    return 0
                lines.sort(key=length_key, reverse=True)
                
            else: # alpha
                lines.sort()
                
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
                
            logger.info(f"Sorted {input_file} by {sort_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sort combos: {e}")
            return False

    def categorize_by_domain(self, input_file: Path, output_dir: Path) -> Dict[str, int]:
        """Split combos into separate files based on email domain."""
        domain_files = {}
        counts = {}
        
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    user, pwd = self.parse_line(line)
                    if user and '@' in user:
                        domain = user.split('@')[-1].lower()
                        
                        # Group small domains or distinct ones? 
                        # Let's clean the domain string to be safe filename
                        safe_domain = re.sub(r'[^a-zA-Z0-9.-]', '_', domain)
                        
                        if safe_domain not in domain_files:
                            domain_files[safe_domain] = open(output_dir / f"{safe_domain}.txt", 'a', encoding='utf-8')
                            counts[safe_domain] = 0
                            
                        domain_files[safe_domain].write(f"{user}:{pwd}\n")
                        counts[safe_domain] += 1
            
            # Close all handles
            for fh in domain_files.values():
                fh.close()
                
            return counts
            
        except Exception as e:
            logger.error(f"Failed to categorize: {e}")
            return counts

