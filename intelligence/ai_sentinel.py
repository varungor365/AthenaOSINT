"""
AI-Powered Sentinel Intelligence System.
Uses LLM for diff analysis, anomaly detection, and smart alerting.
"""
import os
import json
import difflib
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from loguru import logger


class AIIntelligenceAnalyzer:
    """
    Advanced intelligence analyzer using LLM for:
    - Smart diff analysis (understanding WHAT changed and WHY it matters)
    - Anomaly detection (identifying suspicious patterns)
    - Threat assessment (severity scoring)
    - Automated reporting
    """
    
    def __init__(self, model_url: str = None):
        self.model_url = model_url or os.getenv(
            "AGENT_ORCHESTRATOR_URL",
            "http://127.0.0.1:8081/api/generate"
        )
        self.model_name = os.getenv("AGENT_MODEL", "dolphin-llama3:8b-256k-v2.9-q5_K_M")
    
    def analyze_diff(
        self,
        old_content: str,
        new_content: str,
        url: str,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        AI-powered diff analysis that understands semantic changes.
        
        Returns:
            {
                'severity': 'critical|high|medium|low|info',
                'summary': 'Human-readable summary',
                'details': 'Detailed analysis',
                'indicators': [...list of IOCs or suspicious patterns...],
                'recommendations': [...suggested actions...],
                'threat_score': 0-100
            }
        """
        # Calculate basic diff
        diff = list(difflib.unified_diff(
            old_content.splitlines(),
            new_content.splitlines(),
            lineterm='',
            n=3
        ))
        
        if not diff:
            return {
                'severity': 'info',
                'summary': 'No changes detected',
                'details': '',
                'indicators': [],
                'recommendations': [],
                'threat_score': 0
            }
        
        # Prepare diff for LLM analysis
        diff_text = '\n'.join(diff[:100])  # Limit to first 100 lines
        
        # Build context-aware prompt
        prompt = self._build_diff_analysis_prompt(url, diff_text, old_content, new_content, context)
        
        try:
            # Call LLM for analysis
            analysis = self._query_llm(prompt, system="You are a cybersecurity analyst specializing in threat intelligence and anomaly detection.")
            
            # Parse LLM response
            result = self._parse_llm_analysis(analysis)
            result['raw_diff_lines'] = len(diff)
            result['url'] = url
            result['analyzed_at'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"AI diff analysis failed: {e}")
            # Fallback to rule-based analysis
            return self._fallback_diff_analysis(diff_text, url)
    
    def detect_anomalies(
        self,
        findings: Dict[str, Any],
        baseline: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalous patterns in scan results using LLM.
        
        Args:
            findings: Current scan findings
            baseline: Historical baseline for comparison
            
        Returns:
            Anomaly report with detected issues
        """
        prompt = f"""
Analyze these OSINT scan findings for security anomalies and suspicious patterns:

CURRENT FINDINGS:
{json.dumps(findings, indent=2, default=str)[:2000]}

{("BASELINE (Normal Activity):" + chr(10) + json.dumps(baseline, indent=2, default=str)[:1000]) if baseline else ""}

Identify:
1. Unusual email patterns or leaked credentials
2. Suspicious domain/subdomain activity
3. Breach exposure risks
4. New or unexpected data sources
5. Abnormal metadata patterns

Provide:
- Severity: critical|high|medium|low|info
- Summary: 1-2 sentence overview
- Anomalies: List of specific suspicious findings
- Recommendations: Immediate actions to take
"""
        
        try:
            analysis = self._query_llm(prompt, system="You are an expert OSINT analyst and threat hunter.")
            return self._parse_llm_analysis(analysis)
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            return {'severity': 'info', 'summary': 'Analysis unavailable', 'anomalies': []}
    
    def assess_vulnerability(self, vuln_data: Dict) -> Dict[str, Any]:
        """
        AI-powered vulnerability risk assessment.
        
        Args:
            vuln_data: Vulnerability data from Nuclei or similar scanners
            
        Returns:
            Enhanced threat assessment with context
        """
        prompt = f"""
Assess this vulnerability finding:

VULNERABILITY DATA:
{json.dumps(vuln_data, indent=2, default=str)[:1500]}

Provide:
- Risk Score: 0-100
- Exploitability: How easy is it to exploit?
- Impact: What's the worst-case scenario?
- Urgency: immediate|high|medium|low
- Remediation Steps: Specific actions to fix
- Detection Recommendations: How to detect exploitation attempts
"""
        
        try:
            analysis = self._query_llm(
                prompt,
                system="You are a penetration testing expert and vulnerability analyst."
            )
            return self._parse_llm_analysis(analysis)
        except Exception as e:
            logger.error(f"Vulnerability assessment failed: {e}")
            return {'risk_score': 50, 'urgency': 'medium'}
    
    def generate_intelligence_report(
        self,
        profile: Any,
        analysis_results: List[Dict]
    ) -> str:
        """
        Generate executive-level intelligence summary using LLM.
        
        Returns:
            Markdown-formatted intelligence report
        """
        prompt = f"""
Create an executive intelligence brief based on this OSINT investigation:

TARGET: {getattr(profile, 'target_query', 'Unknown')}

FINDINGS SUMMARY:
- Emails: {len(getattr(profile, 'emails', []))}
- Usernames: {len(getattr(profile, 'usernames', {}))}
- Domains: {len(getattr(profile, 'domains', []))}
- Breaches: {len(getattr(profile, 'breaches', []))}

ANALYSIS RESULTS:
{json.dumps(analysis_results, indent=2, default=str)[:2000]}

Generate a concise intelligence report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (bullet points)
3. Risk Assessment
4. Recommended Actions
5. Priority Timeline

Format as Markdown.
"""
        
        try:
            return self._query_llm(prompt, system="You are an intelligence analyst creating executive briefings.")
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return "# Intelligence Report\n\n*Report generation unavailable*"
    
    def _build_diff_analysis_prompt(
        self,
        url: str,
        diff_text: str,
        old_content: str,
        new_content: str,
        context: Optional[Dict]
    ) -> str:
        """Build context-aware prompt for diff analysis."""
        return f"""
Analyze this website change for security implications:

URL: {url}
CHANGE TYPE: Content modification detected

DIFF (Unified format):
```
{diff_text[:1500]}
```

OLD CONTENT (sample):
{old_content[:300]}...

NEW CONTENT (sample):
{new_content[:300]}...

{f"CONTEXT: {json.dumps(context, indent=2)}" if context else ""}

Provide:
1. Severity: critical|high|medium|low|info
2. Summary: What changed and why it matters (1 sentence)
3. Details: Technical analysis of changes
4. Indicators: List any suspicious keywords, patterns, or IOCs found
5. Recommendations: Suggested monitoring or investigation actions
6. Threat Score: 0-100 based on risk

Be specific about WHAT changed and WHY it's significant from a security perspective.
"""
    
    def _query_llm(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1024) -> str:
        """Query LLM via orchestrator API."""
        try:
            payload = {
                "prompt": prompt,
                "system": system,
                "temperature": 0.3,  # Lower temp for analytical tasks
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                self.model_url,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('success'):
                return data.get('output', '')
            else:
                raise RuntimeError(data.get('error', 'Unknown error'))
                
        except requests.exceptions.ConnectionError:
            raise RuntimeError("AI Orchestrator not available")
        except Exception as e:
            logger.error(f"LLM query failed: {e}")
            raise
    
    def _parse_llm_analysis(self, text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        # Try to extract structured data
        result = {
            'severity': 'medium',
            'summary': '',
            'details': text,
            'indicators': [],
            'recommendations': [],
            'threat_score': 50
        }
        
        lines = text.lower()
        
        # Extract severity
        if 'critical' in lines:
            result['severity'] = 'critical'
            result['threat_score'] = 90
        elif 'high' in lines:
            result['severity'] = 'high'
            result['threat_score'] = 75
        elif 'medium' in lines:
            result['severity'] = 'medium'
            result['threat_score'] = 50
        elif 'low' in lines:
            result['severity'] = 'low'
            result['threat_score'] = 25
        else:
            result['severity'] = 'info'
            result['threat_score'] = 10
        
        # Extract summary (first meaningful line)
        text_lines = text.split('\n')
        for line in text_lines:
            if len(line.strip()) > 20 and not line.strip().startswith('#'):
                result['summary'] = line.strip()[:200]
                break
        
        # Extract threat score if explicitly mentioned
        import re
        score_match = re.search(r'(?:threat|risk).*?score.*?(\d+)', lines)
        if score_match:
            result['threat_score'] = int(score_match.group(1))
        
        return result
    
    def _fallback_diff_analysis(self, diff_text: str, url: str) -> Dict[str, Any]:
        """Rule-based fallback when LLM unavailable."""
        suspicious_keywords = [
            'password', 'secret', 'api key', 'token', 'credential',
            'admin', 'root', 'exploit', 'vulnerability', 'breach',
            'malware', 'phishing', 'hack', 'inject'
        ]
        
        diff_lower = diff_text.lower()
        found_keywords = [kw for kw in suspicious_keywords if kw in diff_lower]
        
        severity = 'high' if found_keywords else 'medium'
        threat_score = min(len(found_keywords) * 20, 100)
        
        return {
            'severity': severity,
            'summary': f"Change detected at {url}" + (f" (found: {', '.join(found_keywords)})" if found_keywords else ""),
            'details': f"Diff contains {len(diff_text.splitlines())} changed lines",
            'indicators': found_keywords,
            'recommendations': ['Review changes manually', 'Check for unauthorized modifications'],
            'threat_score': threat_score,
            'url': url,
            'analyzed_at': datetime.now().isoformat()
        }


# Global analyzer instance
_global_analyzer = None

def get_ai_analyzer() -> AIIntelligenceAnalyzer:
    """Get or create global AI analyzer instance."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = AIIntelligenceAnalyzer()
    return _global_analyzer
