# PsychoPy Roadmap

last updated: 20 July 2026

## Purpose

This document provides a brief overview of recent and upcoming priorities for development by the core team at Open Science Tools for work in PsychoPy, PsychoJS and Pavlovia.

These goals are purely for your information and do not represent any binding agreement - we reserve the right to change the plans and outcomes at any time.

## Release cycles

PsychoPy and PsychoJS have, for some years, been built around a release cycle of 2 major release series per year (typically in February and July), labelled YYYY.1.n and YYYY.2.n where n indicates the bug-fix release within the series. Within a series we aim only to include minor tweaks to the code and no known changes incompatibilities other than to fix bugs. 

For example, the release 2026.1 series included 2026.1.0 (20 Feb 2026), with bug-fix releases 2026.1.1 (26 Feb), 2026.1.2 (19 March), and 2026.1.3 (30 March). 

The first release(s) after a major release are often subject to bugs - a lot of code typically gets updated between these and we can’t test all possible corner cases with our small team - so more cautious users would be recommended to use bug-fix versions x.x.2 or x.x.3 upwards.

Releases of PsychoPy and PsychoJS are always paired, whereas releases of Pavlovia are able to operate independently and are not currently subject to a fixed release cycle.

## Upcoming releases

### PsychoPy/JS 2027.1.0

Expected Feb 2027

*Expected highlights:*
  - 🐍 Improved webcam recording performance in lab-based (Python) experiments, with lower latency, better audio-visual synchrony and greater capacity (e.g. for multiple simultaneous camera recordings).
  - 🐍 Support for Python 3.14 and threaded hardware polling
    - Move movie rendering from ffpyplayer backend to PyAV due to lack of support in ffpyplayer
    - Add keyboard polling to thread in main process (not needing iohub)
  - 🐍🌐 PsychoPy encouraging a Project Structure to support better PsychoPy/Replovia?
  - 🐍🌐 Improved accessibility features within experiments - Text/letter/word spacing, Inter-line spacing, Magnifier (required for consultancy client)
  - 🐍 Add Parallel Port to Device Manager
  - 🌐 Improved Pavlovia Surveys

## Recent releases

### PsychoPy/JS 2025.1.0

Released 4 April 2025

Highlights:

  - 🐍 Added visual and audio timing validators to provide automated always-on timing tests
  - 🌐 Added the option for YouTube movies in MovieStim
  - 🐍 Added FaceAPI as a Builder Component (plugin)
  - 🐍 Added Sound Sensor Component for recordings from microphones or dedicated VoiceKey devices (e.g. Cedrus Riponda)

### PsychoPy/JS 2025.2.0

Released 6 Aug 2025

Highlights:

  - 🐍 Improved SerialComponent to give more control over what data is sent
  - 🐍 Device Manager to consolidate working with a single device at multiple points in a study or across studies
  - 🐍 Much better performance for movie playing and camera recordings (better buffering of frames)
  - 🐍 Revamped photometer classes for easier gamma calibration

### PsychoPy/JS 2026.1.0

Released 20 Feb 2026

Highlights:

  - First release of the PsychoPy Studio application - a complete rewrite of the user interface using modern web-frameworks (Svelte, JavaScript, Electron)
  - 🐍 Added live object tracking for webcam recordings
  - 🐍 Added support for displaying graphs (matplotlib) as stimuli in ImageStim
  - 🐍 Improved inter-frame interval timing for MacOS

### PsychoPy/JS 2026.2.0

Released 19 June 2026

Highlights:

  - 🐍 Native support for Apple Silicon Macs (rather than Rosetta emulation)
  - 🐍🌐 Textbox Component now supports inline styling
  - 🐍 Added a new HDF5 Marker Component for writing markers to a HDF5 file
  - Language translation and Accessibility improvements to PsychoPy Studio
  - Better support for classroom installations (customize virtual env locations)
