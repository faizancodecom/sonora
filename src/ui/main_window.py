"""
Main application window for Sonora.
"""

import os
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QLabel, QPushButton, QFileDialog,
    QInputDialog, QMessageBox, QFrame
)
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtCore import Qt

from .styles import DARK_THEME_QSS
from .sidebar import Sidebar
from .track_table import TrackTable
from .player_bar import PlayerBar
from .dialogs import ScannerWorker, ScanProgressDialog
from ..playlist_manager import PlaylistManager
from ..audio_player import AudioPlayer
from ..metadata_manager import format_duration
from ..remix_engine import RemixEngine
from ..resource_utils import get_resource_path, get_icon_path
from .remix_dialog import RemixDialog


class MainWindow(QMainWindow):
    """Primary application window coordinating playback, library, and UI components."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Sonora")
        self.resize(1150, 720)
        self.setMinimumSize(850, 550)

        # Set App Icon
        icon_path = get_resource_path("assets", "icon.ico")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Core logic
        self.playlist_mgr = PlaylistManager()
        self.audio_player = AudioPlayer(self)
        self.remix_engine = RemixEngine(self)

        # Current view state
        self.current_view_type = "all"
        self.current_view_param = ""
        self.active_tracks: List[Dict[str, Any]] = []

        self._init_ui()
        self._connect_signals()
        self._setup_shortcuts()

        # Load initial state
        self.sidebar.update_folders(self.playlist_mgr.folders)
        self.sidebar.update_playlists(list(self.playlist_mgr.playlists.keys()))
        self._refresh_current_view()

        # Restore saved settings
        saved_vol = self.playlist_mgr.settings.get("volume", 75)
        self.audio_player.set_volume(saved_vol)
        self.player_bar.update_volume_display(saved_vol)

    def _get_icon(self, name: str) -> QIcon:
        path = get_icon_path(name)
        if os.path.isfile(path):
            return QIcon(path)
        return QIcon()

    def _init_ui(self):
        self.setStyleSheet(DARK_THEME_QSS)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Top area: Sidebar + Main Content View
        top_split = QWidget()
        top_layout = QHBoxLayout(top_split)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)

        # Sidebar (Left)
        self.sidebar = Sidebar(self)
        top_layout.addWidget(self.sidebar)

        # Main Content Area (Right)
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(24, 16, 24, 0)
        main_layout.setSpacing(14)

        # Header: Search & View Title
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search tracks, artists, albums...")
        self.search_input.addAction(self._get_icon("search.svg"), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_input)

        header_layout.addStretch()

        # Shuffle Play Button
        self.btn_shuffle_play = QPushButton("  Shuffle Play")
        self.btn_shuffle_play.setObjectName("PrimaryBtn")
        self.btn_shuffle_play.setIcon(self._get_icon("shuffle.svg"))
        self.btn_shuffle_play.setToolTip("Shuffle and play a random track from this view")
        self.btn_shuffle_play.clicked.connect(self._on_shuffle_play_clicked)
        header_layout.addWidget(self.btn_shuffle_play)

        # Scan Button
        self.btn_scan = QPushButton("  Scan Folder...")
        self.btn_scan.setObjectName("SecondaryBtn")
        self.btn_scan.setIcon(self._get_icon("folder.svg"))
        self.btn_scan.clicked.connect(self._on_add_folder)
        header_layout.addWidget(self.btn_scan)

        main_layout.addWidget(header_widget)

        # View Title & Stats bar
        view_meta_widget = QWidget()
        view_meta_layout = QHBoxLayout(view_meta_widget)
        view_meta_layout.setContentsMargins(4, 4, 4, 4)

        self.view_title_label = QLabel("Your Library")
        self.view_title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")

        self.stats_label = QLabel("0 songs")
        self.stats_label.setObjectName("StatsLabel")

        view_meta_layout.addWidget(self.view_title_label)
        view_meta_layout.addSpacing(16)
        view_meta_layout.addWidget(self.stats_label)
        view_meta_layout.addStretch()

        main_layout.addWidget(view_meta_widget)

        # Track Table
        self.track_table = TrackTable(self)
        self.track_table.set_playlist_provider(lambda: list(self.playlist_mgr.playlists.keys()))
        main_layout.addWidget(self.track_table, stretch=1)

        top_layout.addWidget(main_content, stretch=1)
        root_layout.addWidget(top_split, stretch=1)

        # Bottom Player Dock (Persistent)
        self.player_bar = PlayerBar(self)
        root_layout.addWidget(self.player_bar)

    def _connect_signals(self):
        # Sidebar
        self.sidebar.view_selected.connect(self._on_view_changed)
        self.sidebar.add_folder_requested.connect(self._on_add_folder)
        self.sidebar.create_playlist_requested.connect(self._on_create_playlist)

        # Table
        self.track_table.track_double_clicked.connect(self._on_track_double_clicked)
        self.track_table.track_metadata_changed.connect(self._on_track_metadata_updated)
        self.track_table.track_removed.connect(self._on_track_removed)
        self.track_table.add_to_playlist.connect(self._on_add_to_playlist)
        self.track_table.new_playlist_and_add.connect(self._on_new_playlist_and_add)
        self.track_table.remove_from_playlist.connect(self._on_remove_from_playlist)

        # Player Bar -> Audio Player
        self.player_bar.play_pause_clicked.connect(self.audio_player.toggle_play_pause)
        self.player_bar.next_clicked.connect(self.audio_player.next_track)
        self.player_bar.prev_clicked.connect(self.audio_player.previous_track)
        self.player_bar.seek_requested.connect(self.audio_player.seek)
        self.player_bar.volume_changed.connect(self._on_volume_changed)
        self.player_bar.mute_toggled.connect(self._on_mute_toggled)
        self.player_bar.shuffle_toggled.connect(self._on_shuffle_toggled)
        self.player_bar.repeat_cycled.connect(self._on_repeat_cycled)
        self.player_bar.track_updated.connect(self._on_track_metadata_updated)
        self.player_bar.remix_clicked.connect(self._open_remix_dialog)

        # Audio Player -> UI & Remix Engine
        self.audio_player.track_changed.connect(self._on_audio_track_changed)
        self.audio_player.state_changed.connect(self.player_bar.set_playing_state)
        self.audio_player.state_changed.connect(self.remix_engine.sync_playback)
        self.audio_player.position_changed.connect(self.player_bar.update_position)

    def _setup_shortcuts(self):
        # Spacebar for Play/Pause
        shortcut_space = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        shortcut_space.activated.connect(self.audio_player.toggle_play_pause)

        # Ctrl+Right for Next
        shortcut_next = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Right), self)
        shortcut_next.activated.connect(self.audio_player.next_track)

        # Ctrl+Left for Prev
        shortcut_prev = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Left), self)
        shortcut_prev.activated.connect(self.audio_player.previous_track)

        # Ctrl+F to focus search
        shortcut_search = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_F), self)
        shortcut_search.activated.connect(self.search_input.setFocus)

    def _on_view_changed(self, view_type: str, param: str):
        self.current_view_type = view_type
        self.current_view_param = param
        self.search_input.clear()
        self._refresh_current_view()

    def _refresh_current_view(self):
        query = self.search_input.text().strip().lower()

        if self.current_view_type == "all":
            self.view_title_label.setText("Your Library")
            tracks = self.playlist_mgr.tracks
        elif self.current_view_type == "recent":
            self.view_title_label.setText("Recently Played")
            recent_paths = set(self.playlist_mgr.recently_played)
            tracks = [t for t in self.playlist_mgr.tracks if t["file_path"] in recent_paths]
        elif self.current_view_type == "folder":
            folder_name = os.path.basename(self.current_view_param) or self.current_view_param
            self.view_title_label.setText(f"Folder: {folder_name}")
            tracks = self.playlist_mgr.get_tracks_by_folder(self.current_view_param)
        elif self.current_view_type == "playlist":
            self.view_title_label.setText(f"Playlist: {self.current_view_param}")
            tracks = self.playlist_mgr.get_playlist_tracks(self.current_view_param)
        else:
            tracks = self.playlist_mgr.tracks

        # Apply search filter if active
        if query:
            filtered = []
            for t in tracks:
                searchable = f"{t.get('title', '')} {t.get('artist', '')} {t.get('album', '')}".lower()
                if query in searchable:
                    filtered.append(t)
            self.active_tracks = filtered
        else:
            self.active_tracks = tracks

        # Update stats
        total_seconds = sum(t.get("duration", 0) for t in self.active_tracks)
        formatted_total = format_duration(total_seconds)
        self.stats_label.setText(f"{len(self.active_tracks)} songs • {formatted_total}")

        # Update table
        self.track_table.set_current_playlist_name(self.current_view_param if self.current_view_type == "playlist" else None)
        current_playing = self.audio_player.get_current_track()
        active_path = current_playing.get("file_path") if current_playing else None
        self.track_table.set_tracks(self.active_tracks, active_path=active_path)

    def _on_search_changed(self, text: str):
        self._refresh_current_view()

    def _on_track_double_clicked(self, row: int):
        if 0 <= row < len(self.active_tracks):
            self.audio_player.set_queue(self.active_tracks, start_index=row)

    def _on_audio_track_changed(self, track: dict):
        self.player_bar.set_track_info(track)
        file_path = track.get("file_path", "")
        self.track_table.set_active_track(file_path)
        self.playlist_mgr.record_recently_played(file_path)

    def _on_track_metadata_updated(self, updated_track: dict):
        file_path = updated_track.get("file_path", "")
        self.track_table.invalidate_cover_cache(file_path)

        for i, t in enumerate(self.playlist_mgr.tracks):
            if t.get("file_path") == file_path:
                self.playlist_mgr.tracks[i] = updated_track
                break

        for i, t in enumerate(self.active_tracks):
            if t.get("file_path") == file_path:
                self.active_tracks[i] = updated_track
                break

        cur_track = self.audio_player.get_current_track()
        if cur_track and cur_track.get("file_path") == file_path:
            self.player_bar.set_track_info(updated_track)

        self.playlist_mgr.save()
        self._refresh_current_view()

    def _on_track_removed(self, file_path: str):
        self.playlist_mgr.remove_track(file_path)
        self._refresh_current_view()

    def _on_volume_changed(self, volume: int):
        self.audio_player.set_volume(volume)
        self.playlist_mgr.settings["volume"] = volume
        self.player_bar.update_volume_display(volume, is_muted=self.audio_player.is_muted())

    def _on_mute_toggled(self):
        is_muted = self.audio_player.toggle_mute()
        vol = self.audio_player.get_volume()
        self.player_bar.update_volume_display(vol, is_muted=is_muted)

    def _on_shuffle_toggled(self):
        new_state = self.audio_player.toggle_shuffle()
        self.player_bar.set_shuffle_state(new_state)
        self.playlist_mgr.settings["shuffle"] = new_state

    def _on_repeat_cycled(self):
        new_mode = self.audio_player.cycle_repeat_mode()
        self.player_bar.set_repeat_state(new_mode)
        self.playlist_mgr.settings["repeat"] = new_mode

    def _on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Music Directory to Scan")
        if not folder:
            return

        progress_dlg = ScanProgressDialog(self)
        worker = ScannerWorker(self.playlist_mgr, folder, recursive=True)

        worker.progress.connect(progress_dlg.update_progress)

        def on_finished(new_tracks):
            progress_dlg.accept()
            self.sidebar.update_folders(self.playlist_mgr.folders)
            self._refresh_current_view()
            QMessageBox.information(
                self, "Scan Complete",
                f"Successfully scanned folder and added {len(new_tracks)} new tracks to your library."
            )

        worker.finished.connect(on_finished)
        worker.start()
        progress_dlg.exec()

    def _on_create_playlist(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Enter playlist name:")
        if ok and name.strip():
            if self.playlist_mgr.create_playlist(name.strip()):
                self.sidebar.update_playlists(list(self.playlist_mgr.playlists.keys()))
            else:
                QMessageBox.warning(self, "Playlist Exists", "A playlist with that name already exists.")

    def _on_add_to_playlist(self, playlist_name: str, file_path: str):
        if self.playlist_mgr.add_to_playlist(playlist_name, file_path):
            QMessageBox.information(self, "Added to Playlist", f"Added track to playlist '{playlist_name}'.")
            if self.current_view_type == "playlist" and self.current_view_param == playlist_name:
                self._refresh_current_view()
        else:
            QMessageBox.information(self, "Already in Playlist", f"This track is already inside '{playlist_name}'.")

    def _on_new_playlist_and_add(self, file_path: str):
        name, ok = QInputDialog.getText(self, "New Playlist", "Enter playlist name:")
        if ok and name.strip():
            p_name = name.strip()
            if self.playlist_mgr.create_playlist(p_name):
                self.playlist_mgr.add_to_playlist(p_name, file_path)
                self.sidebar.update_playlists(list(self.playlist_mgr.playlists.keys()))
                QMessageBox.information(self, "Playlist Created", f"Created '{p_name}' and added track.")
                if self.current_view_type == "playlist" and self.current_view_param == p_name:
                    self._refresh_current_view()
            else:
                QMessageBox.warning(self, "Playlist Exists", "A playlist with that name already exists.")

    def _on_remove_from_playlist(self, file_path: str):
        if self.current_view_type == "playlist" and self.current_view_param:
            self.playlist_mgr.remove_from_playlist(self.current_view_param, file_path)
            self._refresh_current_view()

    def _on_shuffle_play_clicked(self):
        """Shuffle and immediately play a random track from current view."""
        if not self.active_tracks:
            return
        import random
        rand_idx = random.randint(0, len(self.active_tracks) - 1)
        self.audio_player.is_shuffle = True
        self.player_bar.set_shuffle_state(True)
        self.playlist_mgr.settings["shuffle"] = True
        self.audio_player.set_queue(self.active_tracks, start_index=rand_idx)

    def _open_remix_dialog(self):
        """Open the Remix & Sound Layers dialog."""
        dlg = RemixDialog(self.remix_engine, self.audio_player, self)
        dlg.exec()

    def closeEvent(self, event):
        """Save settings and stop remix playback on application exit."""
        self.remix_engine.stop_all()
        self.playlist_mgr.save()
        event.accept()
