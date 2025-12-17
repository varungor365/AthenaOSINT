"""
Graph Exporter.
Exports network data to GraphML format for use in Maltego, Gephi, etc.
"""

from typing import Dict, List
import xml.etree.ElementTree as ET
from xml.dom import minidom

class GraphExporter:
    """Exports graph data to various formats."""
    
    def export_graphml(self, nodes: List[Dict], edges: List[Dict]) -> str:
        """Generate GraphML XML string."""
        
        # Root element
        graphml = ET.Element('graphml', {
            'xmlns': 'http://graphml.graphdrawing.org/xmlns',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xsi:schemaLocation': 'http://graphml.graphdrawing.org/xmlns http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd'
        })
        
        # Key definitions for attributes
        key_label = ET.SubElement(graphml, 'key', {'id': 'label', 'for': 'node', 'attr.name': 'label', 'attr.type': 'string'})
        key_type = ET.SubElement(graphml, 'key', {'id': 'type', 'for': 'node', 'attr.name': 'type', 'attr.type': 'string'})
        
        # Graph element
        graph = ET.SubElement(graphml, 'graph', {'id': 'G', 'edgedefault': 'directed'})
        
        # Nodes
        for node in nodes:
            n = ET.SubElement(graph, 'node', {'id': node['id']})
            
            # Data: Label
            d_label = ET.SubElement(n, 'data', {'key': 'label'})
            d_label.text = str(node.get('label', node['id']))
            
            # Data: Type
            d_type = ET.SubElement(n, 'data', {'key': 'type'})
            d_type.text = str(node.get('group', 'unknown'))
            
        # Edges
        for i, edge in enumerate(edges):
            ET.SubElement(graph, 'edge', {
                'id': f'e{i}',
                'source': edge['from'],
                'target': edge['to']
            })
            
        # Pretty print
        rough_string = ET.tostring(graphml, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
