# main.py - Startet das Labeling-Tool

from labeling.label_drawer import LabelDrawer
from labeling.label_manager import LabelManager
from PyQt5.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)

    manager = LabelManager()
    manager.load_project()   # <<< automatisch laden

    window = LabelDrawer(manager)  # <<< manager übergeben
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()