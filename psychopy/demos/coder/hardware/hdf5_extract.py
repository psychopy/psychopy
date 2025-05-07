"""
This script reads an HDF5 eye-tracking data file, identifies trials based on specified 
start and end markers in the experiment messages, extracts gaze data for each trial,
and animates gaze movement over time in a 2D space.

The user can customize:
    - The path to the HDF5 file
    - The marker text used to indicate the start and end of trials

⚠️ If you get an error saying a package (like h5py, numpy, matplotlib) is missing:
In PsychoPy, go to:
    Tools > Plugins/Packages Manager > Packages
Then search for and install the missing package (e.g., "h5py", "matplotlib", "numpy").
"""

"""
This script reads an HDF5 eye-tracking data file, identifies trials based on specified 
start and end markers in the experiment messages, extracts gaze data for each trial,
and animates gaze movement over time in a 2D space.

The user can customize:
    - The path to the HDF5 file
    - The marker text used to indicate the start and end of trials
"""

# ==== USER INPUTS ====
HDF5_FILE = '823238_eyetracking_youtube_2025-05-01_10h34.25.036.hdf5'  # Path to HDF5 file
TRIAL_START_MARKER = 'BEGIN_SEQUENCE 3'#'trial_start'  # Marker text for start of trial
TRIAL_END_MARKER = 'DONE_SEQUENCE 3'#'trial_end'      # Marker text for end of trial
# ======================

import h5py
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

def extract_eye_data_in_trials(hdf5_path, start_marker, end_marker):
    """
    Extract gaze data for each trial based on custom trial start/end markers.

    Parameters:
        hdf5_path (str): Path to HDF5 file.
        start_marker (str): String identifying trial start in the message events.
        end_marker (str): String identifying trial end in the message events.

    Returns:
        List of dicts: Each dict contains time, gaze_x, and gaze_y arrays for one trial.
    """
    with h5py.File(hdf5_path, 'r') as f:
        # Dataset paths
        msg_path = 'data_collection/events/experiment/MessageEvent'
        eye_path = 'data_collection/events/eyetracker/MonocularEyeSampleEvent'

        # Load message times and text
        messages = f[msg_path]
        msg_times = messages['time'][:]
        msg_texts = messages['text'][:].astype(str)

        # Find trial start/end times using the provided marker strings
        trial_starts = msg_times[np.char.find(msg_texts, start_marker) != -1]
        trial_ends = msg_times[np.char.find(msg_texts, end_marker) != -1]

        if len(trial_starts) != len(trial_ends):
            raise ValueError("Mismatched number of trial start and end events")

        # Load eye tracking data
        eye_data = f[eye_path]
        eye_times = eye_data['time'][:]
        gaze_x = eye_data['gaze_x'][:]
        gaze_y = eye_data['gaze_y'][:]

        # Extract data between trial start and end times
        trials_gaze = []
        for start, end in zip(trial_starts, trial_ends):
            mask = (eye_times >= start) & (eye_times <= end)
            trial_gaze = {
                'start_time': start,
                'end_time': end,
                'time': eye_times[mask],
                'gaze_x': gaze_x[mask],
                'gaze_y': gaze_y[mask]
            }
            trials_gaze.append(trial_gaze)

        return trials_gaze

def animate_gaze(trial_data, trial_num, save_to_file=False):
    """
    Animate gaze positions over time for a single trial.

    Parameters:
        trial_data (dict): Dictionary with 'time', 'gaze_x', and 'gaze_y' keys.
        trial_num (int): Index of the trial (for labeling).
        save_to_file (bool): Whether to save the animation as an .mp4 video file.
    """
    x = trial_data['gaze_x']
    y = trial_data['gaze_y']
    t = trial_data['time']

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.5, 0.5)
    ax.set_title(f"Gaze Animation - Trial {trial_num}")
    ax.set_xlabel("Gaze X")
    ax.set_ylabel("Gaze Y")

    point, = ax.plot([], [], 'ro', markersize=5)  # Red dot to show gaze

    def init():
        point.set_data([], [])
        return point,

    def update(frame):
        point.set_data(x[frame], y[frame])
        return point,

    ani = animation.FuncAnimation(
        fig, update, frames=len(x),
        init_func=init, blit=True, interval=10
    )

    if save_to_file:
        ani.save(f'gaze_trial_{trial_num}.mp4', fps=60, extra_args=['-vcodec', 'libx264'])

    plt.show()

# ====== MAIN EXECUTION ======
if __name__ == '__main__':
    result = extract_eye_data_in_trials(HDF5_FILE, TRIAL_START_MARKER, TRIAL_END_MARKER)
    if not result:
        print("No valid trials found.")
    else:
        animate_gaze(result[0], trial_num=1, save_to_file=False)
