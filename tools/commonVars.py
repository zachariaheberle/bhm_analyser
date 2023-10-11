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