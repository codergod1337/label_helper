# labeling/models.py - Shape-Definitionen (Box aktiv, andere vorbereitet)

from PyQt5.QtCore import QRect, QPoint, Qt
from PyQt5.QtGui import QColor, QPainter, QPen

class Shape:
    def __init__(self, label: str, shape_id: int, color: tuple):
        self.label = label
        self.shape_id = shape_id
        self.color = QColor(*color)  # erwartet (r, g, b)

    def draw(self, painter: QPainter):
        raise NotImplementedError

    def to_dict(self):
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data):
        raise NotImplementedError

class Box(Shape):
    def __init__(self, rect: QRect, label: str, shape_id: int, color: tuple):
        super().__init__(label, shape_id, color)
        self.rect = rect

    def draw(self, painter: QPainter, active=False, hovered=False):
        if active:
            # Aktiv → gestrichelt und halbtransparent rot
            pen = QPen(QColor(255, 0, 0, 180))
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
        elif hovered:
            # Hover → orange gestrichelt
            pen = QPen(QColor(255, 165, 0, 180))  # Orange Hover
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)    
        else:
            pen = QPen(self.color, 2)
            painter.setPen(pen)

        painter.drawRect(self.rect)

        if not active:
            painter.drawText(self.rect.topLeft() + QPoint(5, -5), f"{self.label} #{self.shape_id}")

    # nach hover -> scale points
    def get_corner_points(self):
        rect = self.rect
        return [
            rect.topLeft(),
            rect.topRight(),
            rect.bottomLeft(),
            rect.bottomRight()
        ]


    def is_point_near_border(self, point, tolerance=5):
        rect = self.rect
        near_left = abs(point.x() - rect.left()) <= tolerance
        near_right = abs(point.x() - rect.right()) <= tolerance
        near_top = abs(point.y() - rect.top()) <= tolerance
        near_bottom = abs(point.y() - rect.bottom()) <= tolerance
        inside_x = rect.left() <= point.x() <= rect.right()
        inside_y = rect.top() <= point.y() <= rect.bottom()
        return ((near_left or near_right) and inside_y) or ((near_top or near_bottom) and inside_x)

    def to_dict(self):
        return {
            "type": "box",
            "label": self.label,
            "id": self.shape_id,
            "color": [self.color.red(), self.color.green(), self.color.blue()],
            "x1": self.rect.left(),
            "y1": self.rect.top(),
            "x2": self.rect.right(),
            "y2": self.rect.bottom()
        }

    @classmethod
    def from_dict(cls, data):
        rect = QRect(data["x1"], data["y1"], data["x2"] - data["x1"], data["y2"] - data["y1"])
        color = tuple(data["color"])
        return cls(rect, data["label"], data["id"], color)

class Circle(Shape):
    pass  # Vorbereitung für später

class Polygon(Shape):
    pass  # Vorbereitung für später