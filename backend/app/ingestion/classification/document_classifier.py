"""
Document Classifier to determine the nature of ingested files.
"""

import os
import mimetypes
from dataclasses import dataclass
from typing import List, Optional

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

@dataclass
class DocumentClassification:
    doc_type: str
    confidence: float
    detected_keywords: List[str]

class DocumentClassifier:
    
    def __init__(self):
        self.keywords = {
            "BLUEPRINT": ["sewer", "drainage", "pipe", "dn", "diameter", "manhole", "elevation"],
            "REPORT": ["summary", "analysis", "survey", "traffic"],
        }
        
    def classify(self, file_path: str) -> DocumentClassification:
        ext = os.path.splitext(file_path)[1].lower()
        mime_type, _ = mimetypes.guess_type(file_path)
        
        doc_type = "UNKNOWN"
        confidence = 0.1
        found_keywords = []
        
        # Extension-based rules
        if ext in ['.tif', '.tiff']:
            doc_type = "SATELLITE/TERRAIN"
            confidence = 0.8
        elif ext in ['.shp', '.geojson', '.kml', '.kmz']:
            doc_type = "MAP"
            confidence = 0.9
        elif ext in ['.csv']:
            # Assume CSV might be generic data
            doc_type = "TABULAR"
            confidence = 0.6
        elif ext in ['.pdf', '.png', '.jpg', '.jpeg']:
            # Content-based heuristics
            text = ""
            if ext == '.pdf':
                doc_type = "BLUEPRINT" # Defaulting for PDF
                confidence = 0.5
            elif OCR_AVAILABLE:
                try:
                    img = Image.open(file_path)
                    text = pytesseract.image_to_string(img).lower()
                    
                    for cat, words in self.keywords.items():
                        matches = [w for w in words if w in text]
                        if matches:
                            doc_type = cat
                            confidence = 0.5 + (0.1 * min(len(matches), 5))
                            found_keywords.extend(matches)
                            break
                    else:
                        doc_type = "IMAGE"
                        confidence = 0.7
                except Exception:
                    pass
                    
        return DocumentClassification(
            doc_type=doc_type,
            confidence=min(confidence, 1.0),
            detected_keywords=list(set(found_keywords))
        )
