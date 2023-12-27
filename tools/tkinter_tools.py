# Written by Zachariah Eberle zachariah.eberle@gmail.com
"""
The purpose of this script is to hold all of the custom tkinter tools / widgets that are built for this project and to hold useful tkinter functions
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import numpy as np
import pandas as pd
from threading import Thread

import tools.commonVars as commonVars
import tools.dt_conv as dt_conv
import tools.hw_info as hw_info
import tools.calibration as calib
import tools.plotting as plotting
import tools.analysis_helpers as analysis_helpers

def raise_frame(frame):
    """
    Raises a frame to be visible from hidden
    """
    frame.tkraise()
    
def disable_frame(frame):
    """
    Disables all buttons in the frame and in all child frames
    """
    for child in frame.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ("Frame", "Labelframe", "TFrame", "TLabelframe", "Canvas"):
            try:
                child.state(["disabled"])
            except:
                child.configure(state="disabled")
        else:
            disable_frame(child)

def enable_frame(frame):
    """
    Enables all buttons in the frame and in all child frames
    """
    for child in frame.winfo_children():
        wtype = child.winfo_class()
        if wtype not in ("Frame", "Labelframe", "TFrame", "TLabelframe", "Canvas"):
            try:
                child.state(["!disabled"])
            except AttributeError:
                child.configure(state="normal")
        else:
            enable_frame(child)

class ScrollableFrame(tk.Frame):
    """
    tk.Frame with an attached scrollbar that can scroll through a canvas. This is (currently) used for displaying either long lists of items
    or very large plots that require a scrollbar to view.
    """

    def __init__(self, master, orient="vertical", canvas_height=None, **kwargs):
        super().__init__(master, **kwargs)

        if orient == "vertical":
            canvas_side = "left"
            scrollbar_side = "right"
            scrollbar_fill = "y"
        elif orient == "horizontal":
            canvas_side = "top"
            scrollbar_side = "bottom"
            scrollbar_fill = "x"

        self.scrollbar = ttk.Scrollbar(self, orient=orient)
        self.scrollbar.pack(side=scrollbar_side, fill=scrollbar_fill, expand=False)
        self.canvas = tk.Canvas(self, height=canvas_height, bd=0, highlightthickness=0, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=canvas_side, fill="both", expand=True)
        self.canvas.bind('<Configure>', lambda event : self._configure_canvas(event))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.scrollbar.config(command=self.canvas.yview)

        self.interior_frame = tk.Frame(self.canvas)
        self.interior_frame_id = self.canvas.create_window(0, 0, window=self.interior_frame, anchor="nw")
        self.interior_frame.bind('<Configure>', lambda event : self._configure_interior(event))

    def _configure_canvas(self, event):
        """
        Updates the inner frame's width to fill the canvas
        """
        if self.interior_frame.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.interior_frame_id, width=self.canvas.winfo_width())
    
    def _configure_interior(self, event):
        """ 
        Updates the scrollbars to match the size of the inner frame
        """
        size = (self.interior_frame.winfo_reqwidth(), self.interior_frame.winfo_reqheight())
        self.canvas.config(scrollregion=f"0 0 {size[0]} {size[1]}")
        if self.interior_frame.winfo_reqwidth() != self.canvas.winfo_width(): # Update the canvas's width to fit the interior frame
            self.canvas.config(width=self.interior_frame.winfo_reqwidth())
    
    def _on_mousescroll(self, event):
        """
        Allows using the scrollwheel when hovering over a the frame (Doesn't work on MacOS or Linux for some reason)
        """
        self.canvas.yview_scroll(int(-1*(event.delta/25)), "units")

class EntryTreeview(ttk.Treeview):
    """
    Treeview that allows the user to edit the boxes using EntryPopup objects, basically
    an editable treeview
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind("<Double-Button-1>", self._on_double_click)
        self.bind("<FocusOut>", lambda event : self._clear_selection())
        self.scrollbar = ttk.Scrollbar(self.master, orient="vertical", command=self.yview)
        self['yscrollcommand'] = self.scrollbar.set

        self.scrollbar.pack(side="right", fill="y")
    
    def _on_double_click(self, event):
        """
        Event handler for when the user double clicks to edit a tkinter treeview.
        Destroys any entry windows if there are any before trying to edit any others.
        """
        for child in event.widget.winfo_children():
            child.destroy()
        if "disabled" in event.widget.state():
            return
        self._edit_entries(event.x, event.y)
    
    def _edit_entries(self, event_x, event_y):
        """
        Pulls up a popup entry box for the user to change entry values of a tkinter treeview
        """
        try:
            selected_item = self.selection()[0]
        except IndexError:
            pass
        else:
            x, y, width, height = self.bbox(selected_item)

            total_column_width = 0
            for i, column in enumerate(self["columns"]):
                column_width = self.column(column)["width"]
                total_column_width += column_width
                if event_x < total_column_width and i == 0:
                    return
                elif event_x < total_column_width:
                    relx = (total_column_width - column_width) / width
                    break

            relwidth = column_width / width

            popup = EntryPopup(self, selected_item, i, font=commonVars.default_font)
            popup.place(relx=relx, y=y, anchor="nw", relwidth=relwidth, height=height)
    
    def _clear_selection(self):
        for sel in self.selection():
            self.selection_remove(sel)
    
class EntryPopup(ttk.Entry):
    """
    ttk.Treeview isn't inherently editable, this subclass of entry is meant to
    create a popup box so the user can edit the values in the tree.
    """

    def __init__(self, parent, item, columnid, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        self.item = item
        self.columnid = columnid

        self.insert(0, parent.item(self.item)["values"][columnid])
        self.focus_force()

        self.bind("<Return>", self._on_return)
        self.bind("<Escape>", lambda event : self.destroy())
        self.bind("<FocusOut>", self._on_return)

        vcmd = (self.register(self._validate), "%S") # valid command
        ivcmd = (self.register(self._on_invalid),) # invalid command
        self.config(validate="key", validatecommand=vcmd, invalidcommand=ivcmd)
    
    def _on_return(self, event):
        """
        Changes the values of the tkinter treeview when hitting enter or
        closing entry box by unfocusing the window.
        """
        if self.get() == "":
            self.bell()
            return
        values = self.parent.item(self.item)["values"]
        values[self.columnid] = self.get()
        self.parent.item(self.item, values=values)
        self.destroy()
    
    def _validate(self, value):
        """
        Checks if the next user input is an integer
        """
        if value.isdigit():
            return True
        else:
            return False
    
    def _on_invalid(self):
        """
        Makes a noise when the user tries to type in a non-integer value into the entry window
        """
        self.bell()

class ValidatedEntry(tk.Entry):
    """
    I hate ttk, I hate ttk, I hate ttk, I hate ttk.
    Anyway, this class is meant to have the LOOK of a ttk.Entry class, without being one.
    All I wanted to do was to highlight the entry box in red when it contains an invalid entry.
    God I hate ttk, as doing this in ttk is impossible when using certain themes.

    Make sure to set ipadx and ipady = 1 when packing widget into gui
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master, *args, relief="solid", insertwidth=1, border=0, highlightbackground="#7a7a7a", 
                         highlightcolor="#0078d7", highlightthickness=1, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        self.valid = True
        self.tooltip = ToolTip(master) # Tooltip to send a message of what specifically went wrong during validation, WIP

        self.config = self.configure # Adding config alias to remap to overridden configure function

    def _on_enter(self, event):
        if self.cget("state") == "normal":
            if self.valid:
                self.config(highlightbackground="#000000")
            else:
                self.config(highlightbackground="#ff0000")
    
    def _on_leave(self, event):
        if self.cget("state") == "normal":
            if self.valid:
                self.config(highlightbackground="#7a7a7a")
            else:
                self.config(highlightbackground="#ff7069")
    
    def _on_disable(self):
        self.config(highlightbackground="#cccccc")
    
    def _on_enable(self):
        if self.valid:
            self.config(highlightbackground="#7a7a7a", highlightcolor="#0078d7")
        else:
            self.config(highlightbackground="#ff7069", highlightcolor="#ff0000")
    
    def configure(self, *args, **kwargs):
        """
        Overriding the configure function so that the entry will properly grey out when disabled
        """
        super().configure(*args, **kwargs)
        if "state" in kwargs:
            if kwargs["state"] == "disabled":
                self._on_disable()
            elif kwargs["state"] == "normal":
                self._on_enable()

    def set_valid(self, valid_state):
        self.valid = valid_state

        if self.valid == True:
            self.config(highlightbackground="#7a7a7a", highlightcolor="#0078d7")
        else:
            self.config(highlightbackground="#ff7069", highlightcolor="#ff0000")

class PlotToolbar(NavigationToolbar2Tk):
    """
    Custom Matplotlib toolbar class that has an additional Plot Settings option in addition the other home/zoom/pan functions.
    """

    def __init__(self, canvas, window, figure, time_sel=True, ch_sel=True, region_sel=True, pack_toolbar=False):
        
        self.toolitems = ( # removing configure subplots option on toolbar because it doesn't work with the agg backend for matplotlib
                        ('Home', 'Reset original view', 'home', 'home'),
                        ('Back', 'Back to  previous view', 'back', 'back'),
                        ('Forward', 'Forward to next view', 'forward', 'forward'),
                        (None, None, None, None),
                        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
                        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
                        (None, None, None, None),
                        ('Save', 'Save the figure', 'filesave', 'save_figure'),
                        (None, None, None, None),
                        ("Settings", "Plot Settings", os.path.relpath("./img/buttons/settings", start=plt.__file__ + "/mpl_data"), "toggle_settings")
                        ) # Use relpath because matplotlib is hardcoded to use its own install location for image files (Maybe there's a way around this)
                            # Turns into some goofy (/path/to/matplotlib/../../../../../desired/image/path) looking string

        super().__init__(canvas, window, pack_toolbar=pack_toolbar)
        self.figure = figure
        self.window = window #(from super init)
        self.canvas = canvas #(from super init)

        self.frame = tk.Frame(window, highlightbackground="#bbbbbb", highlightthickness=2) # Plot Settings frame
        self.frame.lift()

        self.style = ttk.Style()
        self.style.configure("settings.TLabel.Label", font=commonVars.default_font, foreground="#000000")
        # This is simply meant to control the color of LabelFrames when the settings page is disabled/enabled

        if time_sel: # Add time cut selection
            self.start_time_label = ttk.Label(self.frame, text="Start Date/Time", style="settings.TLabel.Label")
            self.start_time = DateEntry(self.frame, labelwidget=self.start_time_label)

            self.end_time_label = ttk.Label(self.frame, text="End Date/Time", style="settings.TLabel.Label")
            self.end_time = DateEntry(self.frame, labelwidget=self.end_time_label)

            self.start_time.grid(row=0, column=0, columnspan=2, ipadx=5, ipady=5, padx=5, pady=5, sticky="ew")
            self.end_time.grid(row=1, column=0, columnspan=2, ipadx=5, ipady=5, padx=5, pady=5, sticky="ew")
        
        if ch_sel: # Add channel cut selection
            self.channel_select_label = ttk.Label(self.frame, text="BHM Channel Selection", style="settings.TLabel.Label")
            self.channel_select = ChannelSelection(self.frame, labelwidget=self.channel_select_label)

            self.channel_select.grid(row=2, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
        
        if region_sel: # Add region cut selection
            self.region_select_label = ttk.Label(self.frame, text="BHM Region Selection", style="settings.TLabel.Label")
            self.region_select = RegionSelection(self.frame, labelwidget=self.region_select_label)

            self.region_select.grid(row=2, column=1, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
            
        # Plot redraw button
        self.draw_button = ttk.Button(self.frame, text="Redraw Plots", command=lambda : Thread(target=self._redraw, daemon=True).start())
        self.draw_button.grid(row=3, column=0, columnspan=2, ipadx=5, ipady=5, padx=5, pady=5, sticky="ew")


    def _set_loading_state(self, state):
        """
        Method to set the state of the settings frame. This will disable/enable the entire frame and change a few colors and what not
        """
        if state == True:
            disable_frame(self.frame)
            self.style.configure("settings.TLabel.Label", foreground="#6D6D6D") # Change text color of labels within plot settings
            # ttk, doesn't normally change the label text color when disabled, so we do so manually for better visual clarity
            self.loading_text = ttk.Label(self.frame, text="Redrawing plots...", font=commonVars.label_font) # Plop some loading text on our frame
            self.loading_text.place(relx=0.5, y=self.frame.winfo_height()/2 - self.draw_button.winfo_height() + 16, anchor="center")

        elif state == False:
            self.loading_text.destroy() # Remove loading text
            enable_frame(self.frame)
            if hasattr(self, "region_select"):
                self.region_select._update_region_display() # Update our region display so we disable the correct sub-widgets
            self.style.configure("settings.TLabel.Label", foreground="#000000") # Change text color back to black

    def toggle_settings(self):
        """
        Toggles the view of the settings frame. If the frame already exists, hide it, else bring up the frame.
        """
        if not self.frame.winfo_ismapped():
            self.frame.place(x=5, rely=(self.master.winfo_height()-self.winfo_height()-5)/self.master.winfo_height(),
                                anchor="sw")
        else:
            self.frame.place_forget()
    
    def _validate(self):
        """
        Set variables to be used for data cutting. Each of these getters have their own internal way 
        of handling errors from their respecitive widgets.
        """
        valid_state = True
        if hasattr(self, "start_time"):
            try:
                self.start_utc = self.start_time.get_time()
                self.end_utc = self.end_time.get_time()
            except AssertionError:
                valid_state = False

        if hasattr(self, "channel_select"):
            self.draw_channels = self.channel_select.get_selected_channels()

        if hasattr(self, "region_select"):
            try:
                self.region_settings = self.region_select.get_region_settings()
            except AssertionError:
                valid_state = False
        
        return valid_state

    
    def clear_plot(self):
        """
        Clear axes in the figure attached to our toolbar
        """
        for ax in self.figure.axes:
            ax.clear()

    def _redraw(self):
        """
        Initialization for draw_plot method
        """
        is_valid = self._validate()
        if is_valid:
            self._set_loading_state(True)
            self.clear_plot()
        else:
            return

        try:
            for uHTR in (commonVars.uHTR4, commonVars.uHTR11):

                if isinstance(self, (LegoToolbar, ADCToolbar, TDCToolbar, TDCStabilityToolbar)):
                    theCut = self._get_data_cut(uHTR, cut_type="numpy")
                elif isinstance(self, (OccupancyToolbar, ChannelEventsToolbar)):
                    theCut = self._get_data_cut(uHTR, cut_type="pandas")
                
                self.draw_plot(uHTR, theCut)

        except Exception as err: # Make sure we re-enable the settings frame if something goes wrong!
            analysis_helpers.error_handler(err)
            messagebox.showerror("Error", "An unknown exception has occured! Traceback information has been written to error.log")
            self._set_loading_state(False)
            return

        self.canvas.draw_idle() # Redraw new canvas
        self.update() # Update toolbar memory, basically makes sure the "home", "back" and "forward" buttons all work properly
        self._set_loading_state(False)
    
    def draw_plot(self, uHTR, theCut):
        """
        This method is intentionally empty here, it is designed to be overridden by subclasses for their
        specific use case on how they want to draw their figures/axes
        """
        pass
    
    def _get_data_cut(self, uHTR, cut_type="numpy"):
        """
        Dpending on the cut_type, returns either a numpy truth array or a pandas.DataFrame.query string
        that we can use as a cut on our data.
        """
        if cut_type == "numpy": # Returns a numpy truth array
            theCut = np.ones(shape=(len(uHTR.run),), dtype=bool)

            if len(theCut) == 0:
                return theCut

            if hasattr(self, "start_time"):
                theCut = (theCut) & (uHTR.orbit >= dt_conv.utc_ms_to_orbit(self.start_utc, commonVars.start_time_utc_ms, commonVars.reference_orbit)) &\
                    (uHTR.orbit <= dt_conv.utc_ms_to_orbit(self.end_utc, commonVars.start_time_utc_ms, commonVars.reference_orbit))
                

            if hasattr(self, "channel_select"):
                chCut = np.zeros(shape=(len(uHTR.run),), dtype=bool)
                for ch_name, ch in self.draw_channels.items():
                    if uHTR.uHTR == "4" and "P" in ch_name:
                        chCut = chCut | (uHTR.ch_mapped == ch)
                    elif uHTR.uHTR == "11" and "M" in ch_name:
                        chCut = chCut | (uHTR.ch_mapped == ch)
                theCut = theCut & chCut

            if hasattr(self, "region_select"):
                
                if self.region_settings["Custom Region"]:
                    theCut = theCut & uHTR.df.eval(self.region_select.query_string).to_numpy()

                else:
                    regionCut = np.zeros(shape=(len(uHTR.run),), dtype=bool)
                    if self.region_settings["Signal Region"]:
                        regionCut = regionCut | uHTR.df.index.isin(uHTR.SR.index)

                    if self.region_settings["Activation Region"]:
                        regionCut = regionCut | uHTR.df.index.isin(uHTR.AR.index)

                    if self.region_settings["Collision Products"]:
                        regionCut = regionCut | uHTR.df.index.isin(uHTR.CP.index)
                    theCut = theCut & regionCut


        elif cut_type == "pandas": # Returns a pd.DataFrame.query string

            theCut = ""

            if len(uHTR.run) == 0:
                return theCut
            
            if hasattr(self, "start_time"):
                theCut += f"(orbit >= {dt_conv.utc_ms_to_orbit(self.start_utc, commonVars.start_time_utc_ms, commonVars.reference_orbit)} & " +\
                    f"orbit <= {dt_conv.utc_ms_to_orbit(self.end_utc, commonVars.start_time_utc_ms, commonVars.reference_orbit)})"

            if hasattr(self, "channel_select"):
                chCut = ""
                if uHTR.uHTR == "4":
                    channels = [uHTR.CMAP[channel] for channel in self.draw_channels if "P" in channel]
                elif uHTR.uHTR == "11":
                    channels = [uHTR.CMAP[channel] for channel in self.draw_channels if "M" in channel]
                for i, ch in enumerate(channels):
                    if i == 0:
                        chCut = f"(ch == {ch})"
                    else:
                        chCut = f"{chCut} | (ch == {ch})"
                if chCut != "":
                    theCut = f"{theCut} & ({chCut})"
                else:
                    return "run == -1" # If the user for some reason chooses options in such a way as to plot absolutely nothing
                    # return a query that guarentees that A) Nothing breaks and B) We plot nothing

            if hasattr(self, "region_select"):
                if self.region_settings["Custom Region"]:
                    theCut = f"{theCut} & {self.region_select.query_string}"
                else:
                    regionCut = ""
                    if self.region_settings["Signal Region"]:
                        regionCut = f"index.isin(@uHTR.SR.index)"

                    if self.region_settings["Activation Region"]:
                        if regionCut == "":
                            regionCut = "index.isin(@uHTR.AR.index)"
                        else:
                            regionCut = f"{regionCut} | index.isin(@uHTR.AR.index)"

                    if self.region_settings["Collision Products"]:
                        if regionCut == "":
                            regionCut = "index.isin(@uHTR.CP.index)"
                        else:
                            regionCut = f"{regionCut} | index.isin(@uHTR.CP.index)"
                    if regionCut != "":
                        theCut = f"{theCut} & ({regionCut})"
                    else:
                        return "run == -1" # If the user for some reason chooses options in such a way as to plot absolutely nothing
                        # return a query that guarentees A) Nothing breaks and B) We plot nothing

        return theCut


class LegoToolbar(PlotToolbar):

    def draw_plot(self, uHTR, theCut):

        if len(uHTR.run) == 0:
            plotting.plot_lego_gui(uHTR.uHTR, None, None, None)
            return
        
        xdata = uHTR.tdc[theCut]
        ydata = uHTR.peak_ampl[theCut]

        if len(xdata) == 0:
            plotting.plot_lego_gui(uHTR.uHTR, None, None, None)
            return

        h, xbins, ybins = np.histogram2d(xdata,ydata, bins=(np.arange(-0.5,50,1),np.arange(0,180,1)))
        plotting.plot_lego_gui(uHTR.uHTR, xbins, ybins, h)


class ADCToolbar(PlotToolbar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, ch_sel=False, region_sel=False, **kwargs)

    def draw_plot(self, uHTR, theCut):

        binx = np.arange(min(120, min(calib.ADC_CUTS.values())), 181, 1)
        binx_tick = np.arange(min(120, min(calib.ADC_CUTS.values())//5*5), 181, 5)
        
        for ch in uHTR.CMAP.keys():

            if len(uHTR.run) == 0:
                plotting.plot_adc_gui(ch, None, binx, binx_tick, uHTR.adc_plt_tdc_width)
                continue
        
            chCut = theCut & (np.abs(uHTR.tdc-calib.TDC_PEAKS[ch]) < uHTR.adc_plt_tdc_width) & (uHTR.ch_mapped == uHTR.CMAP[ch])
            x = uHTR.peak_ampl[chCut]
            

            if len(x) == 0:
                plotting.plot_adc_gui(ch, None, binx, binx_tick, uHTR.adc_plt_tdc_width)
                continue

            plotting.plot_adc_gui(ch, x, binx, binx_tick, uHTR.adc_plt_tdc_width)


class TDCToolbar(PlotToolbar):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, ch_sel=False, region_sel=False, **kwargs)

    def draw_plot(self, uHTR, theCut):
        delay = 0 # This is currently hardcoded as 0 in analysis, leaving it here in case that changes
        for ch in uHTR.CMAP.keys():

            if len(uHTR.run) == 0:
                plotting.plot_tdc_gui(ch, None, None)
                continue

            chCut = theCut & (uHTR.peak_ampl > calib.ADC_CUTS[ch]) & (uHTR.ch_mapped == uHTR.CMAP[ch])
            x = uHTR.tdc[chCut]
            counts, _ = np.histogram(x, bins=np.arange(-.5,50,1))
            peak = np.argmax(counts[delay:])

            if len(x) == 0:
                plotting.plot_tdc_gui(ch, None, None)
                continue

            plotting.plot_tdc_gui(ch, x, peak, delay)


class TDCStabilityToolbar(PlotToolbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ch_sel=False, region_sel=False, **kwargs)
    
    def draw_plot(self, uHTR, theCut):

        if len(uHTR.run) == 0:
            plotting.plot_tdc_stability_gui(uHTR.uHTR, None, None, None, None, None)
            return

        t_df = []
        _mean = []
        _mode = []
        _std_dev = []
        for ch in uHTR.CMAP.keys():
            ch_num = uHTR.CMAP[ch]
            sr = uHTR.df[theCut & (uHTR.df["ch"].values == ch_num) & (uHTR.df["peak_ampl"].values >= calib.ADC_CUTS[ch]) &\
                        (uHTR.df["tdc"].values >= (calib.TDC_PEAKS[ch]-5)) & (uHTR.df["tdc"].values < (calib.TDC_PEAKS[ch]+5))]
            if sr.empty:
                # Changed from appending 0 to NaN so no data point is drawn
                _mean.append(float("NaN"))
                _mode.append(float("NaN"))
                _std_dev.append(float("NaN"))
                # Adds a filler line to sr so that when graphing violin plots, the x labels properly line up when dealing with empty data
                # Passing NaN ensures no other calculations using t_df are changed
                filler_data = {col_name : [float("NaN")] if col_name != "ch_name" else [ch] for col_name in ("bx", "tdc", "tdc_2", "ch", "ch_name", "orbit", "run", "peak_ampl")}
                sr = pd.DataFrame(data=filler_data)
            else:
                _mean.append(sr.tdc.mean())
                _mode.append(sr.tdc.mode()[0])
                _std_dev.append(sr.tdc.std())

            t_df.append(sr)


        t_df = pd.concat(t_df)

        if t_df.empty:
            plotting.plot_tdc_stability_gui(uHTR.uHTR, None, None, None, None, None)
            return

        try:
            _mode_val = t_df.tdc.mode()[0]
        except KeyError: # If we get a KeyError, this means the data is empty
            _mode_val = None
            _sig = None

        else:
            if len(t_df.tdc) == 1: # ensure std() doesn't break due to only one entry existing
                _sig = 0
            else:
                _sig = t_df.tdc.std()

        plotting.plot_tdc_stability_gui(uHTR.uHTR, t_df, _mode, _mode_val, _std_dev, _sig)


class OccupancyToolbar(PlotToolbar):
    
    def draw_plot(self, uHTR, theCut):

        if len(uHTR.run) == 0:
            plotting.plot_occupancy_gui(uHTR.uHTR, None, None)
            return

        BR_bx = uHTR.BR.query(theCut)["bx"]
        SR_bx = uHTR.SR.query(theCut)["bx"]

        if BR_bx.empty and SR_bx.empty:
            plotting.plot_occupancy_gui(uHTR.uHTR, None, None)
            return

        plotting.plot_occupancy_gui(uHTR.uHTR, BR_bx, SR_bx)


class RateToolbar(PlotToolbar):
    # Placeholder, requires much more work to integrate than other plots, currently a WIP

    def __init__(self, canvas, window, figure, **kwargs):
        self.toolitems = (
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to  previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        (None, None, None, None),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        (None, None, None, None),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
        )
        super(PlotToolbar, self).__init__(canvas, window, **kwargs)
        self.figure = figure
        

class ChannelEventsToolbar(PlotToolbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ch_sel=False, **kwargs)
    
    def draw_plot(self, uHTR, theCut):
        
        if len(uHTR.run) == 0:
            plotting.plot_channel_events_gui(uHTR.uHTR, None, None, None)
            return

        channels = [ch for ch in uHTR.CMAP.keys()]
        SR_events = uHTR.SR.query(theCut)["ch"].value_counts(sort=False)#.to_numpy()
        BR_events = uHTR.BR.query(theCut)["ch"].value_counts(sort=False)#.to_numpy()

        for ch in uHTR.CMAP.values(): # Pad pd.Series with zeros to ensure proper plotting
            if ch not in SR_events:
                SR_events.loc[ch] = 0
            if ch not in BR_events:
                BR_events.loc[ch] = 0
        SR_events.sort_index(inplace=True)
        BR_events.sort_index(inplace=True)

        if SR_events.empty and BR_events.empty:
            plotting.plot_channel_events_gui(uHTR.uHTR, None, None, None)
            return

        plotting.plot_channel_events_gui(uHTR.uHTR, channels, SR_events, BR_events)


class DateEntry(ttk.LabelFrame):
    """
    LabelFrame widget that contains date and time entry boxes that are validated to ensure that they contain actual dates.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.date = ValidatedEntry(self, width=10, justify="left", font=commonVars.default_font) # Date Entry 
        self.date_label = ttk.Label(self, text="Date (yyyy/mm/dd)")

        self.time = ValidatedEntry(self, width=8, justify="left", font=commonVars.default_font) # Time Entry
        self.time_label = ttk.Label(self, text="Time (hh:mm:ss)")

        self.date_label.grid(row=0, column=0, padx=(0, 20))
        self.time_label.grid(row=0, column=1)
        
        self.date.grid(row=1, column=0, padx=(0, 20), ipadx=1, ipady=1, sticky="ew")
        self.time.grid(row=1, column=1, ipadx=1, ipady=1, sticky="ew")

        vcmd = (self.register(self._validate), "%W", "%P", "%V") # valid command
        ivcmd = (self.register(self._on_invalid), "%W") # invalid command
        self.date.config(validate=["all"], validatecommand=vcmd, invalidcommand=ivcmd)
        self.time.config(validate=["all"], validatecommand=vcmd, invalidcommand=ivcmd)

        self.date_tooltip_message = ""
        self.time_tooltip_message = ""

        self.utc_time = None
    
    def _validate(self, widget, entry, validation_type):
        """
        Check that ensures that what the Date/Time widget contains is an actual date/time
        in the correct format.

        The date/time checker is NOT robust, it's not meant to be complicated, just does basic checks.
        Does not account for leap seconds or weird timekeeping things in general.
        """
        if widget == str(self.date):
            if validation_type == "focusout":
                try:
                    year = int(entry[0:4])
                    month = int(entry[5:7])
                    day = int(entry[8:10])
                except:
                    self.date_tooltip_message = "Invalid date format!"
                    return False
                
                if not all(char.isdigit() or char == "/" for char in entry): # Basic formatting check
                    self.date_tooltip_message = "Invalid date format!"
                    return False
                
                if entry[4] != "/" or entry[7] != "/": # Checks for mandatory / character between year/month/day
                    self.date_tooltip_message = "'/' character missing in date format!"
                    return False
                
                if year < 0: # Checks for valid year
                    self.date_tooltip_message = "Invalid year value!"
                    return False
                
                if month > 12 or month < 1: # Checks for valid month number
                    self.date_tooltip_message = "Invalid month value!"
                    return False
                
                if month in [1, 3, 5, 7, 8, 10, 12] and (day > 31 or day < 1): # Checks for valid day number (excluding february)
                    self.date_tooltip_message = "Invalid day value!"
                    return False
                elif month in [4, 6, 9, 11] and (day > 30 or day < 1):
                    self.date_tooltip_message = "Invalid day value!"
                    return False
                elif month == 2:
                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0): # leap year check
                        if (day > 29 or day < 1): 
                            self.date_tooltip_message = "Invalid day value!"
                            return False
                        return True
                    elif (day > 28 or day < 1):
                        self.date_tooltip_message = "Invalid day value!"
                        return False
                    
            elif validation_type == "key":
                if len(entry) > 10:
                    self.date_tooltip_message = "Date entry too long!"
                    return False
                
            else:
                # If validation_type != key or focusout, return True, but don't change validity state of entry widget 
                return True
            
            self.date.set_valid(True)
            return True
        
        elif widget == str(self.time):
            if validation_type == "focusout":
                try:
                    hour = int(entry[0:2])
                    minute = int(entry[3:5])
                    second = int(entry[6:8])
                except:
                    self.time_tooltip_message = "Invalid time format!"
                    return False
                
                if not all(char.isdigit() or char == ":" for char in entry): # Basic formatting check
                    self.time_tooltip_message = "Invalid time format!"
                    return False
                
                if entry[2] != ":" or entry[5] != ":": # Checks for mandatory : character between hour:minute:second
                    self.time_tooltip_message = "':' character missing in time format!"
                    return False
            
                if hour < 0 or hour > 23: # Check for valid hour
                    self.time_tooltip_message = "Invalid hour value!"
                    return False
                
                if minute < 0 or minute > 59: # Check for valid minute
                    self.time_tooltip_message = "Invalid minute value!"
                    return False
                
                if second < 0 or second > 59: # Check for valid second
                    self.time_tooltip_message = "Invalid second value!"
                    return False
            
            elif validation_type == "key":
                if len(entry) > 8:
                    self.time_tooltip_message = "Time entry too long!"
                    return False
            
            else:
                # If validation_type != key or focusout, return True, but don't change validity state of entry widget 
                return True
  
            self.time.set_valid(True)    
            return True
        
    
    def _on_invalid(self, widget):
        """
        If widget fails validation, ring display bell and set ValidatedEntry's valid state to False (results in red outline around entry box)
        """
        if widget == str(self.date):
            self.date.set_valid(False)
        elif widget == str(self.time):
            self.time.set_valid(False)
        self.bell()
    
    def set_time(self, utc_ms):
        """
        Sets the values in the Date and Time entry widgets given a utc timestamp in milliseconds
        """
        date = dt_conv.get_date_time(utc_ms)
        self.utc_time = utc_ms
        self.date.delete(0, "end")
        self.time.delete(0, "end")
        self.date.insert(0, f"{date.year:04}/{date.month:02}/{date.day:02}")
        self.time.insert(0, f"{date.hour:02}:{date.minute:02}:{date.second:02}")
    
    def get_time(self):
        """
        Validates date/time entries and returns a utc timestamp (in milliseconds) if all checks are passed
        """
        if self._validate(str(self.date), self.date.get(), "focusout"):
            year, month, day = [int(val) for val in self.date.get().split("/")]
        else:
            self._on_invalid(str(self.date))

        if self._validate(str(self.time), self.time.get(), "focusout"):
            hour, minute, second = [int(val) for val in self.time.get().split(":")]
        else:
            self._on_invalid(str(self.time))

        try:
            self.utc_time = dt_conv.tz_to_utc_ms(year, month, day, hour, minute, second)
        except UnboundLocalError:
            self.utc_time = None
            raise AssertionError
        
        return self.utc_time

class ChannelSelection(ttk.LabelFrame):
    """
    LabelFrame widget that contains a scrollable list of checkboxes that will enable/disable the display of channels
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.checkbutton_info = {}
        self.frame = ScrollableFrame(self, canvas_height=222)
        self.frame.pack(fill="both", expand=True)

        self.channels = {**hw_info.get_uHTR4_CMAP(), **hw_info.get_uHTR11_CMAP()} # Get CMAPs for both uHTR4 and uHTR11

        for i, ch_name in enumerate(self.channels):
            row = i % 20
            column = i//20
            check_var = tk.BooleanVar()
            check_var.set(1)
            check_button = ttk.Checkbutton(self.frame.interior_frame, text=ch_name, variable=check_var, onvalue=True, offvalue=False)
            check_button.grid(row=row, column=column, padx=5, pady=5, sticky="w")
            self.checkbutton_info[ch_name] = [check_button, check_var]
    
    def get_selected_channels(self):
        """
        Get a dict of which channels are selected (both channel name (ie PN01) and channel number)
        """
        return {ch_name : ch_num for ch_name, ch_num in self.channels.items() if self.checkbutton_info[ch_name][1].get()}

class RegionSelection(ttk.LabelFrame):
    """
    LabelFrame widget that allows the selection of predefined BHM Regions (Signal region (SR), 
    Activation region (AR) (Background minus CP), or Collision products (CP)), or the user can manually
    define a region of the plots by typing in a valid pandas.DataFrame.query string to look at a specific region.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.checkbutton_info = {}

        self.regions = "Signal Region", "Activation Region", "Collision Products"
        self.valid_df = pd.DataFrame(
                               {"bx" : [0, 1, 2],
                               "tdc" : [0, 1, 2],
                             "tdc_2" : [0, 1, 2],
                                "ch" : [0, 1, 2],
                           "ch_name" : ["PN01", "PN02", "PN03"],
                             "orbit" : [0, 1, 2],
                               "run" : [0, 1, 2],
                         "peak_ampl" : [0, 1, 2]})
        # Add a false dataframe with the same column names as bhm_analyser.df so we can validate that the
        # query string from custom region entry is a valid query

        # 0 = Preset region, 1 = Custom region
        self.region_sel_var = tk.IntVar()
        self.region_sel_var.set(0)
        self.preset_radiobutton = ttk.Radiobutton(self, text="Preset Region", value=0, variable=self.region_sel_var, command=self._update_region_display)
        self.custom_radiobutton = ttk.Radiobutton(self, text="Custom Region", value=1, variable=self.region_sel_var, command=self._update_region_display)
        self.custom_entry = ValidatedEntry(self, justify="left", font=commonVars.default_font)
        self.custom_entry.config(state="disabled")

        self.preset_radiobutton.pack(side="top", fill="x", padx=5, pady=5)

        for region in self.regions: # Create the 3 predefined region checkboxes
            check_var = tk.BooleanVar()
            check_var.set(1)
            check_button = ttk.Checkbutton(self, text=region, variable=check_var, onvalue=True, offvalue=False)
            check_button.pack(side="top", fill="x", padx=(25, 5), pady=5)
            self.checkbutton_info[region] = [check_button, check_var]
        
        self.custom_radiobutton.pack(side="top", fill="x", padx=5, pady=5)
        self.custom_entry.pack(side="top", fill="x", padx=(25, 5), pady=5, ipadx=1, ipady=1)

        vcmd = (self.register(self._validate), "%P", "%V") # valid command
        ivcmd = (self.register(self._on_invalid)) # invalid command
        self.custom_entry.config(validate=["all"], validatecommand=vcmd, invalidcommand=ivcmd)

        self.tooltip_message = ""

    
    def _update_region_display(self):
        """
        Update which widgets are enable/disable based on which radiobutton is currently selected
        """
        if self.region_sel_var.get(): # If custom region is selected
            for region in self.regions:
                self.checkbutton_info[region][0].state(["disabled"])
            self.custom_entry.configure(state="normal")

        else: # If predefined region is selected
            for region in self.regions:
                self.checkbutton_info[region][0].state(["!disabled"])
            self.custom_entry.configure(state="disabled")
    
    def _validate(self, query_string, validation_type):
        """
        Checks if the string typed into the custom region entry box is a valid query string for our DataFrame.
        """

        if self.region_sel_var.get():
            if validation_type == "manual": # We have to set this validation type manually

                # Since I tend to use these terms interchanagebly, add an alias for adc -> peak_ampl
                self.query_string = query_string.replace("adc", "peak_ampl")
                try:
                    self.valid_df.eval(self.query_string)
                    self.custom_entry.set_valid(True)
                    return True
                except:
                    self.tooltip_message = "Invalid DataFrame query!"
                    return False
            elif validation_type == "key":
                self.custom_entry.set_valid(True)
            
        return True

    def _on_invalid(self):
        """
        If custom region entry query is invalid, ring display bell and set invalidate entry box.
        """
        self.custom_entry.set_valid(False)
        self.bell()
    
    def get_region_settings(self):
        """
        Return a dict telling us which regions are selected. 
        If using a custom region entry, check if it is a valid query string.
        """
        region_dict = {"Custom Region": self.region_sel_var.get()}
        region_dict.update({region : self.checkbutton_info[region][1].get() for region in self.regions})
        if self.region_sel_var.get() == 1:
            if not self._validate(self.custom_entry.get(), "manual"):
                self._on_invalid()
                raise AssertionError
        return region_dict


class ToolTip(tk.Frame):
    """
    Tooltip popup class. Creates a little text info box, WIP
    """

    def __init__(self, master, *args, **kwargs):
        super().__init__(master=master, *args, **kwargs)