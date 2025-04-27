# labeling/label_manager.py - Frames & Shapes Verwaltung

import json
import os
from labeling.models import Box
from PyQt5.QtGui import QColor

class LabelManager:
    def __init__(self):
        self.frames = {}  # frame_index -> List[Shapes]
        self.label_colors = {}  # {label: QColor}
        self.label_counters = {}  # {label: int}

    def add_shape(self, frame_index: int, shape):
        if frame_index not in self.frames:
            self.frames[frame_index] = []
        self.frames[frame_index].append(shape)

    def get_shapes(self, frame_index: int):
        return self.frames.get(frame_index, [])

    def get_label_color(self, label):
        if label not in self.label_colors:
            # Erzeuge eine neue zufällige Farbe wenn Label neu ist
            import random
            color = QColor(random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
            self.label_colors[label] = color
        return self.label_colors[label]

    def get_next_id_for_label(self, label):
        if label not in self.label_counters:
            self.label_counters[label] = 1
        else:
            self.label_counters[label] += 1
        return self.label_counters[label]


    def clear(self):
        self.frames = {}


    def save_project(self, path="data/output/project.json"):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        frames_data = []
        for frame_idx, shapes in self.frames.items():
            frames_data.append({
                "frame_index": frame_idx,
                "shapes": [shape.to_dict() for shape in shapes]
            })

        save_data = {
            "frames": frames_data,
            "counters": self.label_counters  # <<< einfach dumpen
        }

        with open(path, "w") as f:
            json.dump(save_data, f, indent=4)

    def load_project(self, path="data/output/project.json"):
        if not os.path.exists(path):
            print(f"ℹ️ Keine Projektdatei gefunden unter {path}. Starte leer.")
            return

        with open(path, "r") as f:
            data = json.load(f)

        self.frames.clear()
        self.label_counters.clear()

        for frame_data in data.get("frames", []):
            frame_idx = frame_data["frame_index"]
            shapes = []
            for shape_data in frame_data["shapes"]:
                if shape_data.get("type") == "box":
                    shape = Box.from_dict(shape_data)
                    shapes.append(shape)

            self.frames[frame_idx] = shapes

        # Counters wiederherstellen
        self.label_counters.update(data.get("counters", {}))

        print(f"✅ Projekt geladen aus {path}")


    def find_shape_border_hit(self, frame_index: int, pos, tolerance=5):
        shapes = self.get_shapes(frame_index)
        for shape in shapes:
            if hasattr(shape, "is_point_near_border") and shape.is_point_near_border(pos, tolerance):
                return shape
        return None
    
    def delete_shape(self, frame_idx, shape):
        if frame_idx not in self.frames:
            return

        if shape in self.frames[frame_idx]:
            self.frames[frame_idx].remove(shape)



