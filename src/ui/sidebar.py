"""
Sidebar navigation widget for Sonora: Library views, folders, and custom playlists.
Uses clean SVG vector icons.
"""

import os
from typing import List, Dict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QIcon

from ..resource_utils import get_resource_path, get_icon_path


class Sidebar(QWidget):
    """Left navigation panel with Sonora brand header, library buttons, folders, and playlists."""

    view_selected = pyqtSignal(str, str)   # (view_type, identifier) e.g. ("all", ""), ("folder", "/path"), ("playlist", "Rock")
    add_folder_requested = pyqtSignal()
    create_playlist_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")

        self.current_view = ("all", "")
        self.nav_buttons: List[QPushButton] = []

        self._init_ui()

    def _get_icon(self, name: str) -> QIcon:
        path = get_icon_path(name)
        if os.path.isfile(path):
            return QIcon(path)
        return QIcon()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 16, 0, 16)
        main_layout.setSpacing(6)

        # Brand Header (Sonora + logo)
        brand_layout = QHBoxLayout()
        brand_layout.setContentsMargins(18, 6, 18, 12)
        brand_layout.setSpacing(10)

        icon_path = get_resource_path("assets", "icon.png")
        if os.path.isfile(icon_path):
            icon_label = QLabel()
            pix = QPixmap(icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            icon_label.setPixmap(pix)
            brand_layout.addWidget(icon_label)

        brand_label = QLabel("Sonora")
        brand_label.setObjectName("SidebarBrand")
        brand_label.setStyleSheet("padding: 0; font-size: 20px; font-weight: 800; color: #FFFFFF;")
        brand_layout.addWidget(brand_label)
        brand_layout.addStretch()

        main_layout.addLayout(brand_layout)

        # Main Navigation Group
        self.btn_all = QPushButton("  Your Library")
        self.btn_all.setObjectName("SidebarNavButton")
        self.btn_all.setIcon(self._get_icon("library.svg"))
        self.btn_all.setIconSize(QSize(18, 18))
        self.btn_all.setProperty("view_type", "all")
        self.btn_all.setProperty("view_param", "")
        self.btn_all.setProperty("active", "true")
        self.btn_all.clicked.connect(lambda: self._select_view("all", ""))
        self.nav_buttons.append(self.btn_all)
        main_layout.addWidget(self.btn_all)

        self.btn_recent = QPushButton("  Recently Played")
        self.btn_recent.setObjectName("SidebarNavButton")
        self.btn_recent.setIcon(self._get_icon("history.svg"))
        self.btn_recent.setIconSize(QSize(18, 18))
        self.btn_recent.setProperty("view_type", "recent")
        self.btn_recent.setProperty("view_param", "")
        self.btn_recent.clicked.connect(lambda: self._select_view("recent", ""))
        self.nav_buttons.append(self.btn_recent)
        main_layout.addWidget(self.btn_recent)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: #242424; margin: 8px 16px;")
        main_layout.addWidget(divider)

        # Scrollable Area for Folders & Playlists
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(2)

        # Folders Section Header
        lbl_folders = QLabel("MUSIC FOLDERS")
        lbl_folders.setObjectName("SidebarSectionLabel")
        self.scroll_layout.addWidget(lbl_folders)

        # Add Folder Button
        btn_add_folder = QPushButton("  Add Folder...")
        btn_add_folder.setObjectName("AddFolderButton")
        btn_add_folder.setIcon(self._get_icon("plus.svg"))
        btn_add_folder.setIconSize(QSize(14, 14))
        btn_add_folder.clicked.connect(self.add_folder_requested.emit)
        self.scroll_layout.addWidget(btn_add_folder)

        # Dynamic Folder Buttons Container
        self.folders_container = QVBoxLayout()
        self.folders_container.setSpacing(2)
        self.scroll_layout.addLayout(self.folders_container)

        # Playlists Section Header
        lbl_playlists = QLabel("PLAYLISTS")
        lbl_playlists.setObjectName("SidebarSectionLabel")
        self.scroll_layout.addWidget(lbl_playlists)

        # Add Playlist Button
        btn_add_playlist = QPushButton("  New Playlist...")
        btn_add_playlist.setObjectName("AddFolderButton")
        btn_add_playlist.setIcon(self._get_icon("plus.svg"))
        btn_add_playlist.setIconSize(QSize(14, 14))
        btn_add_playlist.clicked.connect(self.create_playlist_requested.emit)
        self.scroll_layout.addWidget(btn_add_playlist)

        # Dynamic Playlists Container
        self.playlists_container = QVBoxLayout()
        self.playlists_container.setSpacing(2)
        self.scroll_layout.addLayout(self.playlists_container)

        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, stretch=1)

    def _select_view(self, view_type: str, param: str):
        self.current_view = (view_type, param)
        self._update_button_states()
        self.view_selected.emit(view_type, param)

    def _update_button_states(self):
        for btn in self.nav_buttons:
            is_active = (btn.property("view_type") == self.current_view[0] and
                         btn.property("view_param") == self.current_view[1])
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().polish(btn)

    def update_folders(self, folders: List[str]):
        """Rebuild the folder items in the sidebar with folder icons."""
        while self.folders_container.count():
            item = self.folders_container.takeAt(0)
            widget = item.widget()
            if widget:
                if widget in self.nav_buttons:
                    self.nav_buttons.remove(widget)
                widget.deleteLater()

        for folder in folders:
            folder_name = os.path.basename(folder) or folder
            btn = QPushButton(f"  {folder_name}")
            btn.setObjectName("SidebarNavButton")
            btn.setIcon(self._get_icon("folder.svg"))
            btn.setIconSize(QSize(16, 16))
            btn.setToolTip(folder)
            btn.setProperty("view_type", "folder")
            btn.setProperty("view_param", folder)
            btn.clicked.connect(lambda checked, f=folder: self._select_view("folder", f))
            self.nav_buttons.append(btn)
            self.folders_container.addWidget(btn)

        self._update_button_states()

    def update_playlists(self, playlists: List[str]):
        """Rebuild the playlist items in the sidebar."""
        while self.playlists_container.count():
            item = self.playlists_container.takeAt(0)
            widget = item.widget()
            if widget:
                if widget in self.nav_buttons:
                    self.nav_buttons.remove(widget)
                widget.deleteLater()

        for name in playlists:
            btn = QPushButton(f"  {name}")
            btn.setObjectName("SidebarNavButton")
            btn.setIcon(self._get_icon("library.svg"))
            btn.setIconSize(QSize(16, 16))
            btn.setProperty("view_type", "playlist")
            btn.setProperty("view_param", name)
            btn.clicked.connect(lambda checked, n=name: self._select_view("playlist", n))
            self.nav_buttons.append(btn)
            self.playlists_container.addWidget(btn)

        self._update_button_states()
