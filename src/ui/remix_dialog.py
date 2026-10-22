"""
Dialog for Sonora Remix & Sound Effects: Drum, Piano, Jazz, Classic, and Custom layer mixing.
"""

import os
from typing import Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSlider, QFileDialog, QFrame, QGridLayout,
    QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from ..resource_utils import get_icon_path


class RemixDialog(QDialog):
    """Allows user to enable/disable and mix Drum, Piano, Jazz, Classic, and Custom layers in real-time."""

    def __init__(self, remix_engine, audio_player, parent=None):
        super().__init__(parent)
        self.engine = remix_engine
        self.player = audio_player

        self.setWindowTitle("Remix & Audio Layers")
        self.setFixedSize(580, 520)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        # Header
        header_lbl = QLabel("Remix & Sound Layering")
        header_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF;")
        sub_lbl = QLabel("Blend dynamic rhythm and instrument layers in real-time over your music.")
        sub_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        root_layout.addWidget(header_lbl)
        root_layout.addWidget(sub_lbl)

        # Presets Row
        presets_frame = QFrame()
        presets_frame.setStyleSheet("background-color: #181818; border-radius: 8px; padding: 6px; border: 1px solid #282828;")
        presets_layout = QHBoxLayout(presets_frame)
        presets_layout.setSpacing(8)

        presets = [
            ("Original", "Original"),
            ("Drums", "Drums"),
            ("Piano", "Piano"),
            ("Jazz", "Jazz"),
            ("Classic", "Classic")
        ]

        self.preset_buttons: Dict[str, QPushButton] = {}
        for label, key in presets:
            btn = QPushButton(label)
            btn.setObjectName("SecondaryBtn")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #242424;
                    color: #FFFFFF;
                    border: 1px solid #333333;
                    border-radius: 14px;
                    padding: 6px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #303030;
                    border-color: #1DB954;
                }
                QPushButton[active="true"] {
                    background-color: #1DB954;
                    color: #000000;
                    font-weight: bold;
                    border: none;
                }
            """)
            btn.clicked.connect(lambda checked, k=key: self._on_preset_clicked(k))
            self.preset_buttons[key] = btn
            presets_layout.addWidget(btn)

        root_layout.addWidget(presets_frame)

        # Sound Layers Grid
        layers_frame = QFrame()
        layers_frame.setStyleSheet("background-color: #161616; border-radius: 8px; border: 1px solid #282828; padding: 12px;")
        layers_grid = QGridLayout(layers_frame)
        layers_grid.setHorizontalSpacing(16)
        layers_grid.setVerticalSpacing(14)

        self.layer_widgets: Dict[str, dict] = {}
        layer_configs = [
            ("drum", "Drums / Beat Groove", "drum.svg"),
            ("piano", "Piano Chords / Harmony", "library.svg"),
            ("jazz", "Jazz Upright Bass & Brush", "music.svg"),
            ("classic", "Classic Orchestral Strings", "classic.svg"),
        ]

        for row, (key, title, icon_name) in enumerate(layer_configs):
            layer = self.engine.layers[key]

            chk = QCheckBox(title)
            chk.setChecked(layer.is_enabled)
            chk.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(layer.volume)
            slider.setStyleSheet("""
                QSlider::groove:horizontal { height: 4px; background: #333; border-radius: 2px; }
                QSlider::sub-page:horizontal { background: #1DB954; border-radius: 2px; }
                QSlider::handle:horizontal { background: #FFF; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }
            """)

            vol_lbl = QLabel(f"{layer.volume}%")
            vol_lbl.setStyleSheet("color: #888888; font-size: 11px; min-width: 32px;")

            # Connect callbacks
            chk.toggled.connect(lambda state, k=key: self._on_layer_toggled(k, state))
            slider.valueChanged.connect(lambda val, k=key, l=vol_lbl: self._on_layer_vol_changed(k, val, l))

            layers_grid.addWidget(chk, row, 0)
            layers_grid.addWidget(slider, row, 1)
            layers_grid.addWidget(vol_lbl, row, 2)

            self.layer_widgets[key] = {"chk": chk, "slider": slider, "label": vol_lbl}

        root_layout.addWidget(layers_frame)

        # Custom Audio Stem / Loop Section
        custom_frame = QFrame()
        custom_frame.setStyleSheet("background-color: #181818; border-radius: 8px; border: 1px dashed #3a3a3a; padding: 10px;")
        custom_layout = QVBoxLayout(custom_frame)
        custom_layout.setSpacing(8)

        custom_top = QHBoxLayout()
        self.custom_chk = QCheckBox("Custom Audio Loop")
        self.custom_chk.setChecked(self.engine.layers["custom"].is_enabled)
        self.custom_chk.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 13px;")
        self.custom_chk.toggled.connect(lambda state: self._on_layer_toggled("custom", state))

        btn_browse_custom = QPushButton("Browse Audio File...")
        btn_browse_custom.setObjectName("SecondaryBtn")
        btn_browse_custom.clicked.connect(self._browse_custom_stem)

        custom_top.addWidget(self.custom_chk)
        custom_top.addStretch()
        custom_top.addWidget(btn_browse_custom)

        custom_bottom = QHBoxLayout()
        self.custom_path_lbl = QLabel(
            os.path.basename(self.engine.custom_file_path) if self.engine.custom_file_path else "No custom audio loaded (WAV, MP3, OGG supported)"
        )
        self.custom_path_lbl.setStyleSheet("color: #777777; font-size: 11px;")

        self.custom_slider = QSlider(Qt.Orientation.Horizontal)
        self.custom_slider.setRange(0, 100)
        self.custom_slider.setValue(self.engine.layers["custom"].volume)
        self.custom_vol_lbl = QLabel(f"{self.engine.layers['custom'].volume}%")
        self.custom_vol_lbl.setStyleSheet("color: #888888; font-size: 11px; min-width: 32px;")

        self.custom_slider.valueChanged.connect(
            lambda val: self._on_layer_vol_changed("custom", val, self.custom_vol_lbl)
        )

        custom_bottom.addWidget(self.custom_path_lbl, stretch=1)
        custom_bottom.addWidget(self.custom_slider)
        custom_bottom.addWidget(self.custom_vol_lbl)

        custom_layout.addLayout(custom_top)
        custom_layout.addLayout(custom_bottom)
        root_layout.addWidget(custom_frame)

        self.layer_widgets["custom"] = {"chk": self.custom_chk, "slider": self.custom_slider, "label": self.custom_vol_lbl}

        # Bottom Actions
        bottom_layout = QHBoxLayout()

        btn_mute_all = QPushButton("Disable All Layers")
        btn_mute_all.setObjectName("SecondaryBtn")
        btn_mute_all.clicked.connect(self._disable_all)

        btn_close = QPushButton("Done")
        btn_close.setObjectName("PrimaryBtn")
        btn_close.clicked.connect(self.accept)

        bottom_layout.addWidget(btn_mute_all)
        bottom_layout.addStretch()
        bottom_layout.addWidget(btn_close)

        root_layout.addLayout(bottom_layout)

        self._refresh_active_buttons()

    def _refresh_active_buttons(self):
        for key, btn in self.preset_buttons.items():
            btn.setProperty("active", "true" if key == self.engine.current_preset else "false")
            btn.style().polish(btn)

    def _on_preset_clicked(self, preset_key: str):
        self.engine.apply_preset(preset_key)
        # Update UI switches and sliders
        for k, widgets in self.layer_widgets.items():
            layer = self.engine.layers[k]
            widgets["chk"].blockSignals(True)
            widgets["chk"].setChecked(layer.is_enabled)
            widgets["chk"].blockSignals(False)

            widgets["slider"].blockSignals(True)
            widgets["slider"].setValue(layer.volume)
            widgets["slider"].blockSignals(False)
            widgets["label"].setText(f"{layer.volume}%")

        self._refresh_active_buttons()
        # Sync immediately with current player state
        self.engine.sync_playback(self.player.is_playing())

    def _on_layer_toggled(self, key: str, enabled: bool):
        self.engine.layers[key].set_enabled(enabled)
        self.engine.current_preset = "Custom"
        self._refresh_active_buttons()
        self.engine.sync_playback(self.player.is_playing())

    def _on_layer_vol_changed(self, key: str, val: int, lbl: QLabel):
        self.engine.layers[key].set_volume(val)
        lbl.setText(f"{val}%")

    def _browse_custom_stem(self):
        file_filter = "Audio Files (*.wav *.mp3 *.ogg *.flac *.m4a)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Audio Loop / Stem", "", file_filter)
        if path:
            self.engine.set_custom_file(path)
            self.custom_path_lbl.setText(os.path.basename(path))
            self.custom_chk.setChecked(True)
            self.engine.layers["custom"].set_enabled(True)
            self.engine.sync_playback(self.player.is_playing())

    def _disable_all(self):
        self._on_preset_clicked("Original")
