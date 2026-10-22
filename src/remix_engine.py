"""
Remix and Sound Layering Engine for Sonora.
Allows mixing dynamic rhythm and instrument layers (Drum, Piano, Jazz, Classic, Custom)
over active track playback.
"""

import os
from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

from .resource_utils import get_resource_path


class SoundLayer(QObject):
    """An individual looping accompaniment audio layer."""

    def __init__(self, name: str, default_rel_path: str, parent=None):
        super().__init__(parent)
        self.name = name
        self.file_path = get_resource_path(default_rel_path)
        self.is_enabled = False
        self.volume = 50

        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
        self._output.setVolume(self.volume / 100.0)

        # Loop playback seamlessly
        self._player.mediaStatusChanged.connect(self._on_status_changed)

        if os.path.isfile(self.file_path):
            self._player.setSource(QUrl.fromLocalFile(self.file_path))

    def set_file_path(self, path: str):
        if os.path.isfile(path):
            self.file_path = path
            self._player.setSource(QUrl.fromLocalFile(path))

    def set_volume(self, val: int):
        self.volume = max(0, min(100, val))
        self._output.setVolume(self.volume / 100.0)

    def set_enabled(self, enabled: bool):
        self.is_enabled = enabled
        if not enabled:
            self._player.pause()

    def play(self):
        if self.is_enabled and os.path.isfile(self.file_path):
            self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()

    def _on_status_changed(self, status):
        # Auto-loop
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.is_enabled:
                self._player.setPosition(0)
                self._player.play()


class RemixEngine(QObject):
    """Coordinates ambient and rhythm layers with master playback."""

    state_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.layers: Dict[str, SoundLayer] = {
            "drum": SoundLayer("Drums", os.path.join("assets", "remix", "drum.wav"), self),
            "piano": SoundLayer("Piano", os.path.join("assets", "remix", "piano.wav"), self),
            "jazz": SoundLayer("Jazz", os.path.join("assets", "remix", "jazz.wav"), self),
            "classic": SoundLayer("Classic", os.path.join("assets", "remix", "classic.wav"), self),
            "custom": SoundLayer("Custom", os.path.join("assets", "remix", "drum.wav"), self)
        }

        self.custom_file_path: Optional[str] = None
        self.current_preset = "Original"

    def apply_preset(self, preset_name: str):
        """Apply a built-in or custom remix preset."""
        self.current_preset = preset_name

        if preset_name == "Original":
            for layer in self.layers.values():
                layer.set_enabled(False)

        elif preset_name == "Drums":
            self._set_exclusive_layer("drum", 60)

        elif preset_name == "Piano":
            self._set_exclusive_layer("piano", 65)

        elif preset_name == "Jazz":
            self._set_exclusive_layer("jazz", 60)

        elif preset_name == "Classic":
            self._set_exclusive_layer("classic", 60)

        self.state_changed.emit()

    def _set_exclusive_layer(self, active_key: str, vol: int):
        for k, layer in self.layers.items():
            if k == active_key:
                layer.set_volume(vol)
                layer.set_enabled(True)
            else:
                layer.set_enabled(False)

    def set_custom_file(self, file_path: str):
        """Set a user-provided audio file as the custom remix stem."""
        if os.path.isfile(file_path):
            self.custom_file_path = file_path
            self.layers["custom"].set_file_path(file_path)
            self.state_changed.emit()

    def sync_playback(self, is_playing: bool):
        """Sync layer playback with main player state."""
        for layer in self.layers.values():
            if layer.is_enabled:
                if is_playing:
                    layer.play()
                else:
                    layer.pause()
            else:
                layer.pause()

    def stop_all(self):
        for layer in self.layers.values():
            layer.stop()
