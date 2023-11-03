# Written by Zachariah Eberle zachariah.eberle@gmail.com

import numpy as np
from glob import glob
from tools.bhm import bhm_analyser
import tools.parser as parser
import tools.calibration as calib
import tools.plotting as plotting
import tools.commonVars as commonVars
import pandas as pd
from copy import deepcopy
import traceback
#from paramiko import SSHClient, AutoAddPolicy
import time
from datetime import datetime
from tkinter import messagebox
import os

"""
Various helper functions needed for both no gui and gui analysis files. These
functions are placed in here to prevent redundancy
"""

def find_folder_name(file_path):
    """
    Seperates out the final folder name from its entire file path name
    """
    return file_path.split("./data")[-1][1:]

def find_unique_runs(uHTR4, uHTR11):
    """
    Finds and identifies all runs that are present in the data
    """
    all_runs = np.concatenate((uHTR4.run, uHTR11.run))
    return np.unique(all_runs).astype(np.uint32)

def find_data():
    """
    Uses glob to find all folders present in ./data/ subdirectory of the script 
    """
    data_files = glob("./data/**/*.txt", recursive=True) + glob("./data/**/*.uhtr", recursive=True)
    data_folders = []
    for file in data_files:
        if os.stat(file).st_size != 0: # exclude directories that contain only zero length files
            data_folders.append(os.path.split(file)[0])
    data_folders = np.unique(np.asarray(data_folders))
    data_folders = data_folders[data_folders != "./data"]
    data_folders_names = [find_folder_name(folder) for folder in data_folders]
    data_folders_dict = {find_folder_name(folder) : folder for folder in data_folders}

    if len(data_folders) == 0:
        raise FileNotFoundError
    
    return data_folders, data_folders_names, data_folders_dict

def create_empty_bhm(uHTR):
    uHTR = bhm_analyser(uHTR=uHTR)

    uHTR.ch = np.empty(0,)
    uHTR.ampl = np.empty(0,)
    uHTR.tdc = np.empty(0,)
    uHTR.tdc_2 = np.empty(0,)
    uHTR.bx = np.empty(0,)
    uHTR.orbit = np.empty(0,)
    uHTR.run = np.empty(0,)
    uHTR.ch_mapped= np.empty(0,)

    return uHTR

# def get_start_time(username, password, run):
#     """
#     Uses a double ssh to get start time for rate plots through the OMS API,
#     must have access to lxplus and cmsusr. 
#     """
#     with SSHClient() as ssh: # lxplus connection

#         try:
#             ssh.set_missing_host_key_policy(AutoAddPolicy())
#             ssh.connect("lxplus.cern.ch", username=username, password=password) # ssh username@lxplus.cern.ch
#             if commonVars.root:
#                 commonVars.connection_label_var.set("Connecting to CMSUSR...")
#                 commonVars.connection_progress["value"] = 20
#         except Exception as err:
#             raise type(err)("Something went wrong with connection to LXPLUS!", *err.args)
            
#         try:
#             ssh_transport = ssh.get_transport()
#             ssh_channel = ssh_transport.open_channel("direct-tcpip", ("cmsusr.cern.ch", 22), ("lxplus.cern.ch", 22))
#         except Exception as err:
#             raise type(err)("Something went wrong with ssh tunnel between LXPLUS and CMS!", *err.args)
        
#         with SSHClient() as ssh2: # cmsusr connection
            
#             try:
#                 ssh2.set_missing_host_key_policy(AutoAddPolicy())
#                 ssh2.connect("cmsusr.cern.ch", username=username, password=password, sock=ssh_channel) # ssh username@cmsusr.cern.ch from lxplus
#                 if commonVars.root:
#                     commonVars.connection_label_var.set("Connection to CMSUSR OK!")
#                     commonVars.connection_progress["value"] = 40
#                     time.sleep(0.3) # Just so the user can see the message for a brief moment
#             except Exception as err:
#                 raise type(err)("Something went wrong with connection to CMS from LXPLUS!", *err.args)

