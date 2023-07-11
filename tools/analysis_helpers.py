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

"""
Various helper functions needed for both no gui and gui analysis files. These
functions are placed in here to prevent redundancy
"""

def find_folder_name(file_path):
    """
    Seperates out the final folder name from its entire file path name
    """
    return file_path.split("/")[-1].split("\\")[-1] # Jank workaround for windows and linux support

def find_unique_runs(uHTR4, uHTR11):
    """
    Finds and identifies all runs that are present in the data
    """
    all_runs = np.concatenate((uHTR4.run, uHTR11.run))
    return np.unique(all_runs)

def find_data():
    """
    Uses glob to find all folders present in ./data/ subdirectory of the script 
    """
    data_folders = glob("./data/*")
    data_folders_names = [find_folder_name(folder) for folder in data_folders]
    data_folders_dict = {find_folder_name(folder) : folder for folder in data_folders}

    if len(data_folders) == 0:
        raise FileNotFoundError
    
    return data_folders, data_folders_names, data_folders_dict

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
        fp.write(str(err).upper() + "\n")
        fp.write(traceback.format_exc() + "\n\n")

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
        uHTR4_files = glob(f"./data/{data_folder_str}/uHTR4*.txt")
        uHTR11_files = glob(f"./data/{data_folder_str}/uHTR11*.txt")

        if len(uHTR4_files) == 0 or len(uHTR11_files) == 0: # if files aren't found, return and catch error in analysis
            raise FileNotFoundError

        uHTR4 = bhm_analyser(uHTR="4")

        for i, file in enumerate(uHTR4_files): # this loads each uHTR file and will combine them into one object
            if i == 0: uHTR4.load_data(file)
            else:
                ch, ampl, tdc, tdc_2, bx, orbit, run  = parser.parse_text_file(file)

                uHTR4.ch = np.append(uHTR4.ch, ch, axis=0)
                uHTR4.ampl = np.append(uHTR4.ampl, ampl, axis=0)
                uHTR4.tdc = np.append(uHTR4.tdc, tdc, axis=0)
                uHTR4.tdc_2 = np.append(uHTR4.tdc_2, tdc_2, axis=0)
                uHTR4.bx = np.append(uHTR4.bx, bx, axis=0)
                uHTR4.orbit = np.append(uHTR4.orbit, orbit, axis=0)
                uHTR4.run = np.append(uHTR4.run, run, axis=0)
                uHTR4.ch_mapped = np.append(uHTR4.ch_mapped, ch.T[0]*10 + ch.T[1], axis=0)

        uHTR11 = bhm_analyser(uHTR="11")
        
        for i, file in enumerate(uHTR11_files): # this loads each uHTR file and will combine them into one object
            if i == 0: uHTR11.load_data(file)
            else:
                ch, ampl, tdc, tdc_2, bx, orbit, run  = parser.parse_text_file(file)

                uHTR11.ch = np.append(uHTR11.ch, ch, axis=0)
                uHTR11.ampl = np.append(uHTR11.ampl, ampl, axis=0)
                uHTR11.tdc = np.append(uHTR11.tdc, tdc, axis=0)
                uHTR11.tdc_2 = np.append(uHTR11.tdc_2, tdc_2, axis=0)
                uHTR11.bx = np.append(uHTR11.bx, bx, axis=0)
                uHTR11.orbit = np.append(uHTR11.orbit, orbit, axis=0)
                uHTR11.run = np.append(uHTR11.run, run, axis=0)
                uHTR11.ch_mapped = np.append(uHTR11.ch_mapped, ch.T[0]*10 + ch.T[1], axis=0)
        
        uHTR4.clean_data()
        uHTR11.clean_data()
        
        loaded_runs = find_unique_runs(uHTR4, uHTR11)

        return uHTR4, uHTR11, loaded_runs

def analysis(uHTR4, uHTR11, figure_folder, run_cut=None, custom_range=False, plot_lego=False, plot_ch_events=False, start_time=0, manual_calib=None):
    """
    Performs the data analysis given the current run selection and other plotting options
    """
    commonVars.folder_name = (f"figures/{figure_folder}")

    uHTR11.create_figure_folder()
    uHTR4.create_figure_folder()

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