# Sonora

Sonora is a high-performance desktop audio player built for managing, remixing, and listening to local music collections. Developed in Python using PyQt6 and QtMultimedia, it provides a fast, offline playback experience with a modern dark interface inspired by desktop streaming clients.

## Key Capabilities

- Broad Audio Format Support: Native decoding for MP3, FLAC, WAV, M4A, AAC, OGG, OPUS, AIFF, and WMA containers.
- Vector Icon Interface: Clean user interface built entirely with vector SVG assets and zero emoji characters.
- Shuffle Playback: Dedicated instant shuffle button to randomize the active library, folder, or playlist view and initiate immediate playback.
- Dynamic Sound Layers and Remix Engine: An integrated live audio mixer featuring ambient rhythm and instrument accompaniments (Drums, Piano, Jazz, Classic, and Custom user-loaded audio stems) with independent volume faders and preset configurations.
- Local Directory Ingestion: Scan and index single directories or nested directory trees without modifying existing file structures.
- Direct Physical Tag Editing: An integrated track editor allowing users to modify Title, Artist, and Album tags directly inside the physical audio files on disk (ID3v2 for MP3, Vorbis Comments for FLAC/OGG, and MP4 atoms for M4A).
- Embedded Artwork Management: Automatically displays embedded cover art or folder image files. Users can select and embed custom image files (PNG, JPG, WEBP) directly into the file tags and automatically generate `cover.jpg` within the song folder for system-wide album display.
- Precision Playback Scrubber: Smooth timeline seeking with signature hover expansion (line expands from 4px to 6px, dynamic green accent highlight, and circular grab handle) for responsive scrubbing without playback stutter.
- Loop and Repeat Engine: Three-stage repeat modes including Repeat Off, Repeat All (queue wrap-around), and Continuous Track Loop (repeats current song seamlessly).
- 100% Offline and Local: No external API calls, online scraping, or third-party web dependencies. Songs display native local tags or clean filenames when untagged.
- Persistent Library State: Automatically stores scanned directories, playlists, volume, and playback preferences locally in JSON format (`~/.sonora/library.json`).
- Single Standalone Executable: Pre-compiled into an isolated Windows executable (`build/Sonora.exe`) that executes completely on its own without requiring secondary folders, Python runtime, or pip dependencies.

## Technical Architecture

The codebase follows a modular design separating the presentation layer, audio pipeline, and metadata persistence:

- `main.py`: Application entry point with high-DPI scaling configuration.
- `src/resource_utils.py`: Resource path resolution helper ensuring reliable asset loading in both development and compiled binary states.
- `src/audio_player.py`: Wraps `PyQt6.QtMultimedia.QMediaPlayer` and `QAudioOutput` to manage stream states, position intervals, queue shuffling, and loop handling.
- `src/remix_engine.py`: Multi-track playback coordinator managing looping rhythm and instrument stems synchronized with master playback.
- `src/metadata_manager.py`: Extracts container-level audio tags and handles bidirectional binary cover art writing using Mutagen and Pillow.
- `src/playlist_manager.py`: Ingests disk directories, manages persistent state (`~/.sonora/library.json`), and provides playlist operations.
- `src/ui/`: Contains the presentation layer:
  - `main_window.py`: Coordinates the application layout, search filtering, shuffle dispatching, and shortcut handling.
  - `player_bar.py`: Fixed bottom dock housing album art previews, vector transport buttons, hover-expanding seek bar, volume attenuation, and remix launcher.
  - `sidebar.py`: Navigation drawer displaying library categories, indexed folders, and user-defined playlists.
  - `track_table.py`: High-density track listing with cached thumbnail rendering, active playback indicators, and contextual action menus.
  - `styles.py`: Complete dark palette stylesheet based on modern dark UI design tokens.
  - `dialogs.py`: Dedicated dialog windows for custom metadata/artwork editing (`EditTrackDialog`) and background directory scanning.
  - `remix_dialog.py`: Real-time mixer dialog allowing users to blend Drums, Piano, Jazz, Classic, and Custom audio loops over their music.

## System Prerequisites

