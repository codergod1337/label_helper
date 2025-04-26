# labeling/label_drawer.py - Hauptprogramm

import sys
import os
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QComboBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect, QPoint, QTimer

from labeling.models import Box
from labeling.label_manager import LabelManager
from labeling.selection_manager import SelectionManager

# Basisfarben pro Label
LABEL_COLORS = {
    "person": QColor(0, 200, 0),
    "car": QColor(0, 0, 255),
    "truck": QColor(200, 0, 0),
    "bus": QColor(255, 165, 0),
}

def calculate_color(base_color, shape_id):
    variation = (shape_id * 30) % 60
    r = min(base_color.red() + variation, 255)
    g = min(base_color.green() + variation, 255)
    b = min(base_color.blue() + variation, 255)
    return (r, g, b)

class LabelDrawer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BoundingBox Drawer")
        self.setGeometry(100, 100, 800, 600)

        self.label_manager = LabelManager()
        self.selection_manager = SelectionManager()

        # UI State
        self.labels = list(LABEL_COLORS.keys())
        self.start_pos = None
        self.current_label = self.labels[0]
        self.id_counter = {label: 0 for label in self.labels}
        self.current_frame = 0

        # UI Elemente
        self.label_dropdown = QComboBox()
        self.label_dropdown.addItems(self.labels)
        self.label_dropdown.currentIndexChanged.connect(self.change_label)

        # der save button
        #self.save_button = QPushButton("Speichern")
        #self.save_button.clicked.connect(self.save_project)

        self.canvas = Canvas(self)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.label_dropdown)
        #button_layout.addWidget(self.save_button) savebutton einblenden - nicht

        layout = QVBoxLayout()
        layout.addLayout(button_layout)
        layout.addWidget(self.canvas)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def change_label(self, index):
        self.current_label = self.labels[index]

    def get_next_id(self, label):
        self.id_counter[label] += 1
        return self.id_counter[label]

    def save_project(self):
        output_dir = os.path.join(os.getcwd(), "data", "output")
        os.makedirs(output_dir, exist_ok=True)
        self.label_manager.save_project(os.path.join(output_dir, "boundings.json"))
        self.statusBar().showMessage(f"✅ Projekt gespeichert unter {output_dir}")

class Canvas(QLabel):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

        # Resize Corner BLink!
        self.blink_timer = QTimer()
        self.blink_state = True
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_interval_ms = 100  # alle 100ms togglen

        self.setStyleSheet("background-color: #aaaaaa;")
        self.setMouseTracking(True)

    def toggle_blink(self):
        self.blink_state = not self.blink_state
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            frame_pos = self.map_to_frame_coordinates(event.pos())

            # Prüfen: Hover über Resize-Corner?
            if self.parent.selection_manager.hovered_corner_index is not None:
                # → Resize starten
                shape = self.parent.selection_manager.hovered_shape
                corner = self.parent.selection_manager.hovered_corner_index
                self.parent.selection_manager.start_resizing(shape, corner, frame_pos)
                self.blink_timer.start(self.blink_interval_ms)  # <<< blinken starten
                return

            # Prüfen: Hover über Border?
            hit_shape = self.parent.label_manager.find_shape_border_hit(self.parent.current_frame, frame_pos)
            if hit_shape:
                # → Move starten
                self.setCursor(Qt.ClosedHandCursor)  # <<< CURSOR ÄNDERN
                self.parent.selection_manager.select_shape(hit_shape, frame_pos)
                return

            # Sonst: Neue Box aufziehen starten
            self.parent.start_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent.selection_manager.resizing:
                self.parent.selection_manager.stop_resizing()
                self.blink_timer.stop()  # <<< Timer stoppen
                self.blink_state = True  # <<< wieder sichtbar machen
                self.update()
                return

            if self.parent.selection_manager.moving:
                self.parent.selection_manager.clear_selection()
                self.setCursor(Qt.ArrowCursor)  # <<< CURSOR ZURÜCK
                self.update()
                return

            if self.parent.start_pos:
                end_pos = event.pos()
                rect = QRect(self.parent.start_pos, end_pos).normalized()

                label = self.parent.current_label  # aktuell ausgewähltes Label
                base_color = self.parent.label_manager.get_label_color(label)
                new_id = self.parent.label_manager.get_next_id_for_label(label)

                box = Box(rect, label, new_id, (base_color.red(), base_color.green(), base_color.blue()))
                self.parent.label_manager.add_shape(self.parent.current_frame, box)

                self.parent.start_pos = None
                self.update()

    def check_hovered_corner(self, pos, tolerance=10):
        shapes = self.parent.label_manager.get_shapes(self.parent.current_frame)
        for shape in shapes:
            for idx, corner in enumerate(shape.get_corner_points()):
                if (corner - pos).manhattanLength() <= tolerance:
                    return idx
        return None      

    def map_to_frame_coordinates(self, pos):
        return pos  # aktuell direkte 1:1 Zuordnung, später zoombereit machen

    def mouseMoveEvent(self, event):
        frame_pos = self.map_to_frame_coordinates(event.pos())

        if self.parent.selection_manager.resizing:
            self.parent.selection_manager.move_resize(event.pos())
            self.update()
            return

        if self.parent.selection_manager.moving:
            self.parent.selection_manager.move_active_shape(event.pos())
            self.update()
            return

        # Hover-Detection
        hit_shape = self.parent.label_manager.find_shape_border_hit(self.parent.current_frame, frame_pos)
        self.parent.selection_manager.hovered_shape = hit_shape

        # Hover-Corner-Detection
        corner_hit = self.check_hovered_corner(frame_pos)
        self.parent.selection_manager.set_hovered_corner(corner_hit)

        self.update()
        self.parent.statusBar().showMessage(f"X: {event.x()} | Y: {event.y()}")

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        shapes = self.parent.label_manager.get_shapes(self.parent.current_frame)
        for shape in shapes:
            active = self.parent.selection_manager.is_shape_active(shape)
            hovered = self.parent.selection_manager.is_shape_hovered(shape)
            shape.draw(painter, active=active, hovered=hovered)

            if active or hovered:
                corner_points = shape.get_corner_points()
                for idx, point in enumerate(corner_points):
                    if idx == self.parent.selection_manager.hovered_corner_index and self.parent.selection_manager.resizing:
                        # Blinkeffekt
                        if self.blink_state:
                            painter.setBrush(QColor(0, 0, 0))
                        else:
                            painter.setBrush(QColor(255, 255, 255))
                    else:
                        painter.setBrush(QColor(0, 0, 0))

                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(point, 5, 5)

        if self.parent.start_pos:
            mouse_pos = self.mapFromGlobal(self.cursor().pos())
            rect = QRect(self.parent.start_pos, mouse_pos).normalized()
            pen = QPen(QColor(128, 128, 128), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    # gehört das hier her^^ ?
    def map_to_frame_coordinates(self, pos):
        return pos

def main():
    app = QApplication(sys.argv)
    window = LabelDrawer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()