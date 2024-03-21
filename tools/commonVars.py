# Written by Rohith Saradhy rohithsaradhy@gmail.com
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