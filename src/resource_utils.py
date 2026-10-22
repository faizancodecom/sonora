"""
Resource path resolution helper for both development and PyInstaller bundled environments.
"""

import sys
import os


def get_resource_path(*relative_parts: str) -> str:
    """Return the absolute path to a resource, handling PyInstaller _MEIPASS if bundled."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = getattr(sys, "_MEIPASS")
    else:
        # Repo root is one level above 'src'
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_dir, *relative_parts)


def get_icons_dir() -> str:
    """Return the directory containing SVG icons."""
    return get_resource_path("assets", "icons")


def get_icon_path(icon_name: str) -> str:
    """Return absolute path to a specific icon file."""
    return get_resource_path("assets", "icons", icon_name)
