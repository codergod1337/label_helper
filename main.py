# main.py - Startet das Labeling-Tool

from labeling.label_drawer import LabelDrawer
from PyQt5.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    window = LabelDrawer()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()