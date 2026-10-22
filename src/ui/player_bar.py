"""
Bottom Spotify-style playback dock with track thumbnail, vector icon controls, scrubber, and volume.
"""

import os
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QSlider, QToolButton
)
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QColor, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize

from ..metadata_manager import MetadataManager, format_duration
from ..resource_utils import get_resource_path, get_icon_path
from .dialogs import EditTrackDialog


class ClickableSlider(QSlider):
    """
    Precision scrubbing slider that jumps immediately to click location
    and tracks drag events accurately without jumping back.
    """
    scrub_started = pyqtSignal()
    scrub_moved = pyqtSignal(int)
    scrub_finished = pyqtSignal(int)

    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setMouseTracking(True)
        self._is_dragging = False

    def _pos_to_val(self, pos_x: float) -> int:
        w = max(1, self.width())
        ratio = max(0.0, min(1.0, pos_x / float(w)))
        return int(round(self.minimum() + ratio * (self.maximum() - self.minimum())))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            val = self._pos_to_val(event.position().x())
            self.setValue(val)
            self.scrub_started.emit()
            self.scrub_moved.emit(val)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging and (event.buttons() & Qt.MouseButton.LeftButton):
            val = self._pos_to_val(event.position().x())
            self.setValue(val)
            self.scrub_moved.emit(val)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False
            val = self._pos_to_val(event.position().x())
            self.setValue(val)
            self.scrub_finished.emit(val)
            event.accept()
            return
        super().mouseReleaseEvent(event)


