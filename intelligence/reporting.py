"""
Reporting Module.
Generates professional PDF reports from Intelligence Profiles.
"""
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from core.engine import Profile

class ReportGenerator:
    def __init__(self, templates_dir: str = "web/templates"):
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        
    def generate_pdf(self, profile: Profile, scan_id: str, output_path: str):
        """
        Render HTML templates and convert to PDF.
        """
        try:
            import weasyprint
        except ImportError:
            print("[!] WeasyPrint not installed. install with: pip install weasyprint")
            return False

        # Prepare Context
        context = {
            'target': profile.target_query,
            'type': profile.target_type,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'scan_id': scan_id,
            'emails': list(profile.emails),
            'phones': list(profile.phones),
            'usernames': list(profile.usernames),
            'raw_data': profile.raw_data,
            'risk_score': self._calculate_basic_risk(profile)
        }
        
        # Render HTMLs
        cover_html = self.env.get_template('report_cover.html').render(**context)
        body_html = self.env.get_template('report_body.html').render(**context)
        
        # Convert to PDF
        # We render both as separate docs then merge? Or render one combined HTML?
        # WeasyPrint can handle multi-page. We'll pass the list of HTML strings?
        # Easier: Combine them here or instantiate separate HTML objects.
        
        # We'll use a clean approach: Render them as a list of documents.
        docs = []
        docs.append(weasyprint.HTML(string=cover_html))
        docs.append(weasyprint.HTML(string=body_html))
        
        # Write to file
        all_pages = []
        for doc in docs:
            for p in doc.render().pages:
                all_pages.append(p)
                
        # Create final document structure (hacky way to merge in WeasyPrint without heavy logic)
        # Better way: Render one big HTML with page breaks.
        # Let's try combining the HTML strings with a page break.
        
        full_html = f"""
        {cover_html}
        <div style="page-break-before: always;"></div>
        {body_html}
        """
        
        weasyprint.HTML(string=full_html).write_pdf(output_path)
        return True

    def _calculate_basic_risk(self, profile: Profile) -> int:
        score = 10
        if len(profile.emails) > 0: score += 10
        if 'subdomains' in profile.raw_data:
            score += min(len(profile.raw_data['subdomains']), 20)
        # Check specific findings
        for p in profile.patterns:
            if p.get('severity') == 'high': score += 20
            elif p.get('severity') == 'medium': score += 5
            
        return min(score, 100)
