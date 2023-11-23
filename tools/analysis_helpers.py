# Written by Zachariah Eberle zachariah.eberle@gmail.com

import numpy as np
from glob import glob
from tools.bhm import bhm_analyser
import tools.parser as parser
import tools.calibration as calib
import tools.plotting as plotting
import tools.commonVars as commonVars
from tools.get_run_info import *
import pandas as pd
from copy import deepcopy
import traceback
import time
from datetime import datetime
from tkinter import messagebox
import os
from urllib.error import URLError
import subprocess

"""
Various helper functions needed for both no gui and gui analysis files. These
functions are placed in here to prevent redundancy
"""
def mkdir(path):
    try:
        os.mkdir(path)
    except:
        pass

def askyesno(message, title=""):
    if commonVars.root:
        return messagebox.askyesno(title, message)
       
    else:
        answer = "a"
        while answer.lower() != "y" and answer.lower() != "n":
            answer = input(f"{message} (y/n): ")
        if answer.lower() == "y":
            response = True
        else:
            response = False
        return response


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

def get_run_orbit_ref(uHTR4, uHTR11):
    """
    Finds a run that is shared in both uHTR4 and uHTR11 that can be best used for timing.
    This requires a run transition in the data and thus at least 2 runs for accurate timing,
    else timing could be off by anywhere from seconds to hours.
    Additionally, finds the lowest orbit value within that run to use as a reference point for timing.
    """
    all_runs = sorted(find_unique_runs(uHTR4, uHTR11))
    for i in range(1, len(all_runs)):
        if all_runs[i] in uHTR4.run and all_runs[i] in uHTR11.run: # Check if run transition exists in both files
            run = all_runs[i]
            break
        elif (all_runs[i] == all_runs[i-1]+1 and all_runs[i] in uHTR4.run and all_runs[i-1] in uHTR4.run) or \
             (all_runs[i] == all_runs[i-1]+1 and all_runs[i] in uHTR11.run and all_runs[i-1] in uHTR11.run): 
            # Else check if run transition is +1 within a single file
            run = all_runs[i]
            break

    # If above conditions are never met, inform user about inaccurate run time data and return min value
    else:
        if commonVars.root:
            messagebox.showinfo("Inaccurate run time data", 
                            "The program was unable to accurately determine an accurate run timestamp of the loaded runs, this is probably due to only one run being present in the data." +
                            " Loaded run time data will be off from UTC by anywhere between a few seconds to multiple hours.")
        else:
            print("The program was unable to accurately determine an accurate run timestamp of the loaded runs, this is probably due to only one run being present in the data." +
                    " Loaded run time data will be off from UTC by anywhere between a few seconds to multiple hours.")
        run = min(all_runs)
        
    min_orbit = min(*uHTR4.orbit[uHTR4.run==run], *uHTR11.orbit[uHTR11.run==run])
    return run, min_orbit

