# labeling/box_manager.py - Verwaltung der Box-Objekte

class BoxManager:
    def __init__(self):
        self.boxes = []  # Liste von Box-Objekten (nur Frame 0 aktuell)

    def add_box(self, box):
        self.boxes.append(box)

    def get_boxes(self):
        return self.boxes

    def clear(self):
        self.boxes = []