#             try:
#                 if commonVars.root:
#                     commonVars.connection_label_var.set("Copying over files...")
#                     commonVars.connection_progress["value"] = 60
#                 with ssh2.open_sftp() as sftp: # adding temporary directory to add script to
#                     try:
#                         sftp.chdir("bhm_tmp")
#                     except IOError:
#                         sftp.mkdir("bhm_tmp")
#                         sftp.chdir("bhm_tmp")

#                     sftp.put("./tools/get_run_time.py", "./get_run_time.py") # Copies get_run_time.py from local machine and moves it to the cms machine
#             except Exception as err:
#                 raise type(err)("Something went wrong with copying get_run_time.py to CMS!", *err.args)

#             try:
#                 if commonVars.root:
#                     commonVars.connection_label_var.set("Getting run time data...")
#                     commonVars.connection_progress["value"] = 80
#                 stdin, stdout, stderr = ssh2.exec_command(f"/nfshome0/lumipro/brilconda3/bin/python3 ~/bhm_tmp/get_run_time.py {run}") 
#                 readout = stdout.read().decode()
#             except Exception as err:
#                 raise type(err)("Something went wrong when running get_run_time.py!", *err.args)
#             try:
#                 readout = int(readout)
#             except ValueError:
#                 pass

#     del stdin, stdout, stderr, ssh, ssh2, ssh_transport, ssh_channel # clean up
#     if commonVars.root:
#         commonVars.connection_label_var.set("Done!")
#         commonVars.connection_progress["value"] = 100
#         time.sleep(0.1) # Just so the user can see the message for but a moment
#     return readout

def error_handler(err):
    """
    Function that will write an error to error.log, ususally used when unknown errors have occured
    that I will inevitably have to debug
    """
    with open("error.log", "a") as fp:
        fp.write(f"[{datetime.now().isoformat(timespec='milliseconds', sep=' ')}]: ")
        fp.write(str(err).upper() + "\n")
        fp.write(traceback.format_exc() + "\n\n\n")

def run_handler(runs):
    """
    A text file will be generated in the figure
    folder that shows which runs were analysed
    """
    file_path = commonVars.folder_name + "/analysed_runs.txt"
    with open(file_path, "w") as fp:
        fp.write("List of all runs analysed\n")
        fp.write("-------------------------\n")
        for i, run in enumerate(runs):
            if (i+1) % 3 != 0:
                fp.write("{:^8} ".format(run))
            else:
                fp.write("{:^8}\n".format(run))
        

