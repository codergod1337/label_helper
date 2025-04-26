# labeling/annotation.py

from dataclasses import dataclass
from typing import Tuple

@dataclass
class Annotation:
    video_id: int
    frame: int
    label: str
    box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    source: str                     # 'manual' oder 'yolo'
    track_id: int | None = None     # falls vorhanden
    annotation_id: int | None = None  # eigene feste ID (global)