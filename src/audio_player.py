"""
Audio playback engine for Sonora using PyQt6 QtMultimedia.
"""

import os
import random
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayer(QObject):
    """Core audio controller managing playback, queues, shuffle, and repeat."""

    # Signals
    track_changed = pyqtSignal(dict)
    state_changed = pyqtSignal(bool)           # True if playing, False if paused/stopped
    position_changed = pyqtSignal(int, int)    # current_ms, duration_ms
    volume_changed = pyqtSignal(int)          # 0-100
    queue_updated = pyqtSignal()
    cover_art_updated = pyqtSignal(str)        # file_path

    def __init__(self, parent=None):
        super().__init__(parent)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)

        # State
        self.queue: List[Dict[str, Any]] = []
        self.current_index: int = -1
        self.is_shuffle: bool = False
        self.repeat_mode: str = "off"  # "off", "all", "one"
        self._shuffled_indices: List[int] = []
        self._shuffle_pos: int = 0
        self._is_seeking: bool = False

        # Connect internal QtMultimedia signals
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.mediaStatusChanged.connect(self._on_media_status_changed)

        # Initial volume
        self.set_volume(75)

    def set_volume(self, volume: int):
        """Set volume 0 to 100."""
        clamped = max(0, min(100, volume))
        # QtAudioOutput volume is 0.0 to 1.0 (linear scale)
        self._audio_output.setVolume(clamped / 100.0)
        self.volume_changed.emit(clamped)

    def get_volume(self) -> int:
        return int(round(self._audio_output.volume() * 100))

    def toggle_mute(self) -> bool:
        """Toggle mute, returns True if currently muted."""
        new_state = not self._audio_output.isMuted()
        self._audio_output.setMuted(new_state)
        return new_state

    def is_muted(self) -> bool:
        return self._audio_output.isMuted()

    def set_queue(self, tracks: List[Dict[str, Any]], start_index: int = 0):
        """Set the active playback queue and immediately play the starting index."""
        self.queue = list(tracks)
        if self.is_shuffle:
            self._generate_shuffled_order(start_index)
        else:
            self.current_index = start_index

        self.queue_updated.emit()
        if 0 <= start_index < len(self.queue):
            self.play_track_at_index(start_index)

    def _generate_shuffled_order(self, current_idx: int):
        """Build a randomized permutation with current_idx first."""
        indices = list(range(len(self.queue)))
        if current_idx in indices:
            indices.remove(current_idx)
            random.shuffle(indices)
            indices.insert(0, current_idx)
        else:
            random.shuffle(indices)
        self._shuffled_indices = indices
        self._shuffle_pos = 0

    def toggle_shuffle(self) -> bool:
        """Toggle shuffle state and return new state."""
        self.is_shuffle = not self.is_shuffle
        if self.is_shuffle and self.queue:
            self._generate_shuffled_order(self.current_index)
        return self.is_shuffle

    def cycle_repeat_mode(self) -> str:
        """Cycle repeat: off -> all -> one -> off."""
        modes = ["off", "all", "one"]
        idx = modes.index(self.repeat_mode)
        self.repeat_mode = modes[(idx + 1) % len(modes)]
        return self.repeat_mode

    def play_track_at_index(self, index: int):
        """Play a specific track in the queue."""
        if not self.queue or index < 0 or index >= len(self.queue):
            return

        self.current_index = index
        track = self.queue[index]
        file_path = track.get("file_path", "")

        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            self.next_track()
            return

        url = QUrl.fromLocalFile(file_path)
        self._player.setSource(url)
        self._player.play()
        self.track_changed.emit(track)

    def play(self):
        """Resume or start playing."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self._player.play()
        elif self.current_index >= 0 and self.current_index < len(self.queue):
            self.play_track_at_index(self.current_index)
        elif self.queue:
            self.play_track_at_index(0)

    def pause(self):
        """Pause playback."""
        self._player.pause()

    def toggle_play_pause(self):
        """Toggle play/pause."""
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.pause()
        else:
            self.play()

    def stop(self):
        """Stop playback completely."""
        self._player.stop()

    def next_track(self):
        """Advance to next track based on shuffle/repeat settings."""
        if not self.queue:
            return

        if self.is_shuffle:
            if not self._shuffled_indices:
                self._generate_shuffled_order(self.current_index)
            self._shuffle_pos += 1
            if self._shuffle_pos >= len(self._shuffled_indices):
                if self.repeat_mode == "all":
                    self._shuffle_pos = 0
                else:
                    return
            target_idx = self._shuffled_indices[self._shuffle_pos]
            self.play_track_at_index(target_idx)
        else:
            next_idx = self.current_index + 1
            if next_idx >= len(self.queue):
                if self.repeat_mode == "all":
                    next_idx = 0
                else:
                    return
            self.play_track_at_index(next_idx)

    def previous_track(self):
        """Return to previous track, or restart current track if played > 3 seconds."""
        if not self.queue:
            return

        current_pos = self._player.position()
        if current_pos > 3000:  # 3 seconds threshold
            self.seek(0)
            return

        if self.is_shuffle:
            if self._shuffled_indices and self._shuffle_pos > 0:
                self._shuffle_pos -= 1
                target_idx = self._shuffled_indices[self._shuffle_pos]
                self.play_track_at_index(target_idx)
            else:
                self.seek(0)
        else:
            prev_idx = self.current_index - 1
            if prev_idx < 0:
                if self.repeat_mode == "all":
                    prev_idx = len(self.queue) - 1
                else:
                    self.seek(0)
                    return
            self.play_track_at_index(prev_idx)

    def seek(self, position_ms: int):
        """Seek to a specific millisecond position with bounds clamping."""
        dur = self._player.duration()
        target = max(0, min(dur, position_ms) if dur > 0 else position_ms)
        self._player.setPosition(target)

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """Return currently playing track metadata dictionary."""
        if 0 <= self.current_index < len(self.queue):
            return self.queue[self.current_index]
        return None

    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    # Internal Callbacks
    def _on_position_changed(self, pos: int):
        duration = self._player.duration()
        self.position_changed.emit(pos, max(0, duration))

    def _on_duration_changed(self, duration: int):
        pos = self._player.position()
        self.position_changed.emit(pos, max(0, duration))

    def _on_playback_state_changed(self, state):
        is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self.state_changed.emit(is_playing)

    def _on_media_status_changed(self, status):
        # End of media reached
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.repeat_mode == "one":
                self._player.stop()
                self._player.setPosition(0)
                self._player.play()
            else:
                self.next_track()