def load_uHTR_data(data_folder_str):
    """
    Loads in uHTR data from the specified folder path.
    """
    def check_conversion_consent():
        """
        Checks if the user would like to convert their text files to binary files
        """
        if commonVars.root:
            consent = messagebox.askyesno("Data Conversion Check", 
                "uHTR.txt files found. Would you like to convert them into a new format which loads significantly faster and uses less disk space? (Note, this will not erase the original files)")
        else:
            answer = "a"
            while answer.lower() != "y" and answer.lower() != "n":
                answer = input("uHTR.txt files found. Would you like to convert them into a new format which loads significantly faster and uses less disk space? (Note, this will not erase the original files) (y/n): ")
            if answer.lower() == "y":
                consent = True
            else:
                consent = False
        if consent:
            for file in glob(f"./data/{data_folder_str}/*.txt"):
                parser.txt_to_bin(file)

    def load_from_file(uHTR, files, data_type=None):
        """
        Handles the actual loading process and creating bhm_analyser objects
        """
        if data_type is None:

            if any([".uhtr" in file for file in files]):
                data_type = "binary"
                files = [file for file in files if ".uhtr" in file]

            else:
                data_type = "text"
        
        files = sorted(files)

        commonVars.data_corrupted = False

        def is_sorted(arr):
            """
            Checks if array is sorted
            """
            return np.all(arr[:-1] <= arr[1:])

        _uHTR = bhm_analyser(uHTR=f"{uHTR}")

        for i, file in enumerate(files): # this loads each uHTR file and will combine them into one object
            if i == 0: _uHTR.load_data(file, data_type)
            else:
                if data_type == "binary":
                    evt, ch, ampl, tdc, tdc_2, bx, orbit, run  = parser.parse_bin_file(file)

                elif data_type == "text":
                    evt, ch, ampl, tdc, tdc_2, bx, orbit, run  = parser.parse_text_file(file)
                
                else:
                    raise ValueError(f"Unknown data type: \"{data_type}\"")

                if not is_sorted(evt):
                    commonVars.data_corrupted = True

                try:
                    _uHTR.ch = np.append(_uHTR.ch, ch, axis=0)
                    _uHTR.ampl = np.append(_uHTR.ampl, ampl, axis=0)
                    _uHTR.tdc = np.append(_uHTR.tdc, tdc, axis=0)
                    _uHTR.tdc_2 = np.append(_uHTR.tdc_2, tdc_2, axis=0)
                    _uHTR.bx = np.append(_uHTR.bx, bx, axis=0)
                    _uHTR.orbit = np.append(_uHTR.orbit, orbit, axis=0)
                    _uHTR.run = np.append(_uHTR.run, run, axis=0)
                    _uHTR.ch_mapped = np.append(_uHTR.ch_mapped, ch.T[0]*10 + ch.T[1], axis=0)

                except AttributeError: # If i == 0 entry is empty, we need to create the bhm arrays first
                    _uHTR.load_data(file, data_type)
        
        num_loops = 0
        # Note, this assumes that uHTR*.txt files are named numerically in time (ie. uHTR4 -> uHTR4_1 -> uHTR4_2 -> ... etc)
        while not is_sorted(_uHTR.orbit) and not commonVars.data_corrupted and num_loops < 100:
            # If orbits aren't in order and evts are in order, an integer of orbits must have occured
            # Add 2^32-1 to orbit values that aren't in order and check if orbits are sorted, repeat until
            # all integer overflows have been accounted for (orbit dtype should be np.uint64)
            try:
                overflow_index = np.where((_uHTR.orbit[:-1] <= _uHTR.orbit[1:])==0)[0][0] + 1
                _uHTR.orbit = np.concatenate((_uHTR.orbit[0:overflow_index], _uHTR.orbit[overflow_index:] + 4_294_967_295))
            except IndexError:
                commonVars.data_corrupted = True
                break
            finally:
                num_loops += 1
        
        if num_loops >= 100: # If we are looping too many times, it's likely the data files aren't in order or the data is corrupted.
            commonVars.data_corrupted = True
            
        
        return _uHTR

    uHTR4 = create_empty_bhm("4")
    uHTR11 = create_empty_bhm("11")

    uHTR4_files = glob(f"./data/{data_folder_str}/uHTR4*.txt") + glob(f"./data/{data_folder_str}/uHTR_4*.txt") + \
                    glob(f"./data/{data_folder_str}/uHTR4*.uhtr") + glob(f"./data/{data_folder_str}/uHTR_4*.uhtr")
    
    uHTR11_files = glob(f"./data/{data_folder_str}/uHTR11*.txt") + glob(f"./data/{data_folder_str}/uHTR_11*.txt") + \
                    glob(f"./data/{data_folder_str}/uHTR11*.uhtr") + glob(f"./data/{data_folder_str}/uHTR_11*.uhtr")
    
    if not any([".uhtr" in file for file in uHTR4_files + uHTR11_files]) and len(uHTR4_files + uHTR11_files) > 0:
        check_conversion_consent()
    

    if len(uHTR4_files) > 0 and len(uHTR11_files) > 0: # Check for standard file format

        commonVars.unknown_side = False

        uHTR4 = load_from_file(uHTR="4", files=uHTR4_files)
        uHTR11 = load_from_file(uHTR="11", files=uHTR11_files)


    else: # Check for different known file naming schemes

        data_files =  glob(f"./data/{data_folder_str}/*.txt") + glob(f"./data/{data_folder_str}/*.uhtr")

        if not any([".uhtr" in file for file in data_files]) and len(data_files) > 0:
            check_conversion_consent()

        if all(["MINUS" in file or "PLUS" in file for file in data_files]): # Check for MINUS or PLUS naming scheme

            commonVars.unknown_side = False

            uHTR4_files = glob(f"./data/{data_folder_str}/*PLUS*.txt") + glob(f"./data/{data_folder_str}/*PLUS*.uhtr")
            uHTR11_files = glob(f"./data/{data_folder_str}/*MINUS*.txt") + glob(f"./data/{data_folder_str}/*MINUS*.uhtr")

            if len(uHTR4_files) > 0:
                uHTR4 = load_from_file(uHTR="4", files=uHTR4_files)
            if len(uHTR11_files) > 0:
                uHTR11 = load_from_file(uHTR="11", files=uHTR11_files)


        
        elif all(["MN" in file or "MF" in file  or "PN" in file or "PF" in file for file in data_files]): # Check for M or P naming scheme

            commonVars.unknown_side = False

            uHTR4_text_files = glob(f"./data/{data_folder_str}/*PF*.txt") + glob(f"./data/{data_folder_str}/*PN*.txt")
            uHTR11_text_files = glob(f"./data/{data_folder_str}/*MF*.txt") + glob(f"./data/{data_folder_str}/*MN*.txt")

            if len(uHTR4_text_files) > 0:
                uHTR4 = load_from_file(uHTR="4", data_type="text", files=uHTR4_text_files)
            if len(uHTR11_text_files) > 0:
                uHTR11 = load_from_file(uHTR="11", data_type="text", files=uHTR11_text_files)



        elif len(data_files) > 0: # Cannot determine consistent naming scheme, load everything in as uHTR4

            uHTR4 = load_from_file(uHTR="4", data_type="text", files=data_files)
            
            commonVars.unknown_side = True


        
        else: # If no files are found, raise error
            raise FileNotFoundError

    if len(uHTR4.run) > 0:
        uHTR4.clean_data()
    if len(uHTR11.run) > 0:
        uHTR11.clean_data()
    
    loaded_runs = find_unique_runs(uHTR4, uHTR11)

    return uHTR4, uHTR11, loaded_runs