def get_run_info(run_cut):
    """
    Opens up the terminal/command line where the user will input their password to connect to cmsusr (via ssh) where get_run_time.py will be executed
    """
    mkdir("./cache")

    def get_runs_from_cut(run_cut):
        if run_cut == None:
            return commonVars.loaded_runs
        elif isinstance(run_cut, int):
            return [run_cut]
        else:
            return run_cut

    def get_run_time_ms(run):

        try:
            run_times = np.loadtxt("./cache/run_times.cache", dtype=np.uint64, delimiter=",") # Check if info exists in a local cache
            if not np.any(run_times.T[0]==run):
                raise FileNotFoundError
            else:
                run_time_ms = run_times[run_times.T[0]==run][0][1]
            
        except (FileNotFoundError, OSError):

            if not askyesno("In order to get accurate run time data for rate plots, a valid CMS User account is required."+\
                            " You can enter your credentials in the terminal used to launch this program, are you OK with this?",
                            title="Information Notice"):
                return 0
            
            run_time_ms, _ = query_run(run)

            with open("./cache/run_times.cache", "a") as fp:
                fp.write(f"{run},{run_time_ms}\n")

        return run_time_ms
    
    def get_lumi_info(runs):
        write_to_cache = True

        try:
            lumi_info = pd.read_csv("./cache/lumi_info.cache")
            if lumi_info.empty:
                raise FileNotFoundError
            
            elif not all([run in lumi_info["run"].to_numpy() for run in runs]):
                user_consent = askyesno("In order to compare BHM event rate data to CMS Luminosity, a valid LXPLUS account is required."+\
                                        " You can enter your credentials in the terminal used to launch this program, are you OK with this?",
                                        title="Information Notice")
                if not user_consent:
                    return None
                lumi_info = pd.concat((lumi_info, get_lumisections(runs))).drop_duplicates().reset_index(drop=True)
                
            else:
                write_to_cache = False

        except (FileNotFoundError, OSError):
            user_consent = askyesno("In order to compare BHM event rate data to CMS Luminosity, a valid LXPLUS account is required."+\
                                        " You can enter your credentials in the terminal used to launch this program, are you OK with this?",
                                        title="Information Notice")
            if not user_consent:
                return None
            lumi_info = get_lumisections(runs)

        finally:
            if write_to_cache:
                lumi_info.to_csv("./cache/lumi_info.cache") # This will overwrite old cache, be careful with this!

        lumi_info = lumi_info.dropna().query(f"run>={min(runs)} & run<={max(runs)}") # Get rid of rows with None entries and only select rows with relevant runs

        time_vals = lumi_info["time"].to_numpy()*1000 # convert to ms
        lumi_vals = lumi_info["delivered_lumi"].to_numpy() # In units of ub^-1

        lumi_bins = [time_vals[0]]
        delivered_lumi = [lumi_vals[0]]

        for i in range(len(time_vals)-1):

            # If we do not have lumi info for a large period (>25s), set delivered lumi to zero, and fill in missing lumi bins with 23.5s bins
            if time_vals[i+1] - time_vals[i] > 25000:
                lumi_bins.extend(np.arange(time_vals[i] + 23500, time_vals[i+1], 23500))
                delivered_lumi.extend([0]*len(np.arange(time_vals[i] + 23500, time_vals[i+1], 23500)))

            lumi_bins.append(time_vals[i+1])
            delivered_lumi.append(lumi_vals[i+1])
        
        return lumi_bins, delivered_lumi


    if commonVars.reference_run != 0:
        run = commonVars.reference_run
    else:
        return 0, None, None
    
    run_time_ms = get_run_time_ms(run)
    lumi_bins, delivered_lumi = get_lumi_info(get_runs_from_cut(run_cut))

    return run_time_ms, lumi_bins, delivered_lumi


def load_uHTR_data(data_folder_str):
    """
    Loads in uHTR data from the specified folder path.
    """
    def check_conversion_consent():
        """
        Checks if the user would like to convert their text files to binary files
        """
        consent = askyesno("uHTR.txt files found. Would you like to convert them into a new format which loads"+\
                           " significantly faster and uses less disk space? (Note, this will not erase the original files)",
                           title="Data Conversion Check")
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
    
    commonVars.reference_run, commonVars.reference_orbit = get_run_orbit_ref(uHTR4, uHTR11) # Must be done before clean_data()

    if len(uHTR4.run) > 0:
        uHTR4.clean_data()
    if len(uHTR11.run) > 0:
        uHTR11.clean_data()
    
    loaded_runs = find_unique_runs(uHTR4, uHTR11)

    return uHTR4, uHTR11, loaded_runs

def analysis(uHTR4, uHTR11, figure_folder, run_cut=None, custom_range=False, 
             plot_lego=False, plot_ch_events=False, start_time=0, manual_calib=None,
             lumi_bins=None, delivered_lumi=None):
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

    plotting.rate_plots(_uHTR4, _uHTR11, start_time=start_time, lumi_bins=lumi_bins, delivered_lumi=delivered_lumi)

    del _uHTR4 # removing temp variables
    del _uHTR11