"""
Spotify-style track table displaying songs, thumbnails, artists, albums, and durations.
Uses clean vector icons and context menu metadata editing.
"""

import os
import subprocess
from typing import List, Dict, Any, Optional
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu,
    QAbstractItemView, QLabel, QWidget, QHBoxLayout, QVBoxLayout
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from ..metadata_manager import MetadataManager
from ..resource_utils import get_resource_path, get_icon_path
from .dialogs import EditTrackDialog


class TrackTable(QTableWidget):
    """Interactive track list table with custom thumbnail rendering and context menu."""

    track_selected = pyqtSignal(int)          # Index within currently displayed list
    track_double_clicked = pyqtSignal(int)   # Index to play
    track_metadata_changed = pyqtSignal(dict) # Emits updated track dict
    track_removed = pyqtSignal(str)          # file_path of removed track
    add_to_playlist = pyqtSignal(str, str)    # (playlist_name, file_path)
    new_playlist_and_add = pyqtSignal(str)    # (file_path)
    remove_from_playlist = pyqtSignal(str)    # (file_path)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.tracks: List[Dict[str, Any]] = []
        self.active_track_path: Optional[str] = None
        self._pixmap_cache: Dict[str, QPixmap] = {}
        self._default_cover: Optional[QPixmap] = None
        self.playlist_provider = None
        self.current_playlist_name: Optional[str] = None

        self._init_ui()

    def set_playlist_provider(self, provider_func):
        self.playlist_provider = provider_func

    def set_current_playlist_name(self, name: Optional[str]):
        self.current_playlist_name = name

    def _get_icon(self, name: str) -> QIcon:
        path = get_icon_path(name)
        if os.path.isfile(path):
            return QIcon(path)
        return QIcon()

    def _init_ui(self):
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["#", "COVER", "TITLE & ARTIST", "ALBUM", "TIME"])

        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 48)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(1, 56)

        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(3, 200)

        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 70)

        self.verticalHeader().setDefaultSectionSize(54)

        # Signals
        self.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._load_default_cover()

    def _load_default_cover(self):
        assets_cover = get_resource_path("assets", "default_cover.png")
        if os.path.isfile(assets_cover):
            self._default_cover = self._create_rounded_pixmap(QPixmap(assets_cover), 40, 40, 4)

    def _create_rounded_pixmap(self, src_pixmap: QPixmap, width: int, height: int, radius: int) -> QPixmap:
        """Create a smoothed, rounded rectangle pixmap for thumbnails."""
        scaled = src_pixmap.scaled(
            width, height,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        target = QPixmap(width, height)
        target.fill(Qt.GlobalColor.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(0, 0, width, height, radius, radius)
        painter.setClipPath(path)
        x = (scaled.width() - width) // 2
        y = (scaled.height() - height) // 2
        painter.drawPixmap(0, 0, scaled, x, y, width, height)
        painter.end()

        return target

    def get_track_pixmap(self, file_path: str) -> QPixmap:
        """Get cached thumbnail pixmap or extract it."""
        if file_path in self._pixmap_cache:
            return self._pixmap_cache[file_path]

        raw = MetadataManager.get_album_art_bytes(file_path)
        if raw:
            qimg = QImage.fromData(raw)
            if not qimg.isNull():
                pm = self._create_rounded_pixmap(QPixmap.fromImage(qimg), 40, 40, 4)
                self._pixmap_cache[file_path] = pm
                return pm

        if self._default_cover:
            return self._default_cover

        fallback = QPixmap(40, 40)
        fallback.fill(QColor("#242424"))
        return fallback

    def set_tracks(self, tracks: List[Dict[str, Any]], active_path: Optional[str] = None):
        """Populate the table with track records."""
        self.tracks = list(tracks)
        self.active_track_path = active_path
        self.setRowCount(len(self.tracks))

        for row, track in enumerate(self.tracks):
            file_path = track.get("file_path", "")
            is_active = (file_path == self.active_track_path)

            # Col 0: Index / Playing Indicator
            idx_item = QTableWidgetItem(f"{row + 1}")
            idx_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if is_active:
                idx_item.setText("▶")
                idx_item.setForeground(QColor("#1DB954"))
            else:
                idx_item.setForeground(QColor("#777777"))
            self.setItem(row, 0, idx_item)

            # Col 1: Cover Thumbnail Widget
            cover_label = QLabel()
            cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = self.get_track_pixmap(file_path)
            cover_label.setPixmap(pix)
            self.setCellWidget(row, 1, cover_label)

            # Col 2: Title & Artist (Rich widget)
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            info_layout.setContentsMargins(4, 6, 4, 6)
            info_layout.setSpacing(2)

            title_lbl = QLabel(track.get("title", "Unknown Title"))
            title_lbl.setStyleSheet(
                "font-weight: 600; font-size: 13px; color: " + ("#1DB954;" if is_active else "#FFFFFF;")
            )

            artist_lbl = QLabel(track.get("artist", "Unknown Artist"))
            artist_lbl.setStyleSheet("font-size: 11px; color: #A0A0A0;")

            info_layout.addWidget(title_lbl)
            info_layout.addWidget(artist_lbl)
            self.setCellWidget(row, 2, info_widget)

            # Col 3: Album
            album_item = QTableWidgetItem(track.get("album", "Unknown Album"))
            album_item.setForeground(QColor("#A0A0A0"))
            self.setItem(row, 3, album_item)

            # Col 4: Duration
            time_item = QTableWidgetItem(track.get("duration_str", "00:00"))
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            time_item.setForeground(QColor("#888888"))
            self.setItem(row, 4, time_item)

    def set_active_track(self, active_path: str):
        """Update visual highlight for currently playing track without reloading entire table."""
        self.active_track_path = active_path
        for row in range(self.rowCount()):
            if row < len(self.tracks):
                track = self.tracks[row]
                is_active = (track.get("file_path") == active_path)

                idx_item = self.item(row, 0)
                if idx_item:
                    if is_active:
                        idx_item.setText("▶")
                        idx_item.setForeground(QColor("#1DB954"))
                    else:
                        idx_item.setText(f"{row + 1}")
                        idx_item.setForeground(QColor("#777777"))

                info_widget = self.cellWidget(row, 2)
                if info_widget:
                    title_lbl = info_widget.findChild(QLabel)
                    if title_lbl:
                        title_lbl.setStyleSheet(
                            "font-weight: 600; font-size: 13px; color: " + ("#1DB954;" if is_active else "#FFFFFF;")
                        )

    def invalidate_cover_cache(self, file_path: str):
        """Clear cached thumbnail for a file and refresh its row."""
        if file_path in self._pixmap_cache:
            del self._pixmap_cache[file_path]

        for row, track in enumerate(self.tracks):
            if track.get("file_path") == file_path:
                cover_widget = self.cellWidget(row, 1)
                if isinstance(cover_widget, QLabel):
                    cover_widget.setPixmap(self.get_track_pixmap(file_path))
                break

    def _on_cell_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.tracks):
            self.track_double_clicked.emit(row)

    def _show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return

        row = item.row()
        if not (0 <= row < len(self.tracks)):
            return

        track = self.tracks[row]
        file_path = track.get("file_path", "")
        menu = QMenu(self)

        play_action = menu.addAction(self._get_icon("play.svg"), "Play")
        menu.addSeparator()

        # Add to Playlist Submenu
        playlist_menu = menu.addMenu(self._get_icon("library.svg"), "Add to Playlist")
        playlists = self.playlist_provider() if callable(self.playlist_provider) else []
        playlist_actions = {}
        for p_name in playlists:
            act = playlist_menu.addAction(self._get_icon("library.svg"), p_name)
            playlist_actions[act] = p_name

        if playlists:
            playlist_menu.addSeparator()
        new_playlist_act = playlist_menu.addAction(self._get_icon("plus.svg"), "New Playlist...")

        # If inside a playlist view, allow removing from it
        remove_from_pl_act = None
        if self.current_playlist_name:
            remove_from_pl_act = menu.addAction(f"Remove from '{self.current_playlist_name}'")

        menu.addSeparator()
        edit_action = menu.addAction(self._get_icon("edit.svg"), "Edit Track Info & Artwork...")
        explore_action = menu.addAction(self._get_icon("folder.svg"), "Show in File Explorer")
        menu.addSeparator()
        remove_action = menu.addAction("Remove from Library")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == play_action:
            self.track_double_clicked.emit(row)
        elif action in playlist_actions:
            self.add_to_playlist.emit(playlist_actions[action], file_path)
        elif action == new_playlist_act:
            self.new_playlist_and_add.emit(file_path)
        elif action == remove_from_pl_act and remove_from_pl_act is not None:
            self.remove_from_playlist.emit(file_path)
        elif action == edit_action:
            dlg = EditTrackDialog(track, self)
            dlg.track_updated.connect(self._on_metadata_updated)
            dlg.exec()
        elif action == explore_action:
            if os.path.exists(file_path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(file_path)}"')
        elif action == remove_action:
            self.track_removed.emit(file_path)

    def _on_metadata_updated(self, updated_track: dict):
        file_path = updated_track.get("file_path", "")
        self.invalidate_cover_cache(file_path)

        # Update in-memory track record
        for i, t in enumerate(self.tracks):
            if t.get("file_path") == file_path:
                self.tracks[i] = updated_track
                break

        # Re-render this row
        self.set_tracks(self.tracks, active_path=self.active_track_path)
        self.track_metadata_changed.emit(updated_track)
