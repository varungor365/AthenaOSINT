"""
Graph Engine.
Transforms OSINT Profile data into a Node-Link structure for visualization.
"""
from typing import Dict, List, Any
from core.engine import Profile

class GraphBuilder:
    def __init__(self, profile: Profile):
        self.profile = profile
        self.nodes = []
        self.edges = []
        self.node_ids = set()

    def _add_node(self, node_id: str, label: str, group: str, title: str = ""):
        if node_id in self.node_ids:
            return
        self.node_ids.add(node_id)
        
        # Color/Shape mapping based on group
        color_map = {
            'target': '#FF5733', # Red/Orange
            'email': '#33FF57',  # Green
            'phone': '#3357FF',  # Blue
            'domain': '#FF33F6', # Pink
            'ip': '#33FFF6',     # Cyan
            'username': '#F6FF33', # Yellow
            'social': '#8B33FF', # Purple
            'vuln': '#FF0000',   # Bright Red
            'finding': '#AAAAAA' # Grey
        }
        
        self.nodes.append({
            'id': node_id,
            'label': label,
            'group': group,
            'title': title or label, # Tooltip
            'color': color_map.get(group, '#97C2FC')
        })

    def _add_edge(self, source: str, target: str, label: str = ""):
        if source not in self.node_ids or target not in self.node_ids:
            return # Ensure nodes exist
            
        self.edges.append({
            'from': source,
            'to': target,
            'label': label,
            'arrows': 'to'
        })

    def build(self) -> Dict[str, Any]:
        """Construct the graph JSON."""
        # 1. Root Node (The Target)
        root_id = "root"
        self._add_node(root_id, self.profile.target_query, 'target', f"Type: {self.profile.target_type}")

        # 2. Emails
        for email in self.profile.emails:
            self._add_node(email, email, 'email')
            self._add_edge(root_id, email, 'found')
            
        # 3. Phones
        for phone in self.profile.phones:
            self._add_node(phone, phone, 'phone')
            self._add_edge(root_id, phone, 'found')
            
        # 4. Usernames
        for user in self.profile.usernames:
            self._add_node(user, user, 'username')
            self._add_edge(root_id, user, 'found')
        
        # 5. Raw Data Parsing (Generic)
        # This is where we extract things from the 'raw_data' dictionary populated by modules
        raw = self.profile.raw_data
        
        # Subdomains (from Amass, Subfinder, BBOT, etc)
        if 'subdomains' in raw:
            for sub in raw['subdomains']:
                self._add_node(sub, sub, 'domain')
                self._add_edge(root_id, sub, 'subdomain')
                
        # IP Addresses (from resolving subs or simple scans)
        if 'ips' in raw:
            for ip in raw['ips']:
                self._add_node(ip, ip, 'ip')
                self._add_edge(root_id, ip, 'resolves')
                
        # Social Links (from WebSift, Sherlock)
        if 'social_accounts' in raw:
            for acc in raw['social_accounts']:
                # acc might be dict or string
                url = acc if isinstance(acc, str) else acc.get('url', str(acc))
                site = acc.get('site', 'Social') if isinstance(acc, dict) else 'Social'
                node_id = f"social_{hash(url)}"
                self._add_node(node_id, site, 'social', title=url)
                self._add_edge(root_id, node_id, 'profile')

        # Vulnerabilities / Findings
        # We might want to link finding summaries
        # ... checking profile structure ...
        
        return {
            'nodes': self.nodes,
            'edges': self.edges
        }
