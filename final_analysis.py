# Written by Zachariah Eberle zachariah.eberle@gmail.com

"""
Run this file as main to perform data analysis on BHM data.

Note: BHM data MUST be kept in a subdirectory titled 'data'
"""

from tools.libs import * # Importing all necessary libraries
from tools.analysis_helpers import *
import os
matplotlib.use('agg')


def nogui_analysis():
    """
    If tkinter doesn't exist or if no gui is desired, will run this analysis version instead
    """
    
    def data_folder_prompt():
        """
        Handles getting user information to select which data folder should be analysed.
        """
        valid_entry = False
        user_entry = input("\nPlease select a data folder to load.\nEnter the folder's name or its folder index: ")
        while valid_entry != True:
            if user_entry in data_folders_names: 
                    valid_entry = True
                    data_folder = user_entry

            else:
                try: # Check if value is an integer
                    user_index = int(user_entry)
                    data_folder = data_folders_names[user_index]
                    valid_entry = True

                except ValueError: # check if value is a float

                    try:
                        data_val = float(user_entry)
                        user_entry = input(f"\n{data_val} is not a valid index.\nPlease select an integer index between 0 and {len(data_folders) - 1} or type in the folder name: ")

                    except ValueError: # Fail case for data folder that does not exist
                        user_entry = input(f"\nFolder {user_entry} not in data folder.\nPlease select an index between 0 and {len(data_folders) - 1} or type in the folder name: ")
                        
                except IndexError: # Fail Case when index is out of bounds
                    user_entry = input(f"\nData folder with index {user_index} does not exist.\nPlease select an index between 0 and {len(data_folders) - 1} or type in the folder name: ")

        return data_folder
    
    def run_selection_prompt():
        """
        Handles getting user information to select which run(s) should be analysed.
        """
        valid_entry = False
        user_input = input("Please enter which run(s) you would like to analyse: ")
        while valid_entry != True:
            run_list = user_input.split(",")
            if len(run_list) == 1:
                try: # check if single run is an integer
                    run_selection = int(run_list[0])

                except ValueError:  
                    if user_input.lower() == "all": # check for 'all' case
                        valid_entry = True
                        run_selection = user_input
                    else: # Invalid input
                        user_input = input(f"{run_list[0]} is not a valid input, please re-enter which run(s) you would like to analyse: ")

                else: # ensure selected run is in data
                    if run_selection in loaded_runs:
                        valid_entry = True
                    else:
                        user_input = input(f"Run {run_selection} is not in data, please re-enter which run(s) you would like to analyse: ")

            else: # custom run selection
                try:
                    run_selection = [int(run) for run in run_list]

                except ValueError: # Invalid input
                    user_input = input(f"One or more values, please re-enter which run(s) you would like to analyse: ")
                
                else: # check to see if all runs choices are valid and in the data
                    if all([run in loaded_runs for run in run_selection]):
                        valid_entry = True
                    else:
                        user_input = input(f"One or more entered runs is not in data, please re-enter which run(s) you would like to analyse: ")
        return run_selection
    
    def lego_prompt():
        lego_str = input("\nWould you like a lego plot of the tdc and adc data? (y/n): ")
        plot_lego = None

        while lego_str.lower() and plot_lego == None:
            if lego_str.lower() == "y":
                plot_lego = True
            elif lego_str.lower() == "n":
                plot_lego = False
            else:
                lego_str = input("Invalid input, please enter 'y' or 'n'.\nWould you like a lego plot of the tdc and adc data? (y/n): ")
        
        return plot_lego

    def figure_folder_prompt(run_cut):
        valid_entry = False
        print("\nPlease input the folder name you would like to place figures in.")
        print("Figures will be stored in ./figures/(your input).\nBy default, folders will be placed under ./figures/(data folder name)(run information)")
        figure_folder = input("All names must be alphanumeric and underscores only. Press enter for default naming): ")
        
        while valid_entry != True:
            if figure_folder == "":
                
                if run_cut == None:
                    figure_folder = f"{data_folder}_all_runs"
                elif isinstance(run_cut, list):
                    figure_folder = f"{data_folder}_custom_runs"
                else:
                    figure_folder = f"{data_folder}_run_{run_cut}"

                valid_entry = True

            elif figure_folder.replace("_", "").isalnum():
                valid_entry = True

            else:
                figure_folder = input(f"Invalid file name, all names must be alphanumeric and underscores only.\nPlease re-input the folder name you would like to place figures in: ")

        return figure_folder

    print("BHM Analyser\n------------\n") # Title
    print("Currently Available Data Folders:\n")
    print("Folder Index | Data Folder Name\n--------------------------------") # Generates a table looking diagram of available data folders

    data_folders, data_folders_names, data_folders_dict = find_data()

    for i, folder in enumerate(data_folders_names):
        print("{:>12} | {:<}".format(i, folder))

    data_folder = data_folder_prompt() # Grabbing desired data folder

    try:
        print("\nLoading data, please wait...")
        uHTR4, uHTR11, loaded_runs = load_uHTR_data(data_folder) # Load uHTR data and grab valid runs

    except FileNotFoundError:
        input(f"uHTR files not found in {data_folder}. Please ensure the data files are present. (Press enter to exit)")
        exit()

    except Exception as err:
        input("Something went wrong loading uHTR data! (Press enter to exit)")
        error_handler(err)
        exit()

    if uHTR4 == None: # if no data
        print("No uHTR data found in {}.\nAre you ")

    print(f"Successfully loaded data from {data_folder}\n")
    print("Available Runs:\n")

    for i, run in enumerate(loaded_runs): # Print out available runs
        if (i+1) % 3 != 0:
            print("{:^8}".format(run), end=" ")
        else:
            print("{:^8}".format(run), end="\n")

    if len(loaded_runs) % 3 != 0:
        print("\n", end="")
    print("\nTo analyse a single run, simply type in one of the available runs.\nTo select all runs, simply type in 'all'.")
    print("Additionally, you can choose a custom set of runs by entering in a comma seperated list of the runs you wish to analyse")

    run_selection = run_selection_prompt() # Grab run(s) to analyse
    
    custom_range = False
    run_cut = run_selection

    if run_selection == "all":
        run_cut = None
    elif isinstance(run_selection, list):
        custom_range = True

    plot_lego = lego_prompt() # Optional plot

    figure_folder = figure_folder_prompt(run_cut)
    
    print("\nAnalysing and plotting data, please wait...")

    try:
        analysis(uHTR4, uHTR11, figure_folder, run_cut=run_cut, custom_range=custom_range, plot_lego=plot_lego) # primary analysis

    except Exception as err:
        error_handler(err)
        input("An unknown exception has occured! Traceback information has been written to error.log (Press enter to exit)")
        exit()

    print(f"Figures written to {os.getcwd()}/{commonVars.folder_name}")

        


if __name__ == "__main__":
    try:
        import tkinter as tk
        #import a as b
    except ImportError or ModuleNotFoundError:
        print("Tkinter could not be located, running no gui analysis...\n\n")
        nogui_analysis()
    else:
        import tools.tkinter_gui as gui
        gui.gui()
