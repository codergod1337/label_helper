# labeling/label_drawer.py - Hauptprogramm

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QComboBox, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
)
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect, QPoint

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
        self.setStyleSheet("background-color: #EEEEEE;")
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.map_to_frame_coordinates(event.pos())  # hier Position anpassen
            hit_shape = self.parent.label_manager.find_shape_border_hit(self.parent.current_frame, pos)

            if hit_shape:
                self.parent.selection_manager.select_shape(hit_shape, pos)
                self.update()
            else:
                self.parent.start_pos = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.parent.selection_manager.moving:
                # Verschiebemodus beenden
                self.parent.selection_manager.clear_selection()

                # Projekt sofort speichern nach Drop
                output_dir = os.path.join(os.getcwd(), "data", "output")
                os.makedirs(output_dir, exist_ok=True)
                self.parent.label_manager.save_project(os.path.join(output_dir, "boundings.json"))
                self.parent.statusBar().showMessage(f"✅ Box verschoben und gespeichert auf Frame {self.parent.current_frame}")

                self.update()

            elif self.parent.start_pos:
                end_pos = event.pos()
                rect = QRect(self.parent.start_pos, end_pos).normalized()

                base_color = LABEL_COLORS.get(self.parent.current_label, QColor(128, 128, 128))
                shape_id = self.parent.get_next_id(self.parent.current_label)
                final_color = calculate_color(base_color, shape_id)

                box = Box(rect, self.parent.current_label, shape_id, final_color)
                self.parent.label_manager.add_shape(self.parent.current_frame, box)

                # Sofort speichern
                output_dir = os.path.join(os.getcwd(), "data", "output")
                os.makedirs(output_dir, exist_ok=True)
                self.parent.label_manager.save_project(os.path.join(output_dir, "boundings.json"))
                self.parent.statusBar().showMessage(f"✅ Box gespeichert auf Frame {self.parent.current_frame}")

                self.parent.start_pos = None
                self.update()

      

    def map_to_frame_coordinates(self, pos):
        return pos  # aktuell direkte 1:1 Zuordnung, später zoombereit machen

    def mouseMoveEvent(self, event):
        frame_pos = self.map_to_frame_coordinates(event.pos())

        if self.parent.selection_manager.moving:
            self.parent.selection_manager.move_active_shape(event.pos())
            self.update()
        #elif self.parent.start_pos:
        #    self.update()
        else:
        # Hover-Highlight prüfen
            hovered_shape = self.parent.label_manager.find_shape_border_hit(self.parent.current_frame, frame_pos)
            self.parent.selection_manager.set_hovered_shape(hovered_shape)
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

        if self.parent.start_pos:
            mouse_pos = self.mapFromGlobal(self.cursor().pos())
            rect = QRect(self.parent.start_pos, mouse_pos).normalized()
            pen = QPen(QColor(128, 128, 128), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(rect)

def main():
    app = QApplication(sys.argv)
    window = LabelDrawer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()