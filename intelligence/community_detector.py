"""
Community Detection Module.
Uses Graph Theory (Louvain Modularity) to identify clusters in the data.
"""

import networkx as nx
from typing import Dict, Any, List
from loguru import logger
from colorama import Fore, Style

try:
    import community as community_louvain
except ImportError:
    community_louvain = None

class CommunityDetector:
    """Analyzes relationship graphs to find communities."""
    
    def __init__(self):
        if not community_louvain:
            logger.warning("python-louvain not installed. Community detection disabled.")
            
    def detect_communities(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, int]:
        """Run Louvain algorithm on the graph data.
        
        Args:
            nodes: List of node dicts {'id': '...', ...}
            edges: List of edge dicts {'from': '...', 'to': '...'}
            
        Returns:
            Dict mapping node_id to community_id (int)
        """
        if not community_louvain:
            return {}
            
        print(f"{Fore.CYAN}[+] Running Community Detection (Louvain)...{Style.RESET_ALL}")
        
        # Build configuration graph
        G = nx.Graph()
        
        for node in nodes:
            G.add_node(node['id'])
            
        for edge in edges:
            G.add_edge(edge['from'], edge['to'])
            
        if G.number_of_nodes() == 0:
            return {}
            
        try:
            # Run Louvain
            # resolution=1.0 is standard. Higher = smaller communities.
            partition = community_louvain.best_partition(G)
            
            # Count communities
            num_communities = len(set(partition.values()))
            print(f"  {Fore.GREEN}└─ Detected {num_communities} distinct communities (clusters).{Style.RESET_ALL}")
            
            return partition
            
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return {}

