"""
Sonora Dark Theme Stylesheet (Spotify-inspired aesthetic).
"""

DARK_THEME_QSS = """
/* Global Window & Base Widgets */
QMainWindow, QDialog {
    background-color: #121212;
    color: #FFFFFF;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: transparent;
    color: #FFFFFF;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    outline: none;
}

/* Sidebar */
#SidebarWidget {
    background-color: #000000;
    border-right: 1px solid #1c1c1c;
    min-width: 220px;
    max-width: 260px;
}

#SidebarBrand {
    font-size: 18px;
    font-weight: 700;
    color: #FFFFFF;
    padding: 16px 16px 8px 16px;
    letter-spacing: -0.3px;
}

#SidebarNavButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #B3B3B3;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
    padding: 10px 16px;
    margin: 2px 8px;
}

#SidebarNavButton:hover {
    color: #FFFFFF;
    background-color: #181818;
}

#SidebarNavButton:checked, #SidebarNavButton[active="true"] {
    color: #FFFFFF;
    background-color: #242424;
}

#SidebarSectionLabel {
    color: #6a6a6a;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 14px 16px 6px 16px;
}

#AddFolderButton {
    background-color: #1a1a1a;
    border: 1px dashed #333333;
    border-radius: 8px;
    color: #E0E0E0;
    font-size: 12px;
    font-weight: 600;
    padding: 9px 12px;
    margin: 6px 12px;
}

#AddFolderButton:hover {
    background-color: #262626;
    border-color: #1DB954;
    color: #1DB954;
}

/* Header & Search Bar */
#HeaderWidget {
    background-color: #121212;
    padding: 12px 24px;
    border-bottom: 1px solid #1a1a1a;
}

#SearchInput {
    background-color: #242424;
    border: 1px solid transparent;
    border-radius: 20px;
    color: #FFFFFF;
    font-size: 13px;
    padding: 8px 16px;
    min-width: 280px;
}

#SearchInput:focus {
    border: 1px solid #535353;
    background-color: #2a2a2a;
}

#StatsLabel {
    color: #888888;
    font-size: 12px;
}

/* Track Table */
QTableWidget {
    background-color: #121212;
    border: none;
    gridline-color: transparent;
    selection-background-color: #2a2a2a;
    selection-color: #FFFFFF;
    color: #E0E0E0;
}

QTableWidget::item {
    padding: 6px 10px;
    border-radius: 4px;
    border-bottom: 1px solid #181818;
}

QTableWidget::item:hover {
    background-color: #1e1e1e;
}

QTableWidget::item:selected {
    background-color: #282828;
    color: #1DB954;
}

QHeaderView::section {
    background-color: #121212;
    color: #888888;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border: none;
    border-bottom: 1px solid #282828;
    padding: 8px 10px;
}

/* Bottom Player Dock */
#PlayerBarWidget {
    background-color: #181818;
    border-top: 1px solid #282828;
    min-height: 90px;
    max-height: 90px;
    padding: 0 16px;
}

#TrackTitleLabel {
    font-size: 13px;
    font-weight: 600;
    color: #FFFFFF;
}

#TrackArtistLabel {
    font-size: 11px;
    color: #A7A7A7;
}

#TrackArtistLabel:hover {
    color: #FFFFFF;
    text-decoration: underline;
}

#TimeLabel {
    font-size: 11px;
    color: #A7A7A7;
    font-family: 'Consolas', monospace;
    min-width: 42px;
}

/* Control Buttons */
#PlayPauseButton {
    background-color: #FFFFFF;
    border: none;
    border-radius: 20px;
    min-width: 40px;
    max-width: 40px;
    min-height: 40px;
    max-height: 40px;
    padding: 0px;
}

#PlayPauseButton:hover {
    background-color: #1ED760;
}

#ControlIconButton {
    background-color: transparent;
    border: none;
    border-radius: 16px;
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 6px;
}

#ControlIconButton:hover {
    background-color: #242424;
}

#ControlIconButton[active="true"] {
    background-color: rgba(29, 185, 84, 0.15);
}

/* Spotify Seek Slider with Signature Hover Line Expansion */
#SeekSlider {
    height: 20px;
}

#SeekSlider::groove:horizontal {
    height: 4px;
    background: #4d4d4d;
    border-radius: 2px;
}

#SeekSlider::sub-page:horizontal {
    background: #FFFFFF;
    border-radius: 2px;
}

#SeekSlider::handle:horizontal {
    background: transparent;
    border: none;
    width: 0px;
    height: 0px;
    margin: 0px;
}

#SeekSlider:hover::groove:horizontal {
    height: 6px;
    background: #535353;
    border-radius: 3px;
}

#SeekSlider:hover::sub-page:horizontal {
    background: #1DB954;
    border-radius: 3px;
}

#SeekSlider:hover::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #1DB954;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 7px;
}

/* Volume Slider with Hover */
#VolumeSlider {
    height: 20px;
}

#VolumeSlider::groove:horizontal {
    height: 4px;
    background: #4d4d4d;
    border-radius: 2px;
}

#VolumeSlider::sub-page:horizontal {
    background: #B3B3B3;
    border-radius: 2px;
}

#VolumeSlider::handle:horizontal {
    background: transparent;
    border: none;
    width: 0px;
    height: 0px;
    margin: 0px;
}

#VolumeSlider:hover::groove:horizontal {
    height: 5px;
    background: #535353;
    border-radius: 2.5px;
}

#VolumeSlider:hover::sub-page:horizontal {
    background: #1DB954;
    border-radius: 2.5px;
}

#VolumeSlider:hover::handle:horizontal {
    background: #FFFFFF;
    width: 12px;
    height: 12px;
    margin: -3.5px 0;
    border-radius: 6px;
}

/* Minimalist Scrollbars */
QScrollBar:vertical {
    background: #121212;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #333333;
    min-height: 24px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
    background: none;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    height: 0;
}

/* Context Menu */
QMenu {
    background-color: #282828;
    color: #FFFFFF;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 0;
}

QMenu::item {
    padding: 8px 24px;
    border-radius: 4px;
    margin: 1px 4px;
}

QMenu::item:selected {
    background-color: #3e3e3e;
    color: #1DB954;
}

QMenu::separator {
    height: 1px;
    background-color: #383838;
    margin: 4px 8px;
}

/* Standard Buttons & Inputs */
QPushButton#PrimaryBtn {
    background-color: #1DB954;
    color: #000000;
    border: none;
    border-radius: 18px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 700;
}

QPushButton#PrimaryBtn:hover {
    background-color: #1ed760;
}

QPushButton#SecondaryBtn {
    background-color: transparent;
    color: #FFFFFF;
    border: 1px solid #535353;
    border-radius: 18px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}

QPushButton#SecondaryBtn:hover {
    border-color: #FFFFFF;
    background-color: #1a1a1a;
}
"""
