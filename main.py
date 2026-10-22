"""
Sonora - High-Fidelity Local Desktop Music Player
Entry point for launching the desktop application.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from src.ui.main_window import MainWindow
from src.resource_utils import get_resource_path


def main():
    # Enable High DPI scaling
    if hasattr(Qt.ApplicationAttribute, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Sonora")
    app.setApplicationDisplayName("Sonora")
    app.setOrganizationName("faizancodecom")
    app.setOrganizationDomain("github.com/faizancodecom")

    # Set application icon
    icon_path = get_resource_path("assets", "icon.ico")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
