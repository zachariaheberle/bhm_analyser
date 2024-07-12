# Written by Rohith Saradhy rohithsaradhy@gmail.com and Zachariah Eberle zachariah.eberle@gmail.com
import numpy as np

'''
Common Variables

'''
#folder where it will be saved...
folder_name=""

# tkinter root if applicable
root = None

# Global flag to check for possible data corruption
data_corrupted = False

# Global flag that indicates that we do not know which uHTR side data is coming from
unknown_side = False

# Most accurate references to UTC time in for our data (both the run and orbit number)
reference_run = 0
reference_orbit = 0
start_time_utc_ms = 0

# currently loaded runs in the gui
loaded_runs = []

# bins used for bhm analysis, used for rate plot calculations
bhm_bins = {}

# Angle map for BHM detectors
angle_map_N = np.asarray( # Near side of angle_map
                [100.32, 112.91, 124.57, 138.20, 150.47, 162.74, 175.16, -173.02, -160.27, -148.77]
                )
angle_map_F = 180 - angle_map_N # Far side of angle_map, simple 180 degree reflection of near side

# angle_map is in order of (P/M)N01, (P/M)N02, ..., (P/M)F01, ..., (P/M)F10
angle_map = np.deg2rad(np.concatenate((angle_map_N, angle_map_F)))