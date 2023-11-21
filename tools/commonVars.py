# Written by Rohith Saradhy rohithsaradhy@gmail.com
'''
Common Variables

'''
#folder where it will be saved...
folder_name=""

# tkinter root if applicable
root = None

# Where to put time information
TIME_DUMP_FILE = "./time_info.txt"
LOG_DUMP_FILE = "./log_info.txt"

# Global tracker of all available profilers
profilers = {}

# Global flag to check for possible data corruption
data_corrupted = False

# Global flag that indicates that we do not know which uHTR side data is coming from
unknown_side = False

# Most accurate references to UTC time in for our data (both the run and orbit number)
reference_run = 0
reference_orbit = 0

# currently loaded runs in the gui
loaded_runs = []