- Operating System: Windows 10 / 11 (64-bit)
- Python: Version 3.10 or higher (only required when running from source)
- Audio Output: Standard system audio device

## Installation and Execution

### Method 1: Single Standalone Executable (Recommended)

1. Navigate to the `build/` directory in the repository.
2. Double-click `Sonora.exe`.
3. The executable runs as an independent single binary without requiring any surrounding folders, Python installation, or command-line execution.

### Method 2: Running from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/faizancodecom/sonora.git
   cd sonora
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # Windows Command Prompt
   .\venv\Scripts\activate.bat
   ```

3. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Launch the application:
   ```bash
   python main.py
   ```

## Complete Operating Manual

### Section 1: Music Library Ingestion

Sonora is designed to organize local files without duplicating, moving, or altering your existing storage structure.

1. Adding a Music Folder:
   - Click the "Add Folder..." button located in the left sidebar, or click the "Scan Folder..." button in the top navigation bar.
   - A directory selection dialog will appear. Choose the local folder where your audio files are stored.
   - Sonora performs an asynchronous scan of the selected directory and all its subfolders.
   - Supported extensions parsed automatically: `.mp3`, `.flac`, `.wav`, `.m4a`, `.aac`, `.ogg`, `.opus`, `.aiff`, `.wma`.
2. Reviewing Ingested Tracks:
   - All parsed tracks appear in "Your Library" with track number, album artwork thumbnail, title, artist, album name, and duration.
   - The left sidebar displays the folder name under the "MUSIC FOLDERS" section for instant one-click filtering.

### Section 2: Playback Controls and Transport Navigation

The bottom dock contains all transport controls rendered with crisp vector SVG icons:

1. Starting Playback:
   - Double-click any row in the track list to start playback immediately.
   - Alternatively, right-click any song and select "Play".
2. Play and Pause:
   - Click the circular central button in the bottom dock to toggle between Play and Pause.
   - Alternatively, press the Spacebar on your keyboard.
3. Next and Previous Navigation:
   - Click the Skip Next icon to jump to the subsequent track in the queue.
   - Click the Skip Previous icon to return to the beginning of the current song (if played past 3 seconds) or return to the previous track.
4. Precision Scrubber Seeking:
   - Hover your mouse cursor over the bottom horizontal timeline. The seek bar automatically expands from 4px to 6px thickness, illuminates in Spotify Green, and displays a circular grab handle.
   - Click anywhere along the line to seek instantly to that timestamp.
   - Click and drag the handle horizontally to scrub smoothly while monitoring the real-time timestamp display.
5. Volume Attenuation and Muting:
   - Drag the horizontal volume slider in the bottom right corner (0% to 100%).
   - Click the speaker icon to toggle mute and unmute instantly.

### Section 3: Shuffle and Loop Modes

Sonora includes full queue randomization and continuous loop modes:

1. Instant Shuffle Play:
   - Click the green "Shuffle Play" button located in the top toolbar.
   - Sonora will randomize the currently visible songs (whether in Your Library, a specific folder, or a playlist) and immediately start playing a random track.
2. Transport Shuffle Toggle:
   - Click the crossover arrows icon on the playback dock to enable or disable queue shuffling during playback.
3. Repeat and Loop Modes:
   - Click the Repeat button on the playback dock to cycle through the three operating states:
     - Repeat Off: Playback halts after the final track in the queue finishes.
     - Repeat All: The queue loops continuously from the beginning once the final track concludes.
     - Loop Track (Repeat One): The active song continuously replays from timestamp 00:00 in an uninterrupted loop.

### Section 4: Playlist Creation and Curation

Users can organize custom playlists and manage track assignments directly:

1. Method A: Right-Click Direct Addition (Fastest)
   - In Your Library or any folder view, right-click the song you wish to add.
   - Hover over the "Add to Playlist" submenu.
   - If you have existing playlists, click the target playlist name to add the song immediately.
   - If you want to create a new playlist on the fly, click "New Playlist...", enter a name, and press OK. The playlist is created and the track is added simultaneously.
2. Method B: Creating Empty Playlists via Sidebar
   - Under the "PLAYLISTS" header in the left sidebar, click the "+ New Playlist..." button.
   - Enter your desired playlist name (e.g., Chill, Workout, Classical).
   - The new playlist appears under the sidebar navigation.
   - Add songs to it anytime by right-clicking tracks and selecting "Add to Playlist".
3. Viewing Playlist Contents:
   - Click any playlist name in the sidebar. The center table updates to show only tracks assigned to that playlist.
   - Click "Shuffle Play" at the top to play the playlist in randomized order.
4. Removing Tracks from a Playlist:
   - Open the playlist from the sidebar.
   - Right-click the track you wish to remove and select "Remove from '<Playlist Name>'".
   - The song is removed from the playlist without deleting the file from your computer or general library.

### Section 5: Physical Tag and Cover Art Editing

Sonora writes metadata and artwork directly into physical file tags on disk, ensuring your edits remain intact across other players and operating systems:

1. Opening the Track Editor:
   - Right-click any track in the track table and select "Edit Track Info & Artwork...", or click the "Edit" button adjacent to the album art in the bottom player bar.
2. Editing Metadata Fields:
   - Modify the Title, Artist, or Album text fields.
   - If a song was previously untagged, Sonora populates the filename by default so you can refine it cleanly.
3. Changing Album Artwork:
   - Click the "Change Cover..." button below the artwork preview.
   - Select any image file (`.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`).
   - The preview updates immediately.
4. Generating System Folder Thumbnails:
   - Ensure the "Save as folder cover.jpg" checkbox is checked (enabled by default).
   - When saved, Sonora writes a standard `cover.jpg` file into the song's parent directory, enabling Windows Explorer to display the artwork on the folder icon.
5. Saving Changes:
   - Click "Save Changes to File".
   - Sonora applies container-specific tag writes (ID3v2 APIC for MP3, FLAC Picture for FLAC, MP4 covr for M4A, Vorbis metadata blocks for OGG).
   - The track list and player dock refresh instantly with the new information.

### Section 6: Remix and Audio Layering Engine

The Remix Engine allows users to layer ambient rhythm tracks, instrumental harmonies, or custom audio stems over their music in real-time:

1. Launching the Mixer:
   - Click the Remix icon located next to the volume slider in the bottom player dock.
2. Applying Sound Presets:
   - Select any preset button at the top of the dialog:
     - Original: Deactivates all accompaniment layers.
     - Drums: Introduces a dynamic lo-fi kick and shaker groove.
     - Piano: Layers warm acoustic piano chords and melodic texture.
     - Jazz: Blends upright bass walking lines with brushed percussion.
     - Classic: Adds an orchestral string pad layer.
3. Manual Layer Fader Control:
   - Toggle individual checkboxes for Drums, Piano, Jazz, and Classic on or off.
   - Adjust the horizontal slider (0% to 100%) for each layer to control its balance against the master track.
4. Custom Audio Loop Stems:
   - Check the "Custom Audio Loop" option.
   - Click "Browse Audio File..." and select any audio file (`.wav`, `.mp3`, `.ogg`, `.flac`) stored on your computer.
   - Sonora will loop your custom audio stem in synchronization with playback.
5. Playback Synchronization:
   - All active layers automatically play, pause, and stop in lockstep with the primary music player.

### Section 7: Real-Time Search and Filtering

1. Type any search keyword into the search bar at the top of the window.
2. Sonora filters visible tracks instantaneously across song titles, artist names, album titles, and filenames.
3. Clear the search input to restore the full view.

### Section 8: Keyboard Shortcuts

- Space: Play / Pause toggle
- Ctrl + Right Arrow: Skip to next track
- Ctrl + Left Arrow: Return to previous track / restart current song
- Ctrl + F: Focus the search input field

## Configuration and Storage

Sonora maintains all library paths, track metadata, and playlist indices in a local configuration file:

- Configuration Directory: `C:\Users\<User>\.sonora\`
- Database File: `C:\Users\<User>\.sonora\library.json`

The file preserves your volume preferences, shuffle state, repeat mode, indexed folder paths, and custom playlists across restarts.

## License

This project is licensed under the MIT License.

## Author

Faizan (faizancodecom)  
GitHub: [https://github.com/faizancodecom](https://github.com/faizancodecom)
