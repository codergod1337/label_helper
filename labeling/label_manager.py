# labeling/label_manager.py - Frames & Shapes Verwaltung

import json
import os
from labeling.models import Box

class LabelManager:
    def __init__(self):
        self.frames = {}  # frame_index -> List[Shapes]

    def add_shape(self, frame_index: int, shape):
        if frame_index not in self.frames:
            self.frames[frame_index] = []
        self.frames[frame_index].append(shape)

    def get_shapes(self, frame_index: int):
        return self.frames.get(frame_index, [])

    def clear(self):
        self.frames = {}

    def save_project(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        frames_data = []
        for frame_idx, shapes in self.frames.items():
            frames_data.append({
                "frame_index": frame_idx,
                "shapes": [shape.to_dict() for shape in shapes]
            })

        with open(path, "w") as f:
            json.dump({"frames": frames_data}, f, indent=4)

    def find_shape_border_hit(self, frame_index: int, pos, tolerance=5):
        shapes = self.get_shapes(frame_index)
        for shape in shapes:
            if hasattr(shape, "is_point_near_border") and shape.is_point_near_border(pos, tolerance):
                return shape
        return None



    def load_project(self, path: str):
        if not os.path.exists(path):
            return

        self.clear()

        with open(path, "r") as f:
            data = json.load(f)

        for frame in data["frames"]:
            frame_idx = frame["frame_index"]
            self.frames[frame_idx] = []
            for shape_data in frame["shapes"]:
                if shape_data["type"] == "box":
                    self.frames[frame_idx].append(Box.from_dict(shape_data))
                # später: elif für circle / polygon