def analysis(uHTR4, uHTR11, figure_folder, run_cut=None, custom_range=False, plot_lego=False, plot_ch_events=False, start_time=0, manual_calib=None):
    """
    Performs the data analysis given the current run selection and other plotting options
    """
    commonVars.folder_name = (f"figures/{figure_folder}")

    if uHTR4 is not None:
        uHTR4.create_figure_folder()
    if uHTR11 is not None:
        uHTR11.create_figure_folder()

    if run_cut == None:
        analysed_runs = find_unique_runs(uHTR4, uHTR11)
    elif isinstance(run_cut, int):
        analysed_runs = [run_cut]
    else:
        analysed_runs = run_cut

    run_handler(analysed_runs)

    if manual_calib:
        calib.ADC_CUTS = {detector : int(cuts["ADC Cut"]) for detector, cuts in manual_calib.items()}
        calib.TDC_PEAKS = {detector : int(cuts["TDC Peak"]) for detector, cuts in manual_calib.items()}
    else:
        calib.ADC_CUTS = calib.ADC_CUTS_v2
        calib.TDC_PEAKS = calib.TDC_PEAKS_v2

    _uHTR4 = deepcopy(uHTR4) # create copies so multiple analyses can be run without having to reload data
    _uHTR11 = deepcopy(uHTR11)

    if manual_calib:
        _uHTR4.analyse(reAdjust=False, run_cut=run_cut, custom_range=custom_range, plot_lego=plot_lego, plot_ch_events=plot_ch_events)
        _uHTR11.analyse(reAdjust=False, run_cut=run_cut, custom_range=custom_range, plot_lego=plot_lego, plot_ch_events=plot_ch_events)
    else:
        _uHTR4.analyse(run_cut=run_cut, custom_range=custom_range, plot_lego=plot_lego, plot_ch_events=plot_ch_events)
        _uHTR11.analyse(run_cut=run_cut, custom_range=custom_range, plot_lego=plot_lego, plot_ch_events=plot_ch_events)

    plotting.rate_plots(_uHTR4, _uHTR11, start_time=start_time)

    del _uHTR4 # removing temp variables
    del _uHTR11