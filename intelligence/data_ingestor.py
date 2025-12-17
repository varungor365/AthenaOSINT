"""
Data Ingestor.
Parses raw files (SQL, TXT, CSV, XLSX) to extract intelligence.
"""

import re
import os
import pandas as pd
from typing import List, Dict
from colorama import Fore
from logic.verifier import Verifier # Stub for specific validation if needed (not created yet, using regex for now)

# Regex Patterns
PATTERNS = {
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'phone': r'\+?[\d\s-]{10,15}', # Simple international check
    'hash_md5': r'\b[a-fA-F0-9]{32}\b',
    # 'ip': ...
}

class DataIngestor:
    """Parses files and extracts entities."""
    
    def process_file(self, file_path: str) -> List[Dict]:
        """Determine file type and extract data."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.txt' or ext == '.sql' or ext == '.dump':
            return self._process_text(file_path)
        elif ext == '.csv':
            return self._process_csv(file_path)
        elif ext == '.xlsx' or ext == '.xls':
            return self._process_excel(file_path)
        else:
            return []

    def _extract_from_text(self, text: str, source: str) -> List[Dict]:
        """Run regex on text blob."""
        results = []
        for p_type, pattern in PATTERNS.items():
            matches = re.finditer(pattern, text)
            for m in matches:
                val = m.group(0)
                # Basic validation
                if len(val) > 3:
                     results.append({
                         'type': p_type,
                         'value': val,
                         'context': text[:100].strip(), # First 100 chars as context for now? Ideally line context.
                         'source': source
                     })
        return results

    def _process_text(self, file_path: str) -> List[Dict]:
        """Process line by line to save memory."""
        extracted = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content_sample = ""
                line_count = 0
                
                for line in f:
                    line_count += 1
                    # Quick check for speed
                    if '@' in line or len(line) > 20: 
                        found = self._extract_from_text(line, os.path.basename(file_path))
                        if found:
                            for item in found:
                                item['context'] = line.strip()
                            extracted.extend(found)
                    
                    # Accumulate sample for AI check if regex is finding nothing
                    if line_count < 20:
                        content_sample += line
                        
                # AI Fallback: If we read lines but found NOTHING via regex, maybe it's weirdly formatted?
                if not extracted and line_count > 0:
                    from intelligence.llm import LLMClient
                    try:
                        llm = LLMClient()
                        prompt = f"Extract any emails, usernames, or passwords from this unstructured text. Return specific entities only. Text:\n{content_sample}"
                        ai_result = llm.generate_text(prompt, max_tokens=200)
                        if "email" in ai_result.lower() or "@" in ai_result:
                            # If AI sees something, we might want to flag this file for manual review or smarter parsing
                            # For now, just logging it as a finding of type 'ai_hint'
                            extracted.append({
                                'type': 'ai_hint',
                                'value': 'Manual Review Recommended',
                                'context': f"AI detected potential data in {file_path}",
                                'source': os.path.basename(file_path)
                            })
                    except:
                        pass
                        
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return extracted

    def _process_csv(self, file_path: str) -> List[Dict]:
        extracted = []
        try:
            # Chunk processing for large CSVs
            for chunk in pd.read_csv(file_path, chunksize=5000):
                # Convert chunk to string blob or iterate columns
                # Iterating assumes finding emails in any column
                blob = chunk.to_string()
                found = self._extract_from_text(blob, os.path.basename(file_path))
                extracted.extend(found)
        except Exception as e:
            print(f"Error reading CSV {file_path}: {e}")
        return extracted

    def _process_excel(self, file_path: str) -> List[Dict]:
        extracted = []
        try:
            df = pd.read_excel(file_path)
            blob = df.to_string()
            found = self._extract_from_text(blob, os.path.basename(file_path))
            extracted.extend(found)
        except Exception as e:
            print(f"Error reading Excel {file_path}: {e}")
        return extracted
