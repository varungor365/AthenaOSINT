"""
Graph Exporter Module.
Exports intelligence graph to GraphML format (compatible with Maltego/Gephi).
"""
from loguru import logger
from core.engine import Profile
import networkx as nx
from pathlib import Path

# Metadata
META = {
    'name': 'graph_exporter',
    'description': 'Export Intelligence to GraphML',
    'category': 'Utils',
    'risk': 'safe', 
    'emoji': '📊'
}

def scan(target: str, profile: Profile):
    """
    This isn't a scanning module per se, but runs at the end to export data.
    """
    logger.info("[GraphExporter] Generating GraphML export...")
    
    G = nx.Graph()
    
    # Add Central Node
    G.add_node(target, type='Target')
    
    # Add Emails
    for email in profile.emails:
        G.add_node(email, type='Email')
        G.add_edge(target, email)
        
    # Add Phones
    for phone in profile.phones:
        G.add_node(phone, type='Phone')
        G.add_edge(target, phone)
        
    # Add Domains
    for domain in profile.domains:
        G.add_node(domain, type='Domain')
        G.add_edge(target, domain)
        
    # Add Usernames
    for user in profile.usernames:
        G.add_node(user, type='Username')
        G.add_edge(target, user)
        
    # Export
    try:
        from config import get_config
        reports_dir = get_config().get('REPORTS_DIR')
        filename = f"{target.replace('/','_')}_graph.graphml"
        path = reports_dir / filename
        
        nx.write_graphml(G, str(path))
        logger.success(f"[GraphExporter] Exported to {path}")
        profile.add_metadata({'graph_export': str(path)})
        
    except Exception as e:
        logger.error(f"[GraphExporter] Export failed: {e}")
