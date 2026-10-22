"""
Dialogs for Sonora: Track metadata & artwork editor, folder scanning progress.
"""

import os
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QProgressBar, QFrame,
    QCheckBox, QFormLayout
)
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QThread

from ..metadata_manager import MetadataManager, format_file_size, format_duration


class EditTrackDialog(QDialog):
    """
    Comprehensive track editor allowing the user to modify Title, Artist, Album,
    and Album Artwork directly within the physical audio file and folder.
    """

    track_updated = pyqtSignal(dict)  # Emits updated track dictionary

    def __init__(self, track: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.track = dict(track)
        self.selected_image_path: Optional[str] = None
        self._icons_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "icons")

        self.setWindowTitle("Edit Track Information")
        self.setFixedSize(620, 460)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(18)

        # Header Title
        header_lbl = QLabel("Edit Track & Artwork")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF;")
        root_layout.addWidget(header_lbl)

        # Main Body: Split Left (Artwork) and Right (Metadata Fields)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(24)

        # --- Left Column: Album Art ---
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        left_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(180, 180)
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_label.setStyleSheet("border-radius: 8px; background-color: #242424; border: 1px solid #333333;")
        self._load_current_cover()
        left_col.addWidget(self.cover_label)

        btn_choose_art = QPushButton("Change Cover...")
        btn_choose_art.setObjectName("SecondaryBtn")
        btn_choose_art.clicked.connect(self._browse_image)
        left_col.addWidget(btn_choose_art)

        self.chk_folder_cover = QCheckBox("Save as folder cover.jpg")
        self.chk_folder_cover.setChecked(True)
        self.chk_folder_cover.setStyleSheet("color: #A0A0A0; font-size: 11px;")
        left_col.addWidget(self.chk_folder_cover)

        body_layout.addLayout(left_col)

        # --- Right Column: Metadata Form ---
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        # Title
        lbl_title = QLabel("Title:")
        lbl_title.setStyleSheet("color: #B3B3B3; font-weight: 600; font-size: 12px;")
        self.input_title = QLineEdit(self.track.get("title", ""))
        self.input_title.setStyleSheet("background-color: #242424; border: 1px solid #383838; border-radius: 6px; padding: 7px 10px; color: #FFFFFF;")
        form_layout.addRow(lbl_title, self.input_title)

        # Artist
        lbl_artist = QLabel("Artist:")
        lbl_artist.setStyleSheet("color: #B3B3B3; font-weight: 600; font-size: 12px;")
        self.input_artist = QLineEdit(self.track.get("artist", ""))
        self.input_artist.setStyleSheet("background-color: #242424; border: 1px solid #383838; border-radius: 6px; padding: 7px 10px; color: #FFFFFF;")
        form_layout.addRow(lbl_artist, self.input_artist)

        # Album
        lbl_album = QLabel("Album:")
        lbl_album.setStyleSheet("color: #B3B3B3; font-weight: 600; font-size: 12px;")
        self.input_album = QLineEdit(self.track.get("album", ""))
        self.input_album.setStyleSheet("background-color: #242424; border: 1px solid #383838; border-radius: 6px; padding: 7px 10px; color: #FFFFFF;")
        form_layout.addRow(lbl_album, self.input_album)

        right_col.addLayout(form_layout)

        # File Info Details
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #181818; border-radius: 6px; padding: 8px; border: 1px solid #282828;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(8, 8, 8, 8)

        file_path = self.track.get("file_path", "")
        file_size = self.track.get("file_size_str", "0 MB")
        ext = self.track.get("extension", "").upper().replace(".", "")
        dur = self.track.get("duration_str", "00:00")

        lbl_tech = QLabel(f"Format: {ext}  •  Duration: {dur}  •  Size: {file_size}")
        lbl_tech.setStyleSheet("color: #888888; font-size: 11px;")
        info_layout.addWidget(lbl_tech)

        lbl_path = QLabel(f"Path: {file_path}")
        lbl_path.setToolTip(file_path)
        lbl_path.setStyleSheet("color: #666666; font-size: 10px; font-family: monospace;")
        info_layout.addWidget(lbl_path)

        right_col.addWidget(info_frame)
        right_col.addStretch()

        body_layout.addLayout(right_col, stretch=1)
        root_layout.addLayout(body_layout)

        # --- Bottom Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Changes to File")
        btn_save.setObjectName("PrimaryBtn")
        btn_save.clicked.connect(self._save_changes)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        root_layout.addLayout(btn_layout)

    def _load_current_cover(self):
        file_path = self.track.get("file_path", "")
        raw_art = MetadataManager.get_album_art_bytes(file_path)
        if raw_art:
            qimg = QImage.fromData(raw_art)
            if not qimg.isNull():
                pm = QPixmap.fromImage(qimg).scaled(
                    180, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
                self.cover_label.setPixmap(pm)
                return

        self.cover_label.setText("No Artwork")
        self.cover_label.setStyleSheet("color: #666666; font-size: 12px;")

    def _browse_image(self):
        file_filter = "Image Files (*.jpg *.jpeg *.png *.webp *.bmp)"
        img_path, _ = QFileDialog.getOpenFileName(self, "Select Cover Artwork Image", "", file_filter)
        if img_path:
            self.selected_image_path = img_path
            qimg = QImage(img_path)
            if not qimg.isNull():
                pm = QPixmap.fromImage(qimg).scaled(
                    180, 180, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation
                )
                self.cover_label.setPixmap(pm)

    def _save_changes(self):
        file_path = self.track.get("file_path", "")
        new_title = self.input_title.text().strip() or os.path.splitext(os.path.basename(file_path))[0]
        new_artist = self.input_artist.text().strip() or "Unknown Artist"
        new_album = self.input_album.text().strip() or "Unknown Album"
        save_folder = self.chk_folder_cover.isChecked()

        success = MetadataManager.update_track_tags(
            file_path,
            new_title,
            new_artist,
            new_album,
            image_file_path=self.selected_image_path,
            save_to_folder=save_folder
        )

        if success:
            self.track["title"] = new_title
            self.track["artist"] = new_artist
            self.track["album"] = new_album
            if self.selected_image_path:
                self.track["has_cover"] = True

            QMessageBox.information(
                self, "Tags Updated",
                "Successfully updated metadata and embedded artwork directly into the music file."
            )
            self.track_updated.emit(self.track)
            self.accept()
        else:
            QMessageBox.warning(
                self, "Update Warning",
                "Could not modify file tags on disk. Check file permissions or ensure the file is not currently locked."
            )


# Compatibility alias
class ChangeCoverDialog(EditTrackDialog):
    cover_updated = pyqtSignal(str)

    def __init__(self, track: dict, parent=None):
        super().__init__(track, parent)
        self.track_updated.connect(lambda t: self.cover_updated.emit(t.get("file_path", "")))


class ScannerWorker(QThread):
    """Background worker thread to scan folders and parse audio files without freezing UI."""

    progress = pyqtSignal(int, int, str)  # current, total, filename
    finished = pyqtSignal(list)

    def __init__(self, playlist_manager, folder_path, recursive=True):
        super().__init__()
        self.manager = playlist_manager
        self.folder_path = folder_path
        self.recursive = recursive

    def run(self):
        new_tracks = self.manager.scan_folder(
            self.folder_path,
            recursive=self.recursive,
            progress_callback=self._callback
        )
        self.finished.emit(new_tracks)

    def _callback(self, current, total, filename):
        self.progress.emit(current, total, filename)


class ScanProgressDialog(QDialog):
    """Modal dialog displaying folder scan progress."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scanning Music Directory")
        self.setFixedSize(440, 160)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.title_label = QLabel("Scanning files for audio and artwork...")
        self.title_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")

        self.file_label = QLabel("Initializing scan...")
        self.file_label.setStyleSheet("color: #888888; font-size: 11px;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #242424;
                border-radius: 4px;
                height: 8px;
                text-align: center;
                color: transparent;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        layout.addWidget(self.title_label)
        layout.addWidget(self.file_label)
        layout.addWidget(self.progress_bar)

    def update_progress(self, current: int, total: int, filename: str):
        if total > 0:
            pct = int((current / total) * 100)
            self.progress_bar.setValue(pct)
            self.title_label.setText(f"Scanning ({current}/{total})...")
        self.file_label.setText(filename)
