"""
Metadata extraction and cover art embedding module for Sonora audio player.
Supports MP3, FLAC, M4A, OGG, OPUS, WAV, AIFF, and WMA.
"""

import os
import io
import mimetypes
from typing import Optional, Dict, Any
from PIL import Image
import mutagen
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from mutagen.flac import FLAC, Picture as FLACPicture
from mutagen.mp4 import MP4, MP4Cover
from mutagen.oggvorbis import OggVorbis
import base64


SUPPORTED_EXTENSIONS = {
    ".mp3", ".flac", ".wav", ".m4a", ".aac",
    ".ogg", ".opus", ".wma", ".aiff", ".ape"
}


def format_duration(seconds: float) -> str:
    """Format seconds into MM:SS or HH:MM:SS format."""
    if not seconds or seconds < 0:
        return "00:00"
    total_seconds = int(seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_file_size(bytes_size: int) -> str:
    """Format bytes into readable MB/KB."""
    if bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.1f} KB"
    return f"{bytes_size / (1024 * 1024):.1f} MB"


class MetadataManager:
    """Handles extracting tags, durations, and album artwork, as well as embedding custom art."""

    @staticmethod
    def extract_metadata(file_path: str) -> Dict[str, Any]:
        """Extract title, artist, album, duration, and cover image from an audio file."""
        basename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(basename)[0]
        ext = os.path.splitext(basename)[1].lower()

        data: Dict[str, Any] = {
            "file_path": os.path.abspath(file_path),
            "filename": basename,
            "title": name_without_ext,
            "artist": "Unknown Artist",
            "album": "Unknown Album",
            "duration": 0.0,
            "duration_str": "00:00",
            "file_size": 0,
            "file_size_str": "0 MB",
            "has_cover": False,
            "extension": ext
        }

        try:
            size = os.path.getsize(file_path)
            data["file_size"] = size
            data["file_size_str"] = format_file_size(size)
        except OSError:
            pass

        audio = None
        try:
            audio = mutagen.File(file_path)
        except Exception:
            pass

        if audio is None and ext == ".mp3":
            try:
                audio = ID3(file_path)
            except Exception:
                pass

        if audio is not None:
            try:
                # Duration
                if hasattr(audio, "info") and hasattr(audio.info, "length") and audio.info.length:
                    data["duration"] = float(audio.info.length)
                    data["duration_str"] = format_duration(data["duration"])

                # Tags parsing
                tags = getattr(audio, "tags", audio)
                if tags:
                    title = None
                    artist = None
                    album = None

                    # Check for MP3 / ID3
                    if hasattr(tags, "getall"):
                        titles = tags.getall("TIT2")
                        artists = tags.getall("TPE1")
                        albums = tags.getall("TALB")
                        if titles:
                            title = str(titles[0])
                        if artists:
                            artist = str(artists[0])
                        if albums:
                            album = str(albums[0])

                    # Direct key access in ID3 dict
                    if not title and "TIT2" in tags:
                        title = str(tags["TIT2"])
                    if not artist and "TPE1" in tags:
                        artist = str(tags["TPE1"])
                    if not album and "TALB" in tags:
                        album = str(tags["TALB"])

                    # Check for Vorbis / MP4 / FLAC dict tags
                    if not title and "title" in tags:
                        title = str(tags["title"][0]) if isinstance(tags["title"], list) else str(tags["title"])
                    if not title and "\xa9nam" in tags:
                        title = str(tags["\xa9nam"][0])

                    if not artist and "artist" in tags:
                        artist = str(tags["artist"][0]) if isinstance(tags["artist"], list) else str(tags["artist"])
                    if not artist and "\xa9ART" in tags:
                        artist = str(tags["\xa9ART"][0])

                    if not album and "album" in tags:
                        album = str(tags["album"][0]) if isinstance(tags["album"], list) else str(tags["album"])
                    if not album and "\xa9alb" in tags:
                        album = str(tags["\xa9alb"][0])

                    if title and title.strip():
                        data["title"] = title.strip()
                    if artist and artist.strip():
                        data["artist"] = artist.strip()
                    if album and album.strip():
                        data["album"] = album.strip()

            except Exception:
                pass

        return data

    @staticmethod
    def get_album_art_bytes(file_path: str) -> Optional[bytes]:
        """Retrieve binary bytes of embedded cover art or local folder cover."""
        if not os.path.isfile(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()

        # 1. Try mutagen.File first
        audio = None
        try:
            audio = mutagen.File(file_path)
        except Exception:
            pass

        # Fallback for MP3 files if mutagen.File failed
        if audio is None and ext == ".mp3":
            try:
                audio = ID3(file_path)
            except Exception:
                pass

        if audio is not None:
            # Check for ID3 tags
            tags = getattr(audio, "tags", audio)
            if tags:
                try:
                    # Look for APIC frames
                    if hasattr(tags, "getall"):
                        apic_frames = tags.getall("APIC")
                        if apic_frames and hasattr(apic_frames[0], "data"):
                            return apic_frames[0].data

                    # Dict-style check for APIC keys
                    for key in tags.keys():
                        if str(key).startswith("APIC") and hasattr(tags[key], "data"):
                            return tags[key].data

                    # MP4 / M4A covr tag
                    if "covr" in tags and tags["covr"]:
                        covr = tags["covr"][0]
                        return bytes(covr)
                except Exception:
                    pass

            # FLAC pictures
            if hasattr(audio, "pictures") and audio.pictures:
                return audio.pictures[0].data

            # OGG pictures
            if hasattr(audio, "tags") and audio.tags and "metadata_block_picture" in audio.tags:
                try:
                    block = audio.tags["metadata_block_picture"][0]
                    pic = FLACPicture(base64.b64decode(block))
                    return pic.data
                except Exception:
                    pass

        # 2. Fallback to folder image (cover.jpg, folder.jpg, albumart.png, etc.)
        try:
            folder = os.path.dirname(file_path)
            candidate_names = [
                "cover.jpg", "cover.png", "cover.jpeg",
                "folder.jpg", "folder.png", "folder.jpeg",
                "album.jpg", "album.png", "albumart.jpg",
                "front.jpg", "front.png"
            ]
            for name in candidate_names:
                full_path = os.path.join(folder, name)
                if os.path.isfile(full_path):
                    with open(full_path, "rb") as f:
                        return f.read()
        except Exception:
            pass

        return None

    @classmethod
    def _prepare_image_bytes(cls, image_file_path: str):
        """Load, resize if needed, and format image bytes for embedding."""
        with Image.open(image_file_path) as img:
            img_format = "JPEG" if img.format in ("JPEG", "JPG") else "PNG"
            mime = "image/jpeg" if img_format == "JPEG" else "image/png"

            if img.width > 1200 or img.height > 1200:
                img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            if img.mode in ("RGBA", "P") and img_format == "JPEG":
                rgb_img = img.convert("RGB")
                rgb_img.save(buffer, format="JPEG", quality=92)
            else:
                img.save(buffer, format=img_format, quality=92 if img_format == "JPEG" else None)
            return buffer.getvalue(), mime

    @classmethod
    def _save_folder_cover(cls, audio_file_path: str, image_bytes: bytes):
        """Save cover.jpg to the audio file's folder so file managers display it."""
        try:
            folder = os.path.dirname(audio_file_path)
            if os.path.isdir(folder):
                dest = os.path.join(folder, "cover.jpg")
                with open(dest, "wb") as f:
                    f.write(image_bytes)
        except Exception as e:
            print(f"Warning: could not save folder cover.jpg: {e}")

    @classmethod
    def set_custom_album_art(cls, audio_file_path: str, image_file_path: str, save_to_folder: bool = True) -> bool:
        """
        Embed a custom image as album cover into the target audio file.
        Updates ID3 tags for MP3, Picture for FLAC, covr for M4A, or Vorbis block for OGG.
        Also writes cover.jpg to the song's parent folder.
        """
        if not os.path.isfile(audio_file_path) or not os.path.isfile(image_file_path):
            return False

        ext = os.path.splitext(audio_file_path)[1].lower()

        try:
            image_bytes, mime = cls._prepare_image_bytes(image_file_path)

            if save_to_folder:
                cls._save_folder_cover(audio_file_path, image_bytes)

            if ext == ".mp3":
                try:
                    audio = ID3(audio_file_path)
                except ID3NoHeaderError:
                    audio = ID3()

                audio.delall("APIC")
                audio.add(APIC(
                    encoding=3,  # UTF-8
                    mime=mime,
                    type=3,      # 3 is front cover
                    desc="Cover",
                    data=image_bytes
                ))
                audio.save(audio_file_path, v2_version=3)
                return True

            elif ext == ".flac":
                audio = FLAC(audio_file_path)
                pic = FLACPicture()
                pic.data = image_bytes
                pic.type = 3
                pic.mime = mime
                pic.desc = "Cover"
                audio.clear_pictures()
                audio.add_picture(pic)
                audio.save()
                return True

            elif ext in (".m4a", ".mp4", ".aac"):
                audio = MP4(audio_file_path)
                mp4_fmt = MP4Cover.FORMAT_JPEG if mime == "image/jpeg" else MP4Cover.FORMAT_PNG
                audio["covr"] = [MP4Cover(image_bytes, imageformat=mp4_fmt)]
                audio.save()
                return True

            elif ext in (".ogg", ".opus"):
                audio = OggVorbis(audio_file_path)
                pic = FLACPicture()
                pic.data = image_bytes
                pic.type = 3
                pic.mime = mime
                pic.desc = "Cover"
                encoded = base64.b64encode(pic.write()).decode("ascii")
                audio["metadata_block_picture"] = [encoded]
                audio.save()
                return True

            return False

        except Exception as exc:
            print(f"Error embedding cover art: {exc}")
            return False

    @classmethod
    def update_track_tags(
        cls,
        audio_file_path: str,
        title: str,
        artist: str,
        album: str,
        image_file_path: Optional[str] = None,
        save_to_folder: bool = True
    ) -> bool:
        """
        Permanently edit and save Title, Artist, Album, and optional Cover Art
        directly to the actual audio file on disk.
        """
        if not os.path.isfile(audio_file_path):
            return False

        ext = os.path.splitext(audio_file_path)[1].lower()
        title_str = title.strip()
        artist_str = artist.strip()
        album_str = album.strip()

        try:
            image_bytes = None
            mime = "image/jpeg"
            if image_file_path and os.path.isfile(image_file_path):
                image_bytes, mime = cls._prepare_image_bytes(image_file_path)
                if save_to_folder:
                    cls._save_folder_cover(audio_file_path, image_bytes)

            if ext == ".mp3":
                from mutagen.id3 import TIT2, TPE1, TALB
                try:
                    audio = ID3(audio_file_path)
                except ID3NoHeaderError:
                    audio = ID3()

                audio["TIT2"] = TIT2(encoding=3, text=title_str)
                audio["TPE1"] = TPE1(encoding=3, text=artist_str)
                audio["TALB"] = TALB(encoding=3, text=album_str)

                if image_bytes:
                    audio.delall("APIC")
                    audio.add(APIC(
                        encoding=3,
                        mime=mime,
                        type=3,
                        desc="Cover",
                        data=image_bytes
                    ))
                audio.save(audio_file_path, v2_version=3)
                return True

            elif ext == ".flac":
                audio = FLAC(audio_file_path)
                audio["title"] = [title_str]
                audio["artist"] = [artist_str]
                audio["album"] = [album_str]

                if image_bytes:
                    pic = FLACPicture()
                    pic.data = image_bytes
                    pic.type = 3
                    pic.mime = mime
                    pic.desc = "Cover"
                    audio.clear_pictures()
                    audio.add_picture(pic)
                audio.save()
                return True

            elif ext in (".m4a", ".mp4", ".aac"):
                audio = MP4(audio_file_path)
                audio["\xa9nam"] = [title_str]
                audio["\xa9ART"] = [artist_str]
                audio["\xa9alb"] = [album_str]

                if image_bytes:
                    mp4_fmt = MP4Cover.FORMAT_JPEG if mime == "image/jpeg" else MP4Cover.FORMAT_PNG
                    audio["covr"] = [MP4Cover(image_bytes, imageformat=mp4_fmt)]
                audio.save()
                return True

            elif ext in (".ogg", ".opus"):
                audio = OggVorbis(audio_file_path)
                audio["title"] = [title_str]
                audio["artist"] = [artist_str]
                audio["album"] = [album_str]

                if image_bytes:
                    pic = FLACPicture()
                    pic.data = image_bytes
                    pic.type = 3
                    pic.mime = mime
                    pic.desc = "Cover"
                    audio["metadata_block_picture"] = [base64.b64encode(pic.write()).decode("ascii")]
                audio.save()
                return True

            elif ext == ".wav":
                # Try ID3 chunk for WAV
                try:
                    from mutagen.id3 import TIT2, TPE1, TALB
                    try:
                        audio = ID3(audio_file_path)
                    except ID3NoHeaderError:
                        audio = ID3()
                    audio["TIT2"] = TIT2(encoding=3, text=title_str)
                    audio["TPE1"] = TPE1(encoding=3, text=artist_str)
                    audio["TALB"] = TALB(encoding=3, text=album_str)
                    if image_bytes:
                        audio.delall("APIC")
                        audio.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=image_bytes))
                    audio.save(audio_file_path)
                    return True
                except Exception:
                    return False

            return False

        except Exception as exc:
            print(f"Error updating track tags: {exc}")
            return False
