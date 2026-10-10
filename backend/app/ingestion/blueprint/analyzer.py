"""
Analyzer for blueprints and technical drawings.
Extracts networks, annotations, and pipes from images and PDFs.
"""

import os
import re
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False

@dataclass
class SewerNetwork:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    
@dataclass
class DrainageNetwork:
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class BlueprintAnalyzer:
    def __init__(self):
        self.correction_log = []

    def _render_pdf(self, file_path: str) -> Any:
        # Requires pdf2image or PyMuPDF, skipping implementation for briefness.
        # Fallback to PIL if it's an image.
        if PIL_AVAILABLE:
            return Image.open(file_path)
        return None

    def _detect_lines(self, image_np: Any) -> List[Any]:
        if not CV2_AVAILABLE:
            return []
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=50, maxLineGap=10)
        return lines if lines is not None else []

    def _extract_text(self, image_np: Any) -> str:
        if not TESSERACT_AVAILABLE:
            return ""
        return pytesseract.image_to_string(image_np)

    def _parse_labels(self, text: str) -> Dict[str, List[str]]:
        diameters = re.findall(r'(?:DN|Ø)?\s*(\d{2,4})\s*(?:mm)?', text)
        slopes = re.findall(r'(?:1:\d+|\d+(?:\.\d+)?%)', text)
        materials = re.findall(r'(PVC|RC|HDPE|DI|CI)', text, re.IGNORECASE)
        return {
            "diameters": diameters,
            "slopes": slopes,
            "materials": materials
        }

    def _build_network(self, lines: List[Any], labels: Dict[str, List[str]]) -> Any:
        if not NX_AVAILABLE:
            return None
        G = nx.Graph()
        # Simplified node/edge building
        for i, line in enumerate(lines):
            x1, y1, x2, y2 = line[0]
            node1, node2 = (x1, y1), (x2, y2)
            G.add_edge(node1, node2, id=i)
            
        # Assign attributes (simplified)
        for i, (u, v, data) in enumerate(G.edges(data=True)):
            if i < len(labels['diameters']):
                data['diameter'] = labels['diameters'][i]
            if i < len(labels['materials']):
                data['material'] = labels['materials'][i]
        return G

    def analyze_sewer_blueprint(self, image_path: str) -> SewerNetwork:
        if not CV2_AVAILABLE:
            logger.error("OpenCV not available")
            return SewerNetwork([], [])
            
        img = cv2.imread(image_path)
        if img is None:
            return SewerNetwork([], [])
            
        lines = self._detect_lines(img)
        text = self._extract_text(img)
        labels = self._parse_labels(text)
        
        G = self._build_network(lines, labels)
        
        nodes = [{"id": n, "pos": n} for n in G.nodes()] if G else []
        edges = [{"source": u, "target": v, **d} for u, v, d in G.edges(data=True)] if G else []
        
        return SewerNetwork(nodes=nodes, edges=edges)

    def analyze_drainage_blueprint(self, image_path: str) -> DrainageNetwork:
        sewer = self.analyze_sewer_blueprint(image_path)
        return DrainageNetwork(nodes=sewer.nodes, edges=sewer.edges)

    def blueprint_diff(self, old_network: Any, new_network: Any) -> Dict[str, Any]:
        # Compare two extracted networks
        added = len(new_network.edges) - len(old_network.edges)
        return {
            "added_edges": max(0, added),
            "removed_edges": max(0, -added)
        }

    def log_correction(self, element_id: str, old_val: Any, new_val: Any, user: str):
        self.correction_log.append({
            "element": element_id,
            "old": old_val,
            "new": new_val,
            "user": user
        })
