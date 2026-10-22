"""
Library, folder scanner, and playlist state persistence for Sonora.
"""

import os
import json
from typing import List, Dict, Any, Optional, Callable
from .metadata_manager import MetadataManager, SUPPORTED_EXTENSIONS


class PlaylistManager:
    """Manages the music library, saved playlists, and persistent state."""

    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            user_home = os.path.expanduser("~")
            config_dir = os.path.join(user_home, ".sonora")
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.data_file = os.path.join(self.config_dir, "library.json")

        self.folders: List[str] = []
        self.tracks: List[Dict[str, Any]] = []
        self.playlists: Dict[str, List[str]] = {}
        self.recently_played: List[str] = []
        self.settings: Dict[str, Any] = {
            "volume": 75,
            "shuffle": False,
            "repeat": "off",  # "off", "all", "one"
            "last_track": None,
            "last_position": 0
        }

        self.load()

    def load(self):
        """Load library and settings from disk."""
        if not os.path.isfile(self.data_file):
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.folders = data.get("folders", [])
                loaded_tracks = data.get("tracks", [])
                # Verify that files still exist on disk
                self.tracks = [t for t in loaded_tracks if os.path.isfile(t.get("file_path", ""))]
                self.playlists = data.get("playlists", {})
                self.recently_played = data.get("recently_played", [])
                self.settings.update(data.get("settings", {}))
        except Exception as e:
            print(f"Failed to load library data: {e}")

    def save(self):
        """Save current library, playlists, and settings to disk."""
        try:
            data = {
                "folders": self.folders,
                "tracks": self.tracks,
                "playlists": self.playlists,
                "recently_played": self.recently_played[:100],
                "settings": self.settings
            }
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save library data: {e}")

    def scan_folder(
        self,
        folder_path: str,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan a directory for all supported audio files and extract metadata.
        Returns newly added tracks.
        """
        folder_path = os.path.abspath(folder_path)
        if folder_path not in self.folders:
            self.folders.append(folder_path)

        existing_paths = {t["file_path"] for t in self.tracks}
        audio_files = []

        if recursive:
            for root, _, files in os.walk(folder_path):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        audio_files.append(os.path.join(root, f))
        else:
            for f in os.listdir(folder_path):
                full_path = os.path.join(folder_path, f)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        audio_files.append(full_path)

        total = len(audio_files)
        new_tracks = []

        for idx, file_path in enumerate(audio_files):
            if progress_callback:
                progress_callback(idx + 1, total, os.path.basename(file_path))

            if file_path in existing_paths:
                continue

            metadata = MetadataManager.extract_metadata(file_path)
            metadata["folder"] = folder_path
            self.tracks.append(metadata)
            existing_paths.add(file_path)
            new_tracks.append(metadata)

        self.save()
        return new_tracks

    def search_tracks(self, query: str) -> List[Dict[str, Any]]:
        """Filter tracks by matching title, artist, album, or filename."""
        if not query or not query.strip():
            return list(self.tracks)

        tokens = query.lower().strip().split()
        results = []

        for track in self.tracks:
            searchable = f"{track.get('title', '')} {track.get('artist', '')} {track.get('album', '')} {track.get('filename', '')}".lower()
            if all(token in searchable for token in tokens):
                results.append(track)

        return results

    def get_tracks_by_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """Get all tracks belonging to or located under a specific folder."""
        folder_norm = os.path.normpath(folder_path).lower()
        return [
            t for t in self.tracks
            if os.path.normpath(t.get("file_path", "")).lower().startswith(folder_norm)
        ]

    def create_playlist(self, name: str) -> bool:
        """Create a new named playlist."""
        name = name.strip()
        if not name or name in self.playlists:
            return False
        self.playlists[name] = []
        self.save()
        return True

    def delete_playlist(self, name: str) -> bool:
        """Remove a playlist."""
        if name in self.playlists:
            del self.playlists[name]
            self.save()
            return True
        return False

    def add_to_playlist(self, playlist_name: str, file_path: str) -> bool:
        """Add a song to a playlist."""
        if playlist_name not in self.playlists:
            return False
        if file_path not in self.playlists[playlist_name]:
            self.playlists[playlist_name].append(file_path)
            self.save()
            return True
        return False

    def remove_from_playlist(self, playlist_name: str, file_path: str) -> bool:
        """Remove a song from a playlist."""
        if playlist_name in self.playlists and file_path in self.playlists[playlist_name]:
            self.playlists[playlist_name].remove(file_path)
            self.save()
            return True
        return False

    def get_playlist_tracks(self, playlist_name: str) -> List[Dict[str, Any]]:
        """Get track metadata list for songs in a playlist."""
        paths = self.playlists.get(playlist_name, [])
        path_map = {t["file_path"]: t for t in self.tracks}
        results = []
        for p in paths:
            if p in path_map:
                results.append(path_map[p])
            elif os.path.isfile(p):
                # Dynamically extract if not in general library
                meta = MetadataManager.extract_metadata(p)
                results.append(meta)
        return results

    def record_recently_played(self, file_path: str):
        """Record song as recently played."""
        if file_path in self.recently_played:
            self.recently_played.remove(file_path)
        self.recently_played.insert(0, file_path)
        self.recently_played = self.recently_played[:50]
        self.save()

    def remove_track(self, file_path: str):
        """Remove track from library and all playlists."""
        self.tracks = [t for t in self.tracks if t["file_path"] != file_path]
        for name in list(self.playlists.keys()):
            if file_path in self.playlists[name]:
                self.playlists[name].remove(file_path)
        if file_path in self.recently_played:
            self.recently_played.remove(file_path)
        self.save()
