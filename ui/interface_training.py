# ui/interface_training.py

import sys
import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QComboBox, QCheckBox, QStatusBar
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QKeyEvent
from PyQt5.QtCore import Qt, QPoint, QRect

from config import MANUAL_LABEL_OPTIONS
from labeling.label_manager import LabelManager
from labeling.annotation import Annotation
from detection.yolo8_wrapper import YOLOv8Detector
from tracking.deep_sort import DeepSortTracker

class TrainingWindow(QMainWindow):
    def __init__(self, video_path: str, manager: LabelManager):
        super().__init__()

        self.setWindowTitle("Training Interface")
        self.setGeometry(100, 100, 1200, 800)

        self.video_path = video_path
        self.manager = manager
        self.cap = cv2.VideoCapture(video_path)
        self.frame_index = 0
        self.current_frame = None

        self.zoom = 1.0
        self.pan_offset = QPoint(0, 0)
        self.dragging = False
        self.last_mouse_pos = QPoint(0, 0)
        self.start_point = None
        self.end_point = None
        self.box_drawing = False
        self.selected_label = MANUAL_LABEL_OPTIONS[0]

        self.detector = YOLOv8Detector("yolov8n.pt")
        self.tracker = DeepSortTracker()
        self.auto_yolo = True

        # UI Elemente
        self.video_label = QLabel()
        self.video_label.setMouseTracking(True)

        self.next_button = QPushButton("Weiter")
        self.prev_button = QPushButton("Zurück")
        self.save_button = QPushButton("Speichern")
        self.rerun_yolo_button = QPushButton("YOLO neu ausführen")
        self.label_dropdown = QComboBox()
        self.yolo_checkbox = QCheckBox("YOLO Auto")
        self.yolo_checkbox.setChecked(True)

        for label in MANUAL_LABEL_OPTIONS:
            self.label_dropdown.addItem(label)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.prev_button)
        button_layout.addWidget(self.next_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.rerun_yolo_button)
        button_layout.addWidget(self.label_dropdown)
        button_layout.addWidget(self.yolo_checkbox)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.video_label)
        main_layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.setStatusBar(QStatusBar())

        # Verbindungen
        self.next_button.clicked.connect(self.next_frame)
        self.prev_button.clicked.connect(self.prev_frame)
        self.save_button.clicked.connect(self.save_frame)
        self.rerun_yolo_button.clicked.connect(self.manual_rerun_yolo)
        self.label_dropdown.currentIndexChanged.connect(self.change_label)
        self.yolo_checkbox.stateChanged.connect(self.toggle_yolo_auto)

        self.video_label.installEventFilter(self)
        self.show()
        self.load_frame()

    def toggle_yolo_auto(self, state):
        self.auto_yolo = state == Qt.Checked

    def change_label(self, index):
        """Aktualisiert das aktuell ausgewählte Label im Dropdown-Menü."""
        self.selected_label = self.label_dropdown.currentText()

    def load_frame(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
        success, frame = self.cap.read()
        if not success:
            print(f"❌ Frame {self.frame_index} konnte nicht geladen werden.")
            return

        self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.zoom = self.calculate_default_zoom()
        self.pan_offset = QPoint(0, 0)

        if self.auto_yolo:
            self.run_yolo()
        self.show_frame()

    def calculate_default_zoom(self):
        window_width = self.video_label.width() if self.video_label.width() > 0 else 1200
        frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        return min((window_width * 0.9) / frame_width, 1.0)

    def run_yolo(self):
        detections = self.detector.detect(self.current_frame)
        tracked = self.tracker.update(detections, self.current_frame)
        for t in tracked:
            ann = Annotation(
                video_id=1,
                frame=self.frame_index,
                label=t["label"],
                box=t["box"],
                source="yolo",
                track_id=t["track_id"]
            )
            self.manager.add_annotation(ann)

    def manual_rerun_yolo(self):
        self.manager.annotations = [a for a in self.manager.annotations if not (a.frame == self.frame_index and a.source == "yolo")]
        self.run_yolo()
        self.show_frame()

    def show_frame(self):
        if self.current_frame is None:
            return

        frame = self.current_frame.copy()
        h, w = frame.shape[:2]
        scaled_w = int(w * self.zoom)
        scaled_h = int(h * self.zoom)
        frame_resized = cv2.resize(frame, (scaled_w, scaled_h))

        image = QImage(frame_resized.data, frame_resized.shape[1], frame_resized.shape[0], frame_resized.strides[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(image)

        painter = QPainter(pixmap)
        pen = QPen(QColor(0, 255, 0), 2)
        painter.setPen(pen)

        for ann in self.manager.get_by_frame(self.frame_index):
            x1, y1, x2, y2 = ann.box
            x1 = int(x1 * self.zoom + self.pan_offset.x())
            y1 = int(y1 * self.zoom + self.pan_offset.y())
            x2 = int(x2 * self.zoom + self.pan_offset.x())
            y2 = int(y2 * self.zoom + self.pan_offset.y())
            painter.drawRect(QRect(QPoint(x1, y1), QPoint(x2, y2)))
            painter.drawText(x1, y1 - 5, ann.label)

        if self.box_drawing and self.start_point and self.end_point:
            painter.setPen(QPen(QColor(255, 0, 0), 1))
            painter.drawRect(QRect(self.start_point, self.end_point))

        painter.end()
        self.video_label.setPixmap(pixmap)

    def mapToImageCoordinates(self, pos):
        label_size = self.video_label.size()
        frame_h, frame_w = self.current_frame.shape[:2]
        scaled_w = frame_w * self.zoom
        scaled_h = frame_h * self.zoom

        offset_x = max((label_size.width() - scaled_w) / 2, 0)
        offset_y = max((label_size.height() - scaled_h) / 2, 0)

        x = (pos.x() - offset_x - self.pan_offset.x()) / self.zoom
        y = (pos.y() - offset_y - self.pan_offset.y()) / self.zoom

        return int(x), int(y)

    def updateMousePositionDisplay(self, pos):
        if self.current_frame is None:
            self.statusBar().showMessage("")
            return
        x, y = self.mapToImageCoordinates(pos)
        frame_h, frame_w = self.current_frame.shape[:2]
        if 0 <= x < frame_w and 0 <= y < frame_h:
            self.statusBar().showMessage(f"X: {x}  Y: {y}")
        else:
            self.statusBar().showMessage("")

    def wheelEvent(self, event):
        old_zoom = self.zoom
        if event.angleDelta().y() > 0:
            self.zoom = min(self.zoom * 1.1, 5.0)
        else:
            self.zoom = max(self.zoom / 1.1, 0.1)

        pos = event.pos()
        rel_x, rel_y = self.mapToImageCoordinates(pos)
        self.pan_offset = QPoint(
            pos.x() - int(rel_x * self.zoom),
            pos.y() - int(rel_y * self.zoom)
        )
        self.show_frame()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Comma:
            self.prev_frame()
        elif event.key() == Qt.Key_Period:
            self.next_frame()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.dragging = True
            self.last_mouse_pos = event.pos()
        elif event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.box_drawing = True

    def mouseMoveEvent(self, event):
        if self.dragging:
            delta = event.pos() - self.last_mouse_pos
            self.pan_offset += delta
            self.last_mouse_pos = event.pos()
            self.show_frame()
        elif self.box_drawing:
            self.end_point = event.pos()
            self.show_frame()
        self.updateMousePositionDisplay(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.dragging = False
        elif event.button() == Qt.LeftButton and self.start_point and self.end_point:
            start_x, start_y = self.mapToImageCoordinates(self.start_point)
            end_x, end_y = self.mapToImageCoordinates(self.end_point)
            x1 = min(start_x, end_x)
            y1 = min(start_y, end_y)
            x2 = max(start_x, end_x)
            y2 = max(start_y, end_y)

            ann = Annotation(
                video_id=1,
                frame=self.frame_index,
                label=self.selected_label,
                box=(x1, y1, x2, y2),
                source="manual"
            )
            self.manager.add_annotation(ann)
            self.box_drawing = False
            self.start_point = None
            self.end_point = None
            self.show_frame()

    def next_frame(self):
        self.frame_index += 1
        self.load_frame()

    def prev_frame(self):
        self.frame_index = max(0, self.frame_index - 1)
        self.load_frame()

    def save_frame(self):
        import pandas as pd
        if not os.path.exists("data/output"):
            os.makedirs("data/output")
        df = pd.DataFrame(self.manager.export_as_dicts())
        df.to_csv("data/output/manual_labels.csv", index=False)
        print(f"✅ Labels gespeichert unter data/output/manual_labels.csv")

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)