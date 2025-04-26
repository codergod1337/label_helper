# detection/yolo8_wrapper.py

from ultralytics import YOLO
from typing import List, Tuple
import numpy as np

class YOLOv8Detector:
    def __init__(self, model_path: str = "yolov8n.pt", conf_thresh: float = 0.5):
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh

    def detect(self, frame: np.ndarray) -> List[dict]:
        results = self.model.predict(frame, verbose=False)
        detections = []

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                label = self.model.names[int(box.cls[0])]
                if conf >= self.conf_thresh:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detections.append({
                        "label": label,
                        "confidence": conf,
                        "box": (x1, y1, x2, y2)
                    })

        return detections