class PlayerBar(QWidget):
    """Bottom playback dock providing playback controls, seeking, volume, and cover preview."""

    play_pause_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    shuffle_toggled = pyqtSignal()
    repeat_cycled = pyqtSignal()
    seek_requested = pyqtSignal(int)      # Target millisecond
    volume_changed = pyqtSignal(int)      # 0-100
    mute_toggled = pyqtSignal()
    track_updated = pyqtSignal(dict)      # emitted when metadata is edited
    remix_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PlayerBarWidget")

        self.current_track: Optional[Dict[str, Any]] = None
        self._is_scrubbing = False
        self._current_duration_ms = 0
        self._default_cover_pixmap = None

        self._load_default_cover()
        self._init_ui()

    def _get_icon(self, name: str) -> QIcon:
        path = get_icon_path(name)
        if os.path.isfile(path):
            return QIcon(path)
        return QIcon()

    def _load_default_cover(self):
        assets_cover = get_resource_path("assets", "default_cover.png")
        if os.path.isfile(assets_cover):
            self._default_cover_pixmap = self._round_pixmap(QPixmap(assets_cover), 52, 52, 6)

    def _round_pixmap(self, src: QPixmap, w: int, h: int, radius: int) -> QPixmap:
        scaled = src.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        target = QPixmap(w, h)
        target.fill(Qt.GlobalColor.transparent)
        p = QPainter(target)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, radius, radius)
        p.setClipPath(path)
        x = (scaled.width() - w) // 2
        y = (scaled.height() - h) // 2
        p.drawPixmap(0, 0, scaled, x, y, w, h)
        p.end()
        return target

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(16)

        # ----------------- LEFT SECTION: Current Track Info -----------------
        left_widget = QWidget()
        left_widget.setFixedWidth(280)
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(52, 52)
        if self._default_cover_pixmap:
            self.cover_label.setPixmap(self._default_cover_pixmap)
        else:
            self.cover_label.setStyleSheet("background-color: #242424; border-radius: 6px;")

        track_info_layout = QVBoxLayout()
        track_info_layout.setContentsMargins(0, 4, 0, 4)
        track_info_layout.setSpacing(2)

        self.title_label = QLabel("No track playing")
        self.title_label.setObjectName("TrackTitleLabel")
        self.title_label.setFixedWidth(150)

        self.artist_label = QLabel("Choose a song to start")
        self.artist_label.setObjectName("TrackArtistLabel")
        self.artist_label.setFixedWidth(150)

        track_info_layout.addWidget(self.title_label)
        track_info_layout.addWidget(self.artist_label)

        # Edit Track button on player bar
        self.edit_btn = QToolButton()
        self.edit_btn.setIcon(self._get_icon("edit.svg"))
        self.edit_btn.setIconSize(QSize(14, 14))
        self.edit_btn.setToolTip("Edit Track Info & Artwork")
        self.edit_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 5px;
                background-color: #1a1a1a;
            }
            QToolButton:hover {
                border-color: #1DB954;
                background-color: #262626;
            }
        """)
        self.edit_btn.clicked.connect(self._open_edit_dialog)

        left_layout.addWidget(self.cover_label)
        left_layout.addLayout(track_info_layout)
        left_layout.addWidget(self.edit_btn)
        left_layout.addStretch()

        # ----------------- CENTER SECTION: Playback Controls & Scrubber -----------------
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)

        # Controls row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(14)
        controls_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Shuffle button
        self.shuffle_btn = QPushButton()
        self.shuffle_btn.setObjectName("ControlIconButton")
        self.shuffle_btn.setIcon(self._get_icon("shuffle.svg"))
        self.shuffle_btn.setIconSize(QSize(16, 16))
        self.shuffle_btn.setToolTip("Shuffle (Off)")
        self.shuffle_btn.clicked.connect(self.shuffle_toggled.emit)

        # Previous button
        self.prev_btn = QPushButton()
        self.prev_btn.setObjectName("ControlIconButton")
        self.prev_btn.setIcon(self._get_icon("prev.svg"))
        self.prev_btn.setIconSize(QSize(16, 16))
        self.prev_btn.setToolTip("Previous Track")
        self.prev_btn.clicked.connect(self.prev_clicked.emit)

        # Play/Pause button
        self.play_pause_btn = QPushButton()
        self.play_pause_btn.setObjectName("PlayPauseButton")
        self.play_pause_btn.setIcon(self._get_icon("play.svg"))
        self.play_pause_btn.setIconSize(QSize(16, 16))
        self.play_pause_btn.setToolTip("Play")
        self.play_pause_btn.clicked.connect(self.play_pause_clicked.emit)

        # Next button
        self.next_btn = QPushButton()
        self.next_btn.setObjectName("ControlIconButton")
        self.next_btn.setIcon(self._get_icon("next.svg"))
        self.next_btn.setIconSize(QSize(16, 16))
        self.next_btn.setToolTip("Next Track")
        self.next_btn.clicked.connect(self.next_clicked.emit)

        # Repeat / Loop button
        self.repeat_btn = QPushButton()
        self.repeat_btn.setObjectName("ControlIconButton")
        self.repeat_btn.setIcon(self._get_icon("repeat.svg"))
        self.repeat_btn.setIconSize(QSize(16, 16))
        self.repeat_btn.setToolTip("Repeat (Off)")
        self.repeat_btn.clicked.connect(self.repeat_cycled.emit)

        controls_layout.addWidget(self.shuffle_btn)
        controls_layout.addWidget(self.prev_btn)
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.next_btn)
        controls_layout.addWidget(self.repeat_btn)

        # Time & Scrubber row
        time_layout = QHBoxLayout()
        time_layout.setSpacing(10)

        self.cur_time_label = QLabel("0:00")
        self.cur_time_label.setObjectName("TimeLabel")
        self.cur_time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setObjectName("SeekSlider")
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setValue(0)
        self.seek_slider.scrub_started.connect(self._on_scrub_started)
        self.seek_slider.scrub_moved.connect(self._on_scrub_moved)
        self.seek_slider.scrub_finished.connect(self._on_scrub_finished)

        self.tot_time_label = QLabel("0:00")
        self.tot_time_label.setObjectName("TimeLabel")
        self.tot_time_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        time_layout.addWidget(self.cur_time_label)
        time_layout.addWidget(self.seek_slider)
        time_layout.addWidget(self.tot_time_label)

        center_layout.addLayout(controls_layout)
        center_layout.addLayout(time_layout)

        # ----------------- RIGHT SECTION: Volume & Extras -----------------
        right_widget = QWidget()
        right_widget.setFixedWidth(240)
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.mute_btn = QPushButton()
        self.mute_btn.setObjectName("ControlIconButton")
        self.mute_btn.setIcon(self._get_icon("volume_high.svg"))
        self.mute_btn.setIconSize(QSize(16, 16))
        self.mute_btn.setToolTip("Mute/Unmute")
        self.mute_btn.clicked.connect(self.mute_toggled.emit)

        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("VolumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(75)
        self.volume_slider.setFixedWidth(90)
        self.volume_slider.scrub_moved.connect(self.volume_changed.emit)
        self.volume_slider.scrub_finished.connect(self.volume_changed.emit)

        self.volume_label = QLabel("75%")
        self.volume_label.setStyleSheet("color: #888888; font-size: 11px; font-family: monospace; min-width: 32px;")

        self.remix_btn = QPushButton()
        self.remix_btn.setObjectName("ControlIconButton")
        self.remix_btn.setIcon(self._get_icon("remix.svg"))
        self.remix_btn.setIconSize(QSize(16, 16))
        self.remix_btn.setToolTip("Remix & Sound Layers (Drums, Piano, Jazz, Classic, Custom)")
        self.remix_btn.clicked.connect(self.remix_clicked.emit)

        right_layout.addWidget(self.mute_btn)
        right_layout.addWidget(self.volume_slider)
        right_layout.addWidget(self.volume_label)
        right_layout.addWidget(self.remix_btn)

        # Assemble Main Bar
        main_layout.addWidget(left_widget)
        main_layout.addWidget(center_widget, stretch=1)
        main_layout.addWidget(right_widget)

    def set_track_info(self, track: dict):
        """Update display with new track metadata."""
        self.current_track = track
        title = track.get("title", "Unknown Title")
        artist = track.get("artist", "Unknown Artist")

        self.title_label.setText(title if len(title) <= 24 else title[:22] + "...")
        self.title_label.setToolTip(title)

        self.artist_label.setText(artist if len(artist) <= 26 else artist[:24] + "...")
        self.artist_label.setToolTip(artist)

        file_path = track.get("file_path", "")
        self.update_cover_image(file_path)

    def update_cover_image(self, file_path: str):
        """Reload cover artwork for track."""
        raw = MetadataManager.get_album_art_bytes(file_path)
        if raw:
            qimg = QImage.fromData(raw)
            if not qimg.isNull():
                pm = self._round_pixmap(QPixmap.fromImage(qimg), 52, 52, 6)
                self.cover_label.setPixmap(pm)
                return

        if self._default_cover_pixmap:
            self.cover_label.setPixmap(self._default_cover_pixmap)

    def set_playing_state(self, is_playing: bool):
        """Update play/pause button icon."""
        if is_playing:
            self.play_pause_btn.setIcon(self._get_icon("pause.svg"))
            self.play_pause_btn.setToolTip("Pause")
        else:
            self.play_pause_btn.setIcon(self._get_icon("play.svg"))
            self.play_pause_btn.setToolTip("Play")

    def update_position(self, pos_ms: int, dur_ms: int):
        """Update time labels and seek slider."""
        self._current_duration_ms = dur_ms
        if not self._is_scrubbing:
            if dur_ms > 0:
                self.seek_slider.setMaximum(dur_ms)
                self.seek_slider.setValue(pos_ms)
            else:
                self.seek_slider.setMaximum(1000)
                self.seek_slider.setValue(0)

            self.cur_time_label.setText(format_duration(pos_ms / 1000.0))
            self.tot_time_label.setText(format_duration(dur_ms / 1000.0))

    def update_volume_display(self, volume: int, is_muted: bool = False):
        """Update volume slider and icon."""
        self.volume_slider.blockSignals(True)
        self.volume_slider.setValue(volume)
        self.volume_slider.blockSignals(False)

        self.volume_label.setText(f"{volume}%")
        if is_muted or volume == 0:
            self.mute_btn.setIcon(self._get_icon("volume_mute.svg"))
        elif volume < 50:
            self.mute_btn.setIcon(self._get_icon("volume_low.svg"))
        else:
            self.mute_btn.setIcon(self._get_icon("volume_high.svg"))

    def set_shuffle_state(self, is_shuffle: bool):
        if is_shuffle:
            self.shuffle_btn.setIcon(self._get_icon("shuffle_active.svg"))
            self.shuffle_btn.setProperty("active", "true")
            self.shuffle_btn.setToolTip("Shuffle (On)")
        else:
            self.shuffle_btn.setIcon(self._get_icon("shuffle.svg"))
            self.shuffle_btn.setProperty("active", "false")
            self.shuffle_btn.setToolTip("Shuffle (Off)")
        self.shuffle_btn.style().polish(self.shuffle_btn)

    def set_repeat_state(self, repeat_mode: str):
        # repeat_mode: "off", "all", "one"
        if repeat_mode == "off":
            self.repeat_btn.setIcon(self._get_icon("repeat.svg"))
            self.repeat_btn.setProperty("active", "false")
            self.repeat_btn.setToolTip("Repeat (Off) - Click to repeat all")
        elif repeat_mode == "all":
            self.repeat_btn.setIcon(self._get_icon("repeat_active.svg"))
            self.repeat_btn.setProperty("active", "true")
            self.repeat_btn.setToolTip("Repeat All (On) - Click to loop current track")
        elif repeat_mode == "one":
            self.repeat_btn.setIcon(self._get_icon("repeat_one.svg"))
            self.repeat_btn.setProperty("active", "true")
            self.repeat_btn.setToolTip("Loop Track (Active) - Continuously loops this song")
        self.repeat_btn.style().polish(self.repeat_btn)

    def _on_scrub_started(self):
        self._is_scrubbing = True

    def _on_scrub_moved(self, value):
        self.cur_time_label.setText(format_duration(value / 1000.0))

    def _on_scrub_finished(self, value):
        self._is_scrubbing = False
        self.seek_requested.emit(value)

    def _open_edit_dialog(self):
        if not self.current_track:
            return
        dlg = EditTrackDialog(self.current_track, self)
        dlg.track_updated.connect(self._on_track_edited)
        dlg.exec()

    def _on_track_edited(self, updated_track: dict):
        self.set_track_info(updated_track)
        self.track_updated.emit(updated_track)
