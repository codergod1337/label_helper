# tracking/deep_sort.py

from deep_sort_realtime.deepsort_tracker import DeepSort
from typing import List, Tuple
import numpy as np

class DeepSortTracker:
    def __init__(self):
        self.tracker = DeepSort(max_age=30)

    def update(self, detections: List[dict], frame: np.ndarray) -> List[dict]:
        formatted = [
            ([x1, y1, x2 - x1, y2 - y1], det["confidence"], det["label"])
            for det in detections
            for (x1, y1, x2, y2) in [det["box"]]
        ]

        tracks = self.tracker.update_tracks(formatted, frame=frame)
        output = []

        for track in tracks:
            if not track.is_confirmed():
                continue
            x1, y1, x2, y2 = map(int, track.to_ltrb())
            output.append({
                "track_id": track.track_id,
                "label": track.get_det_class(),
                "box": (x1, y1, x2, y2)
            })

        return output