# Written by Zachariah Eberle zachariah.eberle@gmail.com

import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter.filedialog import asksaveasfile, askopenfile
from PIL import Image, ImageTk
from threading import Thread
import tools.commonVars as commonVars
import tools.analysis_helpers as analysis_helpers
import tools.hw_info as hw_info
import tools.calibration as calib
from tools.parser import CorruptionError
from tools.tkinter_tools import *
import os
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json
import numpy as np


def gui():
    """
    Responsible for the entirety of the GUI of the analysis program. Handles
    visuals and all user inputs.
    """

    loaded_runs = list(range(300)) # Placeholder variable

    def change_run_display_box(display_box_id):
        """
        Changes which display is active based on the run selection input.
        """
        if display_box_id.get() == 0:
            raise_frame(AllRuns)
        elif display_box_id.get() == 1:
            raise_frame(IndividualRun)
        elif display_box_id.get() == 2:
            raise_frame(CustomRun)
        else:
            raise_frame(BlankFrame)
    
    def load_data():
        """
        Begins the process of loading in the uHTR data, calls a seperate thread
        to avoid issue with tkinter mainloop
        """
        data_folder_str = data_folder.get()
        if data_folder_str not in data_folders_names:
            data_status_message.set(f"{data_folder_str} not found in data folder.")
            return
        
        disable_widget(RunSelection)
        disable_widget(DataSelectionLabel)
        disable_widget(FolderLabel)
        data_load_button.state(["disabled"])
        analyse_button.state(["disabled"])
        show_figures_button.state(["disabled"])

        data_status_message.set("Loading uHTR Data, Please Wait...")
        loading_thread = Thread(target=load_data_thread, args=[data_folder_str], daemon=True)
        loading_thread.start()
    
    def load_data_thread(data_folder_str):
        """
        Loads in data from the specified folder
        """

        global uHTR4, uHTR11

        try:
            uHTR4, uHTR11, loaded_runs = analysis_helpers.load_uHTR_data(data_folder_str)

        except FileNotFoundError:
            data_status_message.set(f"uHTR files not found in {data_folder_str}. Please ensure the data files are present.")
        
        except CorruptionError as err:
            err = str(err)
            null = "\x00"
            data_status_message.set("Something went wrong loading uHTR data!")
            messagebox.showerror("Data Corruption Error", 
                                 f"Error! Data shows major signs of corruption and cannot be safely parsed: \n{err.replace(null, '')}")

        except Exception as err:
            analysis_helpers.error_handler(err)
            data_status_message.set("Something went wrong loading uHTR data!")
            messagebox.showerror("Error", "An unknown exception has occured! Traceback information has been written to error.log")
        
        else:
            #print(f"unique runs: {list(set(uHTR4.run).symmetric_difference(set(uHTR11.run)))}")
            loaded_data_folder.set(data_folder.get())

            if commonVars.data_corrupted:
                messagebox.showwarning("Possible Data Corruption", "Warning! Currently loaded data shows signs of possible data corruption!" + 
                    f" Please check for any abnormalities in text files and ensure that they are numbered correctly." 
                    f" If not loading from txt file, consider deleting uhtr files in {data_folder_str}, as these files may have been formed from corrupt data.")
            
            if commonVars.unknown_side:
                messagebox.showinfo("Unknown uHTR Side", "Data folder contains errantly named data files. As such, it cannot be determined" +
                                    " which side of the detector (+Z or -Z) the data comes from. All data will be assumed to be from uHTR4 (+Z).")

            update_runs(loaded_runs)
            data_status_message.set(f"Currently Loaded Data Folder: {data_folder_str}")

            enable_widget(RunSelection)
            analyse_button.state(["!disabled"])
            enable_widget(FolderLabel)

        finally:
            enable_widget(DataSelectionLabel)
            data_load_button.state(["!disabled"])

        return

    def update_runs(loaded_runs):
        """
        Updates all widgets that display what runs are currently present in the data
        """
        for item in show_all_runs.get_children():
            show_all_runs.delete(item)
        for run in loaded_runs:
            show_all_runs.insert("", END, values=run)
        individual_run_display_box["values"] = list(loaded_runs)
        custom_run_var.set(list(loaded_runs))
        commonVars.loaded_runs = loaded_runs
    
    def clear_selection(widget):
        if isinstance(widget, tk.Listbox):
            widget.selection_clear(0, "end")
        elif isinstance(widget, ttk.Treeview):
            for sel in widget.selection():
                widget.selection_remove(sel)
    
    def do_analysis():
        """
        Function responsible for triggering data analysis and plot production from tools
        """
        run_type = run_sel_var.get()
        custom_run = [int(custom_run_var.get()[i]) for i in custom_run_display_box.curselection()]
        plot_lego = bool(lego_check_var.get())
        plot_ch_events = bool(channel_event_check_var.get())
        if FolderLabel.winfo_ismapped():
            figure_folder = folder_name_var.get()
        else:
            figure_folder = None
        save_fig = not gui_only_check_var.get()
        loaded_data_folder_str = loaded_data_folder.get()
        custom_range = False

        if run_type == 0: # check which run selection options is chosen
            run_cut = None
        elif run_type == 1:
            try:
                individual_run = int(individual_run_var.get())
            except ValueError:
                return
            run_cut = individual_run
        elif run_type == 2:
            run_cut = custom_run
            custom_range = True
        else:
            return
        
        if run_cut == []: # if custom run is left empty, return and don't do the analysis
            return
        
        if figure_folder == "": # default folder name behavior
            if run_cut == None:
                figure_folder = f"{loaded_data_folder_str}_all_runs"
            elif isinstance(run_cut, list):
                figure_folder = f"{loaded_data_folder_str}_custom_runs"
            else:
                figure_folder = f"{loaded_data_folder_str}_run_{run_cut}"
            proceed = messagebox.askyesno("Default Figure Folder", f"No Figure folder was indicated, figures will be saved with the default folder name:\n./figures/{figure_folder}\n\nDo you wish to proceed?")
            if not proceed:
                return
            
        elif isinstance(figure_folder, str) and not figure_folder.replace("_", "").isalnum(): # is folder alphanumeric w/ underscores
            data_status_message.set("Please ensure folder names are alphanumeric with underscores as the only special character.")
            messagebox.showwarning("Folder Name Invalid", "Please ensure folder names are alphanumeric with underscores as the only special character.")
            return
        
        if data_cuts_check_var.get():
            manual_calib = {data_cuts_tree.item(item_id)["values"][0] : 
                            {"TDC Peak" : data_cuts_tree.item(item_id)["values"][1], 
                            "ADC Cut" : data_cuts_tree.item(item_id)["values"][2]} 
                            for item_id in data_cuts_tree.get_children()}
        else:
            manual_calib = None
        
        disable_widget(MainPage)
        data_status.state(["!disabled"])

        analysis_thread = Thread(target=do_analysis_thread, args=(figure_folder, run_cut, custom_range, plot_lego, plot_ch_events, manual_calib, save_fig), daemon=True)
        analysis_thread.start()

    def do_analysis_thread(figure_folder, run_cut, custom_range, plot_lego, plot_ch_events, manual_calib, save_fig):
        """
        Data analysis thread, sets up folder and cuts and analyses the data
        """
        try:
            erase_all_figures()

            # Grabbing info from OMS
            data_status_message.set("Grabbing CMS info...")
            start_time, lumi_bins, delivered_lumi, beam_status = analysis_helpers.get_run_info(run_cut)
            # Note: lumisection bins and delivered lumi are not enabled, work is currently being done to get this info

            # Main data analysis section
            if start_time is not None:
                data_status_message.set("Analysing and Plotting uHTR Data, Please Wait...")

                # Load time data into toolbars
                initialize_toolbars(start_time, lumi_bins)

                analysis_helpers.analysis(uHTR4, uHTR11, figure_folder, run_cut=run_cut, custom_range=custom_range, 
                                          plot_lego=plot_lego, plot_ch_events=plot_ch_events, start_time=start_time, 
                                          manual_calib=manual_calib, lumi_bins=lumi_bins, delivered_lumi=delivered_lumi,
                                          beam_status=beam_status, save_fig=save_fig)
            else:
                raise KeyboardInterrupt
            data_status_message.set("Loading figure window...")
            draw_all()

            if not plot_lego: # Hides optional plots if not selected
                FigurePage.hide(LegoPage)
            else:
                FigurePage.select(LegoPage)
            if not plot_ch_events:
                FigurePage.hide(ChannelEventsPage)
            else:
                FigurePage.select(ChannelEventsPage)

            FigurePage.select(ADCPage)
            fig_window.deiconify()
            if figure_folder is not None:
                data_status_message.set(f"Figures written to {os.getcwd()}/{commonVars.folder_name}")
            else:
                data_status_message.set(f"Analysis complete, figures drawn in figure window.")
        
        except KeyboardInterrupt:
            data_status_message.set(f"Currently Loaded Data Folder: {loaded_data_folder.get()}")
        
        except LookupError as err:
            data_status_message.set("Something went wrong with plotting and analysis!")
            messagebox.showerror("File Format Error", err)

        except Exception as err:
            data_status_message.set("Something went wrong with plotting and analysis!")
            analysis_helpers.error_handler(err)
            messagebox.showerror("Error", "An unknown exception has occured! Traceback information has been written to error.log")
        
        finally:
            enable_widget(MainPage)
            return
    
    def initialize_toolbars(start_time=0, lumi_bins=None):
        """
        Sets the minimum and maximum time values into the toolbars if they have
        a date/time entry in their settings panel
        """

        min_orbit = min(min(uHTR4.orbit, default=float("inf")), min(uHTR11.orbit, default=float("inf")))
        max_orbit = max(max(uHTR4.orbit, default=-float("inf")), max(uHTR11.orbit, default=-float("inf")))

        for toolbar in toolbar_list:
            if hasattr(toolbar, "start_time"):
                if lumi_bins is not None:
                    toolbar.start_time.set_time(min(min(lumi_bins), (min_orbit.astype(np.float64) - commonVars.reference_orbit)*3564*25*10**-6 + start_time))
                    toolbar.end_time.set_time(max(max(lumi_bins), (max_orbit.astype(np.float64) - commonVars.reference_orbit)*3564*25*10**-6 + start_time))
                else:
                    toolbar.start_time.set_time(0)
                    toolbar.end_time.set_time((max_orbit-min_orbit)*3564*25*10**-6)

    #@@@@@@@@@@@@@@@@@ BEGIN TKINTER SETUP @@@@@@@@@@@@@@@@@@@@

    # Root Window Properties
    root = tk.Tk()
    root.geometry("700x665")
    root.resizable(True, True)
    root.title("BHM Analysis")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    commonVars.root = root # allows other scripts to access root

    # Check for CMS icon file
    try:
        img_list = []
        for size in [8, 16, 32, 64, 128, 256, 512]:
            img = ImageTk.PhotoImage(Image.open(f"img/cms_logo/cms{size}.png"))
            img_list.append(img)
        root.wm_iconphoto(True, *img_list)
    except FileNotFoundError:
        messagebox.showinfo("Notice", "CMS icons were not found in the img subdirectory, using default icon...")
    except:
        messagebox.showinfo("Notice", "Something went wrong loading CMS icons, using default icon...")

    # Setting up global figures to attach plots to gui
    commonVars.adc_fig = Figure(figsize=(6,70), dpi=100)
    commonVars.adc_fig.subplots_adjust(left=0.06, bottom=0.01, right=0.964, top=0.996, wspace=0.242, hspace=0.282)
    commonVars.tdc_fig = Figure(figsize=(6,70), dpi=100)
    commonVars.tdc_fig.subplots_adjust(left=0.06, bottom=0.01, right=0.964, top=0.996, wspace=0.242, hspace=0.282)
    commonVars.tdc_stability_fig = Figure(figsize=(7, 6.18), dpi=100)
    commonVars.tdc_stability_fig.subplots_adjust(left=0.06, bottom=0.11, right=0.96, top=0.933, wspace=0.22, hspace=0.578)
    commonVars.occupancy_fig = Figure(figsize=(7, 2.7), dpi=100)
    commonVars.occupancy_fig.subplots_adjust(left=0.055, bottom=0.11, right=0.96, top=0.913)
    commonVars.rate_fig = Figure(figsize=(7, 2.625), dpi=100)
    commonVars.rate_fig.autofmt_xdate()
    commonVars.rate_fig.subplots_adjust(left=0.06, bottom=0.1, right=0.8, top=0.9, wspace=0.6, hspace=0.3)
    commonVars.lego_fig = Figure(dpi=100)
    commonVars.lego_fig.subplots_adjust(left=0.04, bottom=0.043, right=0.966, top=0.923, wspace=0.176)
    commonVars.ch_events_fig = Figure(dpi=100)
    commonVars.ch_events_fig.subplots_adjust(left=0.075, bottom=0.11, right=0.975, top=0.91)

    figure_list = [commonVars.adc_fig, 
                   commonVars.tdc_fig, 
                   commonVars.tdc_stability_fig, 
                   commonVars.occupancy_fig, 
                   commonVars.rate_fig, 
                   commonVars.lego_fig,
                   commonVars.ch_events_fig]

    # print(root.winfo_screenwidth())
    # print(root.winfo_screenheight())
    # print(root.winfo_fpixels('1i'))

    #@@@@@@@@@@@@@@@@@ FONT SETUP @@@@@@@@@@@@@@@@@@@@@

    # Font Stuff
    default_font = commonVars.default_font = ("Segoe UI", 12)
    label_font = commonVars.label_font = ("Segoe UI", 15)
    s = ttk.Style()
    s.configure(".", font=default_font) # Applies default font to all widgets, can be manually changed for an individual widget later
    root.option_add('*TCombobox*Listbox.font', default_font) # combobox is dumb, this line is necessary to make drop down list have font applied
    s.configure("Treeview.Heading", font=default_font) # Treeview is also dumb, I don't understand why these things are necessary

    #@@@@@@@@@@@@@@@@ MAIN WINDOW FRAME CREATION @@@@@@@@@@@@@@@@@@@

    # Frames to hold various gui elements
    BasePage = ttk.Notebook(root)
    MainPage = tk.Frame(BasePage, width=700, height=600)#, bg="#00FF00")
    OptionsPage = tk.Frame(BasePage, width=700, height=600)

    # Adding frames to BasePage
    BasePage.add(MainPage, text="Analysis")
    BasePage.add(OptionsPage, text="Advanced Options")

    DataSelection = tk.Frame(MainPage)#, bg="#FF00FF")
    DataSelectionLabel = ttk.LabelFrame(DataSelection, text="BHM Data Folder Location")

    Seperator1 = ttk.Separator(MainPage)
    
    RunSelection = tk.Frame(MainPage)#, bg="#FF0000")

    # Placing Frames within window
    BasePage.grid(row=0, column=0, sticky=NSEW)
    DataSelection.pack(side=TOP, fill=X, expand=False, anchor=CENTER)
    DataSelection.grid_columnconfigure(0, weight=1)
    DataSelectionLabel.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=EW)
    DataSelectionLabel.grid_columnconfigure(0, weight=1)

    Seperator1.pack(side=TOP, fill=X, expand=False, pady=5)
    
    RunSelection.pack(side=TOP, fill=X, expand=False, anchor=CENTER)
    RunSelection.grid_rowconfigure(0, weight=1)
    RunSelection.grid_rowconfigure(1, weight=1)
    RunSelection.grid_columnconfigure(0, weight=1, uniform="RunSelection")
    RunSelection.grid_columnconfigure(1, weight=1, uniform="RunSelection")
    RunSelection.grid_columnconfigure(2, weight=1, uniform="RunSelection")

    OptionsPage.grid_columnconfigure(0, weight=1)
    OptionsPage.grid_columnconfigure(1, weight=1)

    #@@@@@@@@@@@@@@@@@ BEGIN MAIN PAGE @@@@@@@@@@@@@@@@@@@@



    #@@@@@@@@@@@@@@@@@ DATA SELECTION FRAME @@@@@@@@@@@@@@@@

    # Data Location
    try:
        data_folders, data_folders_names, data_folders_dict = analysis_helpers.find_data()
    except FileNotFoundError:
        data_folders, data_folders_names, data_folders_dict = ([], [], [])

    # Data Folder Selection 
    data_folder = StringVar()
    data_folder.set("<<No Data Selected>>")
    loaded_data_folder = StringVar() # Keeps track of currently loaded folder, used in do_analysis for folder naming
    loaded_data_folder.set("")
    data_selection_box = ttk.Combobox(DataSelectionLabel, textvariable=data_folder, font=default_font, values=data_folders_names, height=5)

    data_load_button = ttk.Button(DataSelection, text="Load Data", command=load_data)

    data_status_message = StringVar()
    if len(data_folders_names) >= 1: # empty checks
        data_status_message.set("No data loaded")
    else:
        data_status_message.set("No data folders located, please ensure to place data in a subdirectory of this script labeled 'data'.")
        data_load_button.state(["disabled"])
    
    data_status = ttk.Label(DataSelection, textvariable=data_status_message, background="#FFFFFF", relief="solid")

    
    # Placing Items in Data Selection Frame
    data_selection_box.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=EW)
    data_load_button.grid(row=1, column=0, ipadx=5, ipady=5, padx=10, pady=5, sticky=EW)
    data_status.grid(row=2, column=0, ipadx=5, ipady=5, padx=10, pady=5, sticky=EW)


    #@@@@@@@@@@@@@@@@@@@ RUN ANALYSIS FRAME @@@@@@@@@@@@@@@@@@@@@@

    #@@@@@@@@@@@@@@@@@@@ RUN SELECTION SUBFRAME @@@@@@@@@@@@@@@@@@@@@@

    # Run Selector 0 = all runs, 1 = single run, 2 = custom
    run_sel_var = IntVar()

    # Label for run selection section
    RunSelectionLabel = ttk.Label(RunSelection, text="Run Analysis Options", font=label_font)
    RunSelectionLabel.configure(anchor=CENTER)

    # Label for radio buttons
    RadioLabel = ttk.LabelFrame(RunSelection, text="Run Selection Type")

    # Buttons for choosing how to input desired runs
    run_options = ("All Runs", "Individual Run", "Custom")
    run1 = ttk.Radiobutton(RadioLabel, text=run_options[0], value=0, variable=run_sel_var, command=lambda : change_run_display_box(run_sel_var))
    run2 = ttk.Radiobutton(RadioLabel, text=run_options[1], value=1, variable=run_sel_var, command=lambda : change_run_display_box(run_sel_var))
    run3 = ttk.Radiobutton(RadioLabel, text=run_options[2], value=2, variable=run_sel_var, command=lambda : change_run_display_box(run_sel_var))

    run1.pack(fill=X, padx=5, pady=10)
    run2.pack(fill=X, padx=5, pady=10)
    run3.pack(fill=X, padx=5, pady=10)
    run_sel_var.set(3)

    # Run Selection Box
    RunSelectionBox = ttk.LabelFrame(RunSelection, text="Selected Run(s)")

    # I have to do an individual frame for each of the run selection options
    BlankFrame = tk.Frame(RunSelectionBox)#, bg="#123456")




    #@@@@@@@@@@@@@@@@@@ RUN DISPLAY SUBFRAME @@@@@@@@@@@@@@@@@@@@

    # All runs display
    AllRuns = tk.Frame(RunSelectionBox)#, bg="#000000")
    all_runs_display_box = ttk.Label(AllRuns, text="All Runs Selected!")
    show_all_runs = ttk.Treeview(AllRuns, columns=["all_runs"], show="headings", height=2, selectmode=NONE)
    show_all_runs.heading("all_runs", text="All Available Runs", anchor=W)
    show_all_runs.column("all_runs", anchor=W)
    for run in loaded_runs:
        show_all_runs.insert("", END, values=run)
    all_runs_scrollbar = ttk.Scrollbar(AllRuns, orient=VERTICAL, command=show_all_runs.yview)
    show_all_runs['yscrollcommand'] = all_runs_scrollbar.set

    # display for picking individual run
    IndividualRun = tk.Frame(RunSelectionBox)#, bg="#00FFFF")
    individual_run_var = StringVar()
    individual_run_var.set("Please select a run")
    individual_run_display_box = ttk.Combobox(IndividualRun, textvariable=individual_run_var, font=default_font, values=loaded_runs, height=4)

    # display for picking a custom set of runs
    CustomRun = tk.Frame(RunSelectionBox)#, bg="#0000FF")
    CustomRunSubFrame = tk.Frame(CustomRun)#, bg="#AAAAAF")
    custom_run_var = Variable()
    custom_run_var.set(loaded_runs)
    custom_run_display_box = tk.Listbox(CustomRunSubFrame, listvariable=custom_run_var, font=default_font, height=2, selectmode=MULTIPLE, activestyle=NONE)
    custom_scrollbar = ttk.Scrollbar(CustomRunSubFrame, orient=VERTICAL, command=custom_run_display_box.yview)
    custom_run_display_box['yscrollcommand'] = custom_scrollbar.set

    # Clear selection button
    clear_custom_sel = ttk.Button(CustomRun, text="Clear Selection", command=lambda : clear_selection(custom_run_display_box))



    #@@@@@@@@@@@@@@@@@@@@@@@ OPTIONAL PLOTS SUBFRAME @@@@@@@@@@@@@@@@@@@@@@@@@@

    # Optional Plots
    OptionalPlots = ttk.LabelFrame(RunSelection, text="Optional Plots")

    lego_check_var = BooleanVar()
    lego_check_var.set(0)
    lego_check = ttk.Checkbutton(OptionalPlots, text="Lego Plot", variable=lego_check_var, onvalue=1, offvalue=0)

    channel_event_check_var = BooleanVar()
    channel_event_check_var.set(0)
    channel_event_check = ttk.Checkbutton(OptionalPlots, text="Channel Event Plot", variable=channel_event_check_var, onvalue=1, offvalue=0)



    # Placing Items in Run Selection Frame
    RunSelectionLabel.grid(row=0, column=0, columnspan=3, ipadx=5, ipady=5, padx=5, pady=5, sticky=EW)

    RadioLabel.grid(row=1, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    RadioLabel.grid_propagate(False)

    RunSelectionBox.grid(row=1, column=1, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    RunSelectionBox.grid_columnconfigure(0, weight=1)
    RunSelectionBox.grid_rowconfigure(0, weight=1)

    BlankFrame.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)

    AllRuns.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    AllRuns.grid_columnconfigure(0, weight=1)
    AllRuns.grid_rowconfigure(0, weight=1)
    AllRuns.grid_rowconfigure(1, weight=3)
    all_runs_display_box.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=0, sticky=N+EW)
    show_all_runs.grid(row=1, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    all_runs_scrollbar.grid(row=1, column=1, sticky=NS)

    IndividualRun.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    IndividualRun.grid_columnconfigure(0, weight=1)
    IndividualRun.grid_rowconfigure(0, weight=1)
    individual_run_display_box.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=0, sticky=N+EW)

    CustomRun.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    CustomRun.grid_columnconfigure(0, weight=1)
    CustomRun.grid_rowconfigure(0, weight=1)
    CustomRunSubFrame.grid(row=0, column=0, sticky=NSEW)
    CustomRunSubFrame.grid_columnconfigure(0, weight=1)
    CustomRunSubFrame.grid_rowconfigure(0, weight=1)
    custom_run_display_box.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=0, sticky=NSEW)
    custom_scrollbar.grid(row=0, column=1, sticky=NS)
    clear_custom_sel.grid(row=1, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=S)

    raise_frame(BlankFrame)

    OptionalPlots.grid(row=1, column=2, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    lego_check.pack(fill=X, padx=5, pady=10)
    channel_event_check.pack(fill=X, padx=5, pady=10)


    #@@@@@@@@@@@@@@@@@ FOLDER SELECTION ENTRY @@@@@@@@@@@@@@@@@@@@@@

    # Folder Selection
    FolderLabel = ttk.LabelFrame(MainPage, text="Figure Folder Name")
    folder_name_var = StringVar()
    folder_name = ttk.Entry(FolderLabel, textvariable=folder_name_var, font=default_font)
    folder_name.bind("<Return>", lambda event : do_analysis()) # Bind pressing enter to start analysis

    # Placing items in Folder selection frame
    FolderLabel.pack(side=TOP, fill=X, ipadx=5, ipady=5, padx=5, pady=5)
    FolderLabel.grid_columnconfigure(0, weight=1)
    FolderLabel.grid_rowconfigure(0, weight=1)
    
    folder_name.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=EW)

    disable_widget(RunSelection)
    disable_widget(FolderLabel)

    #@@@@@@@@@@@@@@@@ ANALYSIS BUTTON @@@@@@@@@@@@@@@@@@@@@

    # Analysis Button
    analyse_button = ttk.Button(MainPage, text="Plot and Analyse Data", command=do_analysis, state="disabled")
    analyse_button.pack(side=TOP, fill=X, ipadx=5, ipady=5, padx=5, pady=5)

    # Figure window button
    show_figures_button = ttk.Button(MainPage, text="Open Figure Window", command=lambda : fig_window.deiconify(), state="disabled")
    show_figures_button.pack(side=TOP, fill=X, ipadx=5, ipady=5, padx=5, pady=5)

    raise_frame(MainPage)

    #@@@@@@@@@@@@@@@@ END MAIN PAGE @@@@@@@@@@@@@@@@@@@@@




    #@@@@@@@@@@@@@@@ BEGIN OPTIONS PAGE @@@@@@@@@@@@@@@@@@

    
    def toggle_widgets(widgets, bool_var):
        """
        Given a list of widgets, toggles the state of those widgets based on bool_var's state
        """
        for widget in widgets:
            if bool_var.get():
                widget.state(["!disabled"])
            else:
                widget.state(["disabled"])
    
    def load_data_cuts():
        """
        Loads in custom ADC/TDC cuts from a specifically formatted .json file
        """
        filetypes = [("JSON Files", "*.json")]
        try:
            with askopenfile(filetypes=filetypes, defaultextension=filetypes) as fp:
                json_object = json.load(fp)
                for json_list, item in zip(json_object.items(), data_cuts_tree.get_children()):
                    # Check if json is correctly formatted
                    if json_list[0] in hw_info.get_uHTR4_CMAP() or json_list[0] in hw_info.get_uHTR11_CMAP() and list(json_list[1].keys()) == ["TDC Peak", "ADC Cut"]:
                        values = (json_list[0], json_list[1]["TDC Peak"], json_list[1]["ADC Cut"])
                        data_cuts_tree.item(item, values=values)
                    else:
                        raise KeyError("Invalid data structure")
        except AttributeError as err:
            if str(err) == "__enter__": # occurs if the user cancels or closes the file select
                return
            raise err
        except json.decoder.JSONDecodeError or KeyError as err: # occurs if file isn't properly formatted as a .json
            messagebox.showerror("Error", f"Failed to parse {fp.name}: {err.args[0]}")

    def save_data_cuts():
        """
        Saves the values the user input into the data cuts treeview for custom data cuts into a .json file
        """
        filetypes = [("JSON Files", "*.json")]
        try:
            with asksaveasfile(filetypes=filetypes, defaultextension=filetypes, confirmoverwrite=True) as fp:
                json_dict = {data_cuts_tree.item(item_id)["values"][0] : 
                            {"TDC Peak" : data_cuts_tree.item(item_id)["values"][1], 
                            "ADC Cut" : data_cuts_tree.item(item_id)["values"][2]} 
                            for item_id in data_cuts_tree.get_children()}
                json_object = json.dumps(json_dict, indent=4)
                fp.write(json_object)
        except AttributeError as err:
            if str(err) == "__enter__": # occurs if the user cancels or closes the file select
                return
            raise err
    
    def set_analysis_type(state):
        """
        Changes whether or not we are saving figures to disk or only analysing data within the GUI.
        Disables/enables the Entry widget responsible for entering the folder name.
        """
        if state == True:
            FolderLabel.pack_forget()
        else:
            analyse_button.pack_forget()
            show_figures_button.pack_forget()
            # Unpack and repack everything since we need to reorder the widgets
            FolderLabel.pack(side=TOP, fill=X, ipadx=5, ipady=5, padx=5, pady=5)
            analyse_button.pack(side=TOP, fill=X, ipadx=5, ipady=5, padx=5, pady=5)
            show_figures_button.pack(side=TOP, fill=X, ipadx=5, ipady=5, padx=5, pady=5)
            


    #@@@@@@@@@@@@@@@@@@ DATA CUTS FRAME @@@@@@@@@@@@@@@@@@@@

    # Label frame for custom data run cut options
    DataCutsLabel = ttk.LabelFrame(OptionsPage, text="Custom Data Cuts")

    # Enable custom cuts check button
    data_cuts_check_var = BooleanVar()
    data_cuts_check_var.set(0)
    data_cuts_check = ttk.Checkbutton(DataCutsLabel, text="Enable custom data cuts", variable=data_cuts_check_var, 
                        command=lambda : toggle_widgets([data_cuts_tree, save_data_cuts_button, load_data_cuts_button], data_cuts_check_var))

    # Placing items into frame
    DataCutsLabel.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)
    data_cuts_check.pack(side=TOP, anchor=W, ipadx=5, ipady=5, padx=5, pady=5)



    #@@@@@@@@@@@@@@@@@@@@ DATA CUTS TREEVIEW SUBFRAME @@@@@@@@@@@@@@@@@@@@

    # Frame to hold treeview and its scrollbar
    DataCutsFrame = tk.Frame(DataCutsLabel)

    # Treeview of all detectors and their default ADC cuts and TDC peaks
    data_cuts_tree = EntryTreeview(DataCutsFrame, columns=["detector", "tdc_peak", "adc_cut"], show="headings", height=10, selectmode="browse")
    data_cuts_tree.heading("detector", text="Detector")
    data_cuts_tree.heading("tdc_peak", text="TDC Peak")
    data_cuts_tree.heading("adc_cut", text="ADC Cut")
    data_cuts_tree.column("detector", minwidth=100, width=100, anchor=CENTER)
    data_cuts_tree.column("tdc_peak", minwidth=100, width=100, anchor=CENTER)
    data_cuts_tree.column("adc_cut", minwidth=100, width=100, anchor=CENTER)
    for ch_name in hw_info.get_uHTR4_CMAP():
        data_cuts_tree.insert("", END, values=[ch_name, calib.TDC_PEAKS_v2[ch_name], calib.ADC_CUTS_v2[ch_name]])
    for ch_name in hw_info.get_uHTR11_CMAP():
        data_cuts_tree.insert("", END, values=[ch_name, calib.TDC_PEAKS_v2[ch_name], calib.ADC_CUTS_v2[ch_name]])
    data_cuts_tree.state(["disabled"])

    # Placing everything into subframe
    DataCutsFrame.pack(side=LEFT)
    # data_cuts_scrollbar.pack(side=RIGHT, fill=Y)
    data_cuts_tree.pack(side=LEFT, fill=BOTH, ipadx=0, ipady=0, padx=5, pady=5)

    #@@@@@@@@@@@@@@@@@ LOAD/SAVE SUBFRAME @@@@@@@@@@@@@@@@@@@@@@@@

    SaveLoadFrame = tk.Frame(DataCutsLabel)

    # Save button to save cuts to use at a later date
    save_data_cuts_button = ttk.Button(SaveLoadFrame, text="Save Data Cuts", state="disabled", command=save_data_cuts)

    # Load button to load in custom cut data
    load_data_cuts_button = ttk.Button(SaveLoadFrame, text="Load Data Cuts", state="disabled", command=load_data_cuts)


    # Placing everything into their frames
    SaveLoadFrame.pack(side=RIGHT, fill=Y)
    save_data_cuts_button.pack(side=TOP, anchor=N, ipadx=0, ipady=0, padx=5, pady=5)
    load_data_cuts_button.pack(side=TOP, anchor=N, ipadx=0, ipady=0, padx=5, pady=5)
    


    #@@@@@@@@@@@@@@@@@ GUI OPTIONS FRAME @@@@@@@@@@@@@@@@@@@

    # Label frame for gui settings
    GUIOptionsLabelFrame = ttk.LabelFrame(OptionsPage, text="GUI Options")

    # Enables/disables saving figures to disk/showing plots only in the GUI
    gui_only_check_var = BooleanVar()
    gui_only_check_var.set(0)
    gui_only_check = ttk.Checkbutton(GUIOptionsLabelFrame, text="Enable GUI Only\nAnalysis", variable=gui_only_check_var, onvalue=True, offvalue=False, 
                                     command=lambda : set_analysis_type(gui_only_check_var.get()))
    
    # Placing items into frame
    gui_only_check.pack(side=TOP, anchor=N, ipadx=5, ipady=5, padx=5, pady=5)
    GUIOptionsLabelFrame.grid(row=0, column=1, ipadx=5, ipady=5, padx=5, pady=5, sticky=NSEW)



    

    #@@@@@@@@@@@@@@@ BEGIN FIGURE WINDOW @@@@@@@@@@@@@@@@@@@

    def draw_all():
        for canvas in canvas_list:
            canvas.draw_idle()
    
    def erase_all_figures():
        """
        Removes all drawn axes from figures if they exist. We use this so that if multiple
        data sets are analysed, then figures don't corrupt each other. 
        Additionally reset toolbar memory
        """
        for fig in figure_list:
            for ax in fig.axes:
                ax.clear()
        for toolbar in toolbar_list:
            toolbar.update()

    #@@@@@@@@@@@@@@@ FIGURE WINDOW FRAME CREATION @@@@@@@@@@@@@@@@

    # window for displaying figures
    fig_window = tk.Toplevel(root)
    fig_window.geometry("1280x720")
    fig_window.resizable(True, True)
    fig_window.title("Figure Window")
    fig_window.columnconfigure(0, weight=1)
    fig_window.rowconfigure(0, weight=1)

    # Ensures closing the window doesn't destroy it completely
    fig_window.protocol("WM_DELETE_WINDOW", lambda : fig_window.withdraw())

    # Creating a tabbed index of the various graphs
    FigurePage = ttk.Notebook(fig_window)

    # Each frame will handle a different set of graphs
    ADCPage = tk.Frame(FigurePage)
    TDCPage = tk.Frame(FigurePage)
    TDCStabilityPage = tk.Frame(FigurePage)
    OccupancyPage = tk.Frame(FigurePage)
    RatePage = tk.Frame(FigurePage)
    LegoPage = tk.Frame(FigurePage)
    ChannelEventsPage = tk.Frame(FigurePage)

    # Adding each frame to notebook
    FigurePage.add(ADCPage, text="ADC Peaks")
    FigurePage.add(TDCPage, text="TDC Peaks")
    FigurePage.add(TDCStabilityPage, text="TDC Stability")
    FigurePage.add(OccupancyPage, text="Occupancy Plots")
    FigurePage.add(RatePage, text="Rate Plots")
    FigurePage.add(LegoPage, text="Lego Plots")
    FigurePage.add(ChannelEventsPage, text="Channel Event Plots")

    FigurePage.pack(side=TOP, ipadx=5, ipady=5, padx=5, pady=5, fill=BOTH, expand=True)



    #@@@@@@@@@@@@@@@@@@@@ EMBEDDING MATPLOTLIB PLOTS IN TKINTER FRAMES @@@@@@@@@@@@@@@@@@@@@@

    # ADC plots
    ADCPlotFrame = ScrollableFrame(ADCPage)
    ADCPlotFrame.pack(side=TOP, fill=BOTH, expand=True)

    adc_canvas = FigureCanvasTkAgg(commonVars.adc_fig, ADCPlotFrame.interior_frame)
    adc_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    adc_canvas.get_tk_widget().bind("<MouseWheel>", lambda event : ADCPlotFrame._on_mousescroll(event))
    adc_toolbar = ADCToolbar(adc_canvas, ADCPage, commonVars.adc_fig, pack_toolbar=False)
    adc_toolbar.update()
    adc_toolbar.pack(side=BOTTOM, fill=X, expand=False)


    # TDC Plots
    TDCPlotFrame = ScrollableFrame(TDCPage)
    TDCPlotFrame.pack(side=TOP, fill=BOTH, expand=True)

    tdc_canvas = FigureCanvasTkAgg(commonVars.tdc_fig, TDCPlotFrame.interior_frame)
    tdc_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    tdc_canvas.get_tk_widget().bind("<MouseWheel>", lambda event : TDCPlotFrame._on_mousescroll(event))
    tdc1_toolbar = TDCToolbar(tdc_canvas, TDCPage, commonVars.tdc_fig, pack_toolbar=False)
    tdc1_toolbar.update()
    tdc1_toolbar.pack(side=BOTTOM, fill=X, expand=False)


    # TDC Stability Plots
    tdc_stability_canvas = FigureCanvasTkAgg(commonVars.tdc_stability_fig, TDCStabilityPage)
    tdc_stability_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    tdc2_toolbar = TDCStabilityToolbar(tdc_stability_canvas, TDCStabilityPage, commonVars.tdc_stability_fig, pack_toolbar=False)
    tdc2_toolbar.update()
    tdc2_toolbar.pack(side=BOTTOM, fill=X, expand=False)


    # Occupancy Plots
    occupancy_canvas = FigureCanvasTkAgg(commonVars.occupancy_fig, OccupancyPage)
    occupancy_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    occupancy_toolbar = OccupancyToolbar(occupancy_canvas, OccupancyPage, commonVars.occupancy_fig, pack_toolbar=False)
    occupancy_toolbar.update()
    occupancy_toolbar.pack(side=BOTTOM, fill=X, expand=False)


    # Rate Plots
    rate_canvas = FigureCanvasTkAgg(commonVars.rate_fig, RatePage)
    rate_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    rate_toolbar = RateToolbar(rate_canvas, RatePage, commonVars.rate_fig, pack_toolbar=False)
    rate_toolbar.update()
    rate_toolbar.pack(side=BOTTOM, fill=X, expand=False)


    # Lego Plots
    lego_canvas = FigureCanvasTkAgg(commonVars.lego_fig, LegoPage)
    lego_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    lego_toolbar = LegoToolbar(lego_canvas, LegoPage, commonVars.lego_fig, pack_toolbar=False)
    lego_toolbar.update()
    lego_toolbar.pack(side=BOTTOM, fill=X, expand=False)


    # Channel Event Plots
    ch_events_canvas = FigureCanvasTkAgg(commonVars.ch_events_fig, ChannelEventsPage)
    ch_events_canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)
    ch_events_toolbar = ChannelEventsToolbar(ch_events_canvas, ChannelEventsPage, commonVars.ch_events_fig, pack_toolbar=False)
    ch_events_toolbar.update()
    ch_events_toolbar.pack(side=BOTTOM, fill=X, expand=False)

    commonVars.canvas_list = canvas_list = [adc_canvas, tdc_canvas, tdc_stability_canvas, occupancy_canvas, rate_canvas, lego_canvas, ch_events_canvas]
    commonVars.toolbar_list = toolbar_list = [adc_toolbar, tdc1_toolbar, tdc2_toolbar, occupancy_toolbar, rate_toolbar, lego_toolbar, ch_events_toolbar]

    fig_window.withdraw()

    root.mainloop()
