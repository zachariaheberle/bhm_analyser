# Written by Zachariah Eberle zachariah.eberle@gmail.com
"""
The purpose of this script is to hold all of the custom tkinter tools / widgets that are built for this project and to hold useful tkinter functions
"""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk

if not hasattr(Image, 'Resampling'): # Make sure various versions of pillow work
    Image.Resampling = Image

import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
import matplotlib.dates as dates
import numpy as np
import pandas as pd
from threading import Thread

import tools.commonVars as commonVars
import tools.dt_conv as dt_conv
import tools.hw_info as hw_info
import tools.calibration as calib
import tools.plotting as plotting
import tools.analysis_helpers as analysis_helpers

from typing import Union

def raise_frame(frame):
    """
    Raises a frame to be visible from hidden
    """
    frame.tkraise()
    
def disable_widget(widget: Union[tk.Widget, ttk.Widget], only_children=False):
    """
    Disables the widget and all child widgets, can specify only disabling child widgets instead of parent + children
    """
    if widget.winfo_class() not in ("Frame", "TFrame") and not only_children:
        try:
            widget.state(["disabled"])
        except AttributeError:
            widget.configure(state="disabled")

    for child in widget.winfo_children():
        disable_widget(child)

def enable_widget(widget: Union[tk.Widget, ttk.Widget], only_children=False):
    """
    Disables the widget and all child widgets, can specify only disabling child widgets instead of parent + children
    """
    if widget.winfo_class() not in ("Frame", "TFrame") and not only_children:
        try:
            widget.state(["!disabled"])
        except AttributeError:
            widget.configure(state="normal")

    for child in widget.winfo_children():
        enable_widget(child)

class ScrollableFrame(ttk.Frame):
    """
    ttk.Frame with an attached scrollbar that can scroll through a canvas. This is (currently) used for displaying either long lists of items
    or very large plots that require a scrollbar to view. 

    Returns the innermost frame of the widget stack, which is as follows:
    self.frame (outermost frame, essentially the master of this widget stack)
        children : self.canvas, self.scrollbar

    self.canvas (widget that allows the scrolling of the inner frame)
        children: self

    self.scrollbar (self-explanatory, it's the physical scrollbar widgets)
        children: None
    """

    def __init__(self, master, orient="vertical", canvas_height=None, **kwargs):

        if orient == "vertical":
            canvas_side = "left"
            scrollbar_side = "right"
            scrollbar_fill = "y"
        elif orient == "horizontal":
            canvas_side = "top"
            scrollbar_side = "bottom"
            scrollbar_fill = "x"

        self.frame = ttk.Frame(master=master)
        self.scrollbar = ttk.Scrollbar(self.frame, orient=orient)
        self.scrollbar.pack(side=scrollbar_side, fill=scrollbar_fill, expand=False)
        self.canvas = tk.Canvas(self.frame, height=canvas_height, bd=0, highlightthickness=0, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=canvas_side, fill="both", expand=True)
        self.canvas.bind('<Configure>', lambda event : self._configure_canvas(event))
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.scrollbar.config(command=self.canvas.yview)

        super().__init__(self.canvas, **kwargs)

        self.id = self.canvas.create_window(0, 0, window=self, anchor="nw")
        self.bind('<Configure>', lambda event : self._configure_interior(event))
    
    def pack(self, *args, **kwargs):
        """
        Since self is actually the innermost frame, we want to pack the outermost frame when we call pack, override the pack
        method so we're packing self.frame
        """
        self.frame.pack(*args, **kwargs)

    def grid(self, *args, **kwargs):
        """
        Overridden grid method, see self.pack for explanation
        """
        self.frame.grid(*args, **kwargs)
    
    def place(self, *args, **kwargs):
        """
        Overridden place method, see self.pack for explanation
        """
        self.frame.place(*args, **kwargs)

    def _configure_canvas(self, event):
        """
        Updates the inner frame's width to fill the canvas
        """
        if self.winfo_reqwidth() != self.canvas.winfo_width():
            self.canvas.itemconfigure(self.id, width=self.canvas.winfo_width())
    
    def _configure_interior(self, event):
        """ 
        Updates the scrollbars to match the size of the inner frame
        """
        size = (self.winfo_reqwidth(), self.winfo_reqheight())
        self.canvas.config(scrollregion=f"0 0 {size[0]} {size[1]}")
        if self.winfo_reqwidth() != self.canvas.winfo_width(): # Update the canvas's width to fit the interior frame
            self.canvas.config(width=self.winfo_reqwidth())
    
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
                         highlightcolor="#0078d7", highlightthickness=1, selectbackground="#0078d7", 
                         selectforeground="#ffffff", disabledbackground="#f0f0f0", **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        self.valid = True
        self.message = tk.StringVar()
        self.message_label = tk.Label(self.winfo_toplevel(), textvariable=self.message, justify="left", bd=0, 
                                      bg="#ffffff", highlightthickness=1, relief="solid", highlightbackground="#ff0000",
                                      font=("Segoe UI", 10)) # label to show a message of what specifically went wrong during validation

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
        self._remove_message()
    
    def _on_enable(self):
        if self.valid:
            self.config(highlightbackground="#7a7a7a", highlightcolor="#0078d7")
            self._remove_message()
        else:
            self.config(highlightbackground="#ff7069", highlightcolor="#ff0000")
            self._show_message()
    
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
            self._remove_message()
        else:
            self.config(highlightbackground="#ff7069", highlightcolor="#ff0000")
            self._show_message()
    
    def _show_message(self):
        if not self.message_label.winfo_ismapped():
            self.message_label.config(wraplength=self.winfo_width())
            self.message_label.place(in_=self, x=-1, y=-2, anchor="sw")

    def _remove_message(self):
        if self.message_label.winfo_ismapped():
            self.message_label.place_forget()

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
        self.config(bg="#f0f0f0") # Setting toolbar frame background
        for child in self.winfo_children():
            child.config(bg="#f0f0f0") # Setting button and label colors
        self.figure = figure
        self.window = window #(from super init)
        self.canvas = canvas #(from super init)

        self.frame = tk.Frame(window, highlightbackground="#bbbbbb", highlightcolor="#bbbbbb", highlightthickness=2, bg="#f0f0f0") # Plot Settings frame
        self.frame.lift()

        if time_sel: # Add time cut selection
            self.start_time = DateEntry(self.frame, text="Start Date/Time")
            self.end_time = DateEntry(self.frame, text="End Date/Time")

            self.start_time.grid(row=0, column=0, columnspan=2, ipadx=5, ipady=5, padx=5, pady=5, sticky="ew")
            self.end_time.grid(row=1, column=0, columnspan=2, ipadx=5, ipady=5, padx=5, pady=5, sticky="ew")
        
        if ch_sel: # Add channel cut selection
            self.channel_select = ChannelSelection(self.frame, text="BHM Channel Selection")

            self.channel_select.grid(row=2, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
        
        if region_sel: # Add region cut selection
            self.region_select = RegionSelection(self.frame, text="BHM Region Selection")

            self.region_select.grid(row=2, column=1, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
            
        # Plot redraw button
        self.draw_button = ttk.Button(self.frame, text="Redraw Plots", command=lambda : Thread(target=self._redraw, daemon=True).start())
        self.draw_button.grid(row=3, column=0, columnspan=2, ipadx=5, ipady=5, padx=5, pady=5, sticky="ew")


    def _set_loading_state(self, state):
        """
        Method to set the state of the settings frame. This will disable/enable the entire frame and change a few colors and what not
        """
        if state == True:
            disable_widget(self.frame)
            self.loading_text = ttk.Label(self.frame, text="Redrawing plots...", font=commonVars.label_font) # Plop some loading text on our frame
            self.loading_text.place(relx=0.5, y=self.frame.winfo_height()/2 - self.draw_button.winfo_height() + 16, anchor="center")

        elif state == False:
            self.loading_text.destroy() # Remove loading text
            enable_widget(self.frame)
            if hasattr(self, "region_select"):
                self.region_select._update_region_display() # Update our region display so we disable the correct sub-widgets

    def toggle_settings(self):
        """
        Toggles the view of the settings frame. If the frame already exists, hide it, else bring up the frame.
        """
        if not self.frame.winfo_ismapped():
            self.frame.place(x=5, rely=(self.master.winfo_height()-self.winfo_height()-5)/self.master.winfo_height(),
                                anchor="sw")
            if hasattr(self, "region_select") and hasattr(self, "channel_select"):
                height_diff = self.region_select.winfo_height() - self.channel_select.winfo_height()
                if height_diff:
                    new_height = int(self.channel_select.frame.canvas.cget("height")) + height_diff
                    self.channel_select.frame.canvas.config(height=new_height)
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
    
    @staticmethod
    def _mouse_event_to_message(event): # Ignore lego plot axes, since these are typically nonsensical/unintuitive coordinates
        return None


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
    
    @staticmethod
    def _mouse_event_to_message(event):
        """
        Override method for formatting the x/y position of the mouse within subplots in gui to make sense for our use case.
        """
        if event.inaxes and event.inaxes.get_navigate():
            s = f"ADC Bin: {round(event.xdata)}, Event: {round(event.ydata)}"
            return s


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
    
    @staticmethod
    def _mouse_event_to_message(event):
        if event.inaxes and event.inaxes.get_navigate():
            s = f"TDC Bin: {round(event.xdata)}, Event: {round(event.ydata)}"
            return s


class TDCStabilityToolbar(PlotToolbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ch_sel=False, region_sel=False, **kwargs)

        self.ch_map = {i : key for i, key in enumerate({**hw_info.get_uHTR4_CMAP(), **hw_info.get_uHTR11_CMAP()}.keys())}
        self.ch_map.update({-1 : "None", 40 : "None"}) # If outside channels bounds, set channel = None
    
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
    
    def _mouse_event_to_message(self, event):
        if event.inaxes and event.inaxes.get_navigate():
            plot_side = round(event.inaxes.get_position().get_points()[0][0]) # 0 = PN/PF, 1 = MN/MF
            ch_index = round(event.xdata) + 20*plot_side

            if not plot_side: # Ensure that our algorithm doesn't break if we're slightly outside the normal bounds
                if ch_index < 0:
                    ch_index = -1
                elif ch_index > 19:
                    ch_index = 19
            else:
                if ch_index < 20:
                    ch_index = 20
                elif ch_index > 39:
                    ch_index = 40

            s = f"Channel: {self.ch_map[ch_index]}, TDC: {round(event.ydata)}"
            return s


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
    
    @staticmethod
    def _mouse_event_to_message(event):
        if event.inaxes and event.inaxes.get_navigate():
            s = f"BX: {round(event.xdata)}, Event: {round(event.ydata)}"
            return s


class RateToolbar(PlotToolbar):
    """
    Because the rate plots rely on BOTH uHTR4 and uHTR11 and comes in a pair of plots including elements from both uHTR's, we have
    to make an entirely new toolbar just for the rate plots
    """

    def __init__(self, canvas, window, figure, pack_toolbar=False):
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
                        )

        super(PlotToolbar, self).__init__(canvas, window, pack_toolbar=pack_toolbar)
        self.figure = figure
        self.window = window #(from super init)
        self.canvas = canvas #(from super init)

        self.frame = tk.Frame(window, highlightbackground="#bbbbbb", highlightcolor="#bbbbbb", highlightthickness=2, bg="#f0f0f0") # Plot Settings frame
        self.frame.lift()

        self.scroll_frame = ScrollableFrame(self.frame, canvas_height=461)
        self.scroll_frame.pack(side="top", fill="both", expand=True)
        
        # Add channel cut selection
        self.channel_select1 = ChannelSelection(self.scroll_frame, text="BHM Channel Selection\n(Upper Plot)")
        self.channel_select2 = ChannelSelection(self.scroll_frame, text="BHM Channel Selection\n(Lower Plot)")

        self.channel_select1.grid(row=0, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
        self.channel_select2.grid(row=1, column=0, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
        
        # Add region cut selection
        self.region_select1 = RegionSelection(self.scroll_frame, text="BHM Region Selection\n(Upper Plot)")
        self.region_select2 = RegionSelection(self.scroll_frame, text="BHM Region Selection\n(Lower Plot)")

        # Changing default region selection (SR for top plot, CP for bottom)
        self.region_select1.checkbutton_info["Collision Products"][1].set(0)
        self.region_select1.checkbutton_info["Activation Region"][1].set(0)

        self.region_select2.checkbutton_info["Signal Region"][1].set(0)
        self.region_select2.checkbutton_info["Activation Region"][1].set(0)


        self.region_select1.grid(row=0, column=1, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
        self.region_select2.grid(row=1, column=1, ipadx=5, ipady=5, padx=5, pady=5, sticky="nw")
            
        # Plot redraw button
        self.draw_button = ttk.Button(self.frame, text="Redraw Plots", command=lambda : Thread(target=self._redraw, daemon=True).start())
        self.draw_button.pack(side="bottom", fill="x", expand=True, ipadx=5, ipady=5, padx=5, pady=5)
    
    def toggle_settings(self):
        """
        Toggles the view of the settings frame. If the frame already exists, hide it, else bring up the frame.
        """
        if not self.frame.winfo_ismapped():
            self.frame.place(x=5, rely=(self.master.winfo_height()-self.winfo_height()-5)/self.master.winfo_height(),
                                anchor="sw")
            height_diff1 = self.region_select1.winfo_height() - self.channel_select1.winfo_height()
            height_diff2 = self.region_select2.winfo_height() - self.channel_select2.winfo_height()
            if height_diff1:
                new_height1 = int(self.channel_select1.frame.canvas.cget("height")) + height_diff1
                self.channel_select1.frame.canvas.config(height=new_height1)
            if height_diff2:
                new_height2 = int(self.channel_select2.frame.canvas.cget("height")) + height_diff2
                self.channel_select2.frame.canvas.config(height=new_height2)
        else:
            self.frame.place_forget()
    
    def _validate(self):
        """
        Set variables to be used for data cutting. Each of these getters have their own internal way
        of handling errors from their respecitive widgets.
        """
        valid_state = True
        self.draw_channels1 = self.channel_select1.get_selected_channels()
        self.draw_channels2 = self.channel_select2.get_selected_channels()

        try:
            self.region_settings1 = self.region_select1.get_region_settings()
        except AssertionError:
            valid_state = False

        try:
            self.region_settings2 = self.region_select2.get_region_settings()
        except AssertionError:
            valid_state = False
        
        return valid_state

    def _get_data_cut(self):

        theCuts = []
        region_names = []
        
        for plot_index in (1, 2):

            theCut = None
            chCut = ""
            channels = [channel for channel in getattr(self, f"draw_channels{plot_index}")]

            if len(channels) < 40:
                for i, ch_name in enumerate(channels):
                    if i == 0:
                        chCut = f"(ch_name == '{ch_name}')"
                    else:
                        chCut = f"{chCut} | (ch_name == '{ch_name}')"

                if chCut != "":
                    theCut = f"({chCut})"
                else:
                    theCuts.append("run == -1")
                    continue

            if getattr(self, f"region_settings{plot_index}")["Custom Region"]:
                if theCut is not None:
                    theCut = f"{theCut} & ({getattr(self, f'region_select{plot_index}').query_string})"
                else:
                    theCut = getattr(self, f'region_select{plot_index}').query_string
                region_name = "df"
            
            else:

                SR = getattr(self, f"region_settings{plot_index}")["Signal Region"]
                AR = getattr(self, f"region_settings{plot_index}")["Activation Region"]
                CP = getattr(self, f"region_settings{plot_index}")["Collision Products"]

                if SR and not AR and not CP: # Ugly and inefficient, but oh well, there's only 8 combos anyway
                    region_name = "SR"
                
                elif AR and not SR and not CP:
                    region_name = "AR"
                
                elif CP and not SR and not AR:
                    region_name = "CP"
                
                elif AR and CP and not SR:
                    region_name = "BR"
                
                elif SR and AR and not CP:
                    region_name = "SR & AR"
                
                elif SR and CP and not AR:
                    region_name = "SR & CP"
                
                elif not (SR and CP and AR): # Empty
                    theCut = "run == -1"
                    region_name = "df" 
                
                else: # All events
                    region_name = "df"
            

            theCuts.append(theCut)
            region_names.append(region_name)
                
        return theCuts, region_names

    def _set_loading_state(self, state):
        """
        Method to set the state of the settings frame. This will disable/enable the entire frame and change a few colors and what not, mostly taken from
        PlotToolbar._set_loading_state with modifications for the rate plots specifically
        """
        if state == True:
            disable_widget(self.frame)
            self.loading_text = ttk.Label(self.frame, text="Redrawing plots...", font=commonVars.label_font) # Plop some loading text on our frame
            self.loading_text.place(relx=0.5, y=self.frame.winfo_height()/2 - self.draw_button.winfo_height() + 16, anchor="center")

        elif state == False:
            self.loading_text.destroy() # Remove loading text
            enable_widget(self.frame)
            self.region_select1._update_region_display() # Update our region displays so we disable the correct sub-widgets
            self.region_select2._update_region_display()
    
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
            theCuts, region_names = self._get_data_cut()
            self.draw_plot(theCuts, region_names)

        except Exception as err: # Make sure we re-enable the settings frame if something goes wrong!
            analysis_helpers.error_handler(err)
            messagebox.showerror("Error", "An unknown exception has occured! Traceback information has been written to error.log")
            self._set_loading_state(False)
            return

        self.canvas.draw_idle() # Redraw new canvas
        self.update() # Update toolbar memory, basically makes sure the "home", "back" and "forward" buttons all work properly
        self._set_loading_state(False)
    
    def draw_plot(self, theCuts, region_names):
        plotting.rate_plots(commonVars.uHTR4, commonVars.uHTR11, plot_regions=region_names, start_time=commonVars.start_time_utc_ms, 
                            lumi_bins=commonVars.lumi_bins, delivered_lumi=commonVars.delivered_lumi, beam_status=commonVars.beam_status,
                            theCuts=theCuts, save_fig=False)
    
    @staticmethod
    def _mouse_event_to_message(event):
        if event.inaxes and event.inaxes.get_navigate():
            s = f"Time: {dates.num2date(event.xdata).strftime('%Y/%m/%d - %H:%M:%S')}, Event: {round(event.ydata)}"
            return s
        

class ChannelEventsToolbar(PlotToolbar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, ch_sel=False, **kwargs)

        self.ch_map = {i : key for i, key in enumerate({**hw_info.get_uHTR4_CMAP(), **hw_info.get_uHTR11_CMAP()}.keys())}
        self.ch_map.update({-1 : "None", 40 : "None"}) # If outside channels bounds, set channel = None
    
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
    
    def _mouse_event_to_message(self, event):
        if event.inaxes and event.inaxes.get_navigate():
            plot_side = round(event.inaxes.get_position().get_points()[0][0]) # 0 = PN/PF, 1 = MN/MF
            ch_index = round(event.xdata) + 20*plot_side

            if not plot_side: # Ensure that our algorithm doesn't break if we're slightly outside the normal bounds
                if ch_index < 0:
                    ch_index = -1
                elif ch_index > 19:
                    ch_index = 19
            else:
                if ch_index < 20:
                    ch_index = 20
                elif ch_index > 39:
                    ch_index = 40

            s = f"Channel: {self.ch_map[ch_index]}, Event: {round(event.ydata)}"
            return s


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
                    self.date.message.set("Invalid date format!")
                    return False
                
                if not all(char.isdigit() or char == "/" for char in entry): # Basic formatting check
                    self.date.message.set("Invalid date format!")
                    return False
                
                if entry[4] != "/" or entry[7] != "/": # Checks for mandatory / character between year/month/day
                    self.date.message.set("'/' character missing in date format!")
                    return False
                
                if year < 0: # Checks for valid year
                    self.date.message.set("Invalid year value!")
                    return False
                
                if month > 12 or month < 1: # Checks for valid month number
                    self.date.message.set("Invalid month value!")
                    return False
                
                if month in [1, 3, 5, 7, 8, 10, 12] and (day > 31 or day < 1): # Checks for valid day number (excluding february)
                    self.date.message.set("Invalid day value!")
                    return False
                elif month in [4, 6, 9, 11] and (day > 30 or day < 1):
                    self.date.message.set("Invalid day value!")
                    return False
                elif month == 2:
                    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0): # leap year check
                        if (day > 29 or day < 1): 
                            self.date.message.set("Invalid day value!")
                            return False
                        return True
                    elif (day > 28 or day < 1):
                        self.date.message.set("Invalid day value!")
                        return False
                    
            elif validation_type == "key":
                if len(entry) > 10:
                    self.date.message.set("Date entry too long!")
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
                    self.time.message.set("Invalid time format!")
                    return False
                
                if not all(char.isdigit() or char == ":" for char in entry): # Basic formatting check
                    self.time.message.set("Invalid time format!")
                    return False
                
                if entry[2] != ":" or entry[5] != ":": # Checks for mandatory : character between hour:minute:second
                    self.time.message.set("':' character missing in time format!")
                    return False
            
                if hour < 0 or hour > 23: # Check for valid hour
                    self.time.message.set("Invalid hour value!")
                    return False
                
                if minute < 0 or minute > 59: # Check for valid minute
                    self.time.message.set("Invalid minute value!")
                    return False
                
                if second < 0 or second > 59: # Check for valid second
                    self.time.message.set("Invalid second value!")
                    return False
            
            elif validation_type == "key":
                if len(entry) > 8:
                    self.time.message.set("Time entry too long!")
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
    
    def _mouse_event_to_message(self, event):
        if event.inaxes and event.inaxes.get_navigate():
            plot_side = round(event.inaxes.get_position().get_points()[0][0]) # 0 = PN/PF, 1 = MN/MF
            ch_index = round(event.xdata) + 20*plot_side

            if not plot_side: # Ensure that our algorithm doesn't break if we're slightly outside the normal bounds
                if ch_index < 0:
                    ch_index = -1
                elif ch_index > 19:
                    ch_index = 19
            else:
                if ch_index < 20:
                    ch_index = 20
                elif ch_index > 39:
                    ch_index = 40

            s = f"Channel: {self.ch_map[ch_index]}, TDC: {round(event.ydata)}"
            return s

class ChannelSelection(ttk.LabelFrame):
    """
    LabelFrame widget that contains a scrollable list of checkboxes that will enable/disable the display of channels
    """

    def __init__(self, master, canvas_height=None, **kwargs):
        super().__init__(master, **kwargs)

        self.checkbutton_info = {}
        self.frame = ScrollableFrame(self, canvas_height=canvas_height)
        self.frame.pack(fill="both", expand=True)

        self.channels = {**hw_info.get_uHTR4_CMAP(), **hw_info.get_uHTR11_CMAP()} # Get CMAPs for both uHTR4 and uHTR11

        self.button_frame = ttk.Frame(self)
        self.button_frame.pack(fill="both", expand=True, pady=1)

        self.select_button = ttk.Button(self.button_frame, text="Select all", command=self.select_all)
        self.deselect_button = ttk.Button(self.button_frame, text="Deselect all", command=self.deselect_all)
        self.select_plusZ_button = ttk.Button(self.button_frame, text="Select +Z", command=self.select_plusZ)
        self.select_minusZ_button = ttk.Button(self.button_frame, text="Select -Z", command=self.select_minusZ)
        
        self.select_button.grid(column=0, row=0, sticky="nsew", padx=5)
        self.deselect_button.grid(column=0, row=1, sticky="nsew", padx=5)
        self.select_plusZ_button.grid(column=1, row=0, sticky="nsew", padx=5)
        self.select_minusZ_button.grid(column=1, row=1, sticky="nsew", padx=5)

        for i, ch_name in enumerate(self.channels):
            row = i % 20
            column = i//20
            check_var = tk.BooleanVar()
            check_var.set(1)
            check_button = ttk.Checkbutton(self.frame, text=ch_name, variable=check_var, onvalue=True, offvalue=False)
            check_button.grid(row=row, column=column, padx=5, pady=5, sticky="w")
            self.checkbutton_info[ch_name] = [check_button, check_var]
    
    def deselect_all(self):
        for check_button, check_var in self.checkbutton_info.values():
            check_var.set(False)

    def select_all(self):
        for check_button, check_var in self.checkbutton_info.values():
            check_var.set(True)
    
    def select_plusZ(self):
        for ch_name in self.checkbutton_info.keys():
            if "P" in ch_name:
                self.checkbutton_info[ch_name][1].set(True)
            else:
                self.checkbutton_info[ch_name][1].set(False)
    
    def select_minusZ(self):
        for ch_name in self.checkbutton_info.keys():
            if "M" in ch_name:
                self.checkbutton_info[ch_name][1].set(True)
            else:
                self.checkbutton_info[ch_name][1].set(False)
    
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

        self.custom_radiobutton_frame = ttk.Frame(self)
        self.custom_radiobutton = ttk.Radiobutton(self.custom_radiobutton_frame, text="Custom Region", value=1, variable=self.region_sel_var, command=self._update_region_display)
        self.custom_radiobutton_tooltip = ToolTip(self.custom_radiobutton_frame, text="Custom regions can be defined by entering a valid pandas dataframe query. "+ \
                                                  "The allowed variables are: bx, tdc, tdc_2, ch, ch_name, orbit, run, peak_ampl, adc (An alias for peak_ampl)", 
                                                  max_width=190)

        self.custom_entry = ValidatedEntry(self, justify="left", font=commonVars.default_font)
        self.custom_entry.config(state="disabled")

        self.custom_entry.message.set("Invalid dataframe query!") # Set this message once since it doesn't change, only shows if entry is actually invalidated

        self.preset_radiobutton.pack(side="top", fill="x", padx=5, pady=5)

        for region in self.regions: # Create the 3 predefined region checkboxes
            check_var = tk.BooleanVar()
            check_var.set(1)
            check_button = ttk.Checkbutton(self, text=region, variable=check_var, onvalue=True, offvalue=False)
            check_button.pack(side="top", fill="x", padx=(25, 5), pady=5)
            self.checkbutton_info[region] = [check_button, check_var]
        
        self.custom_radiobutton_frame.pack(side="top", fill="x")
        self.custom_radiobutton.pack(side="left", fill="x", padx=5, pady=5)
        self.custom_radiobutton_tooltip.pack(side="left")

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


class ToolTip(tk.Canvas):
    """
    Tooltip popup class. Creates a text info box when hovering over with the mouse.
    """

    def __init__(self, master, text="", icon_size=12, height=None, img_x=0, img_y=0, img_anchor="nw", tooltip_anchor="sw", max_width=float("inf"), **canvas_kwargs):

        if height is None:
            height = icon_size

        super().__init__(master=master, highlightthickness=0, width=icon_size, height=height, **canvas_kwargs)

        # Load image icons
        self.icon_normal = ImageTk.PhotoImage(Image.open("./img/tooltips/tooltip_info_normal.png").resize((icon_size, icon_size), resample=Image.Resampling.LANCZOS))
        self.icon_disabled = ImageTk.PhotoImage(Image.open("./img/tooltips/tooltip_info_disabled.png").resize((icon_size, icon_size), resample=Image.Resampling.LANCZOS))

        self.create_image(img_x, img_y, anchor=img_anchor, image=self.icon_normal, disabledimage=self.icon_disabled)

        self.tooltip_anchor = tooltip_anchor

        self.tooltip_label = tk.Label(self.winfo_toplevel(), text=text, justify="left", wraplength=max_width, bd=0, 
                                      bg="#cecece", highlightthickness=1, relief="solid", highlightbackground="#555555",
                                      font=("Segoe UI", 10))
        
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """
        Create popup textbox when mouse is hovering over icon
        """
        # Since the label object's parent is the toplevel window, we need to find the upper right corner of the canvas widget relative to toplevel, rather than relative to its parent
        x = self.winfo_rootx() - self.winfo_toplevel().winfo_rootx() + self.winfo_width()
        y =  self.winfo_rooty() - self.winfo_toplevel().winfo_rooty()

        self.tooltip_label.place(x=x, y=y, anchor=self.tooltip_anchor)
    
    def _on_leave(self, event):
        """
        Hide popup textbox when mouse is no longer hovering over icon
        """
        self.tooltip_label.place_forget()

class _ListboxFrame(tk.Frame):
    """
    Special frame class that is purely used to identify listbox frames using type()

    Only designed for use in Combobox
    """
    pass

class _Canvas(tk.Canvas):
    """
    tk.Canvas meant to simply override the configure method so we can properly "disable"
    the canvas by recoloring the border lines. I could make a truly custom class for this, but this is easier

    Only designed for use in Combobox
    """
    def configure(self, *args, **kwargs):
        super().configure(*args, **kwargs)
        if "state" in kwargs:
            if kwargs["state"] == "disabled":
                self.master._canvas_on_disable()
            elif kwargs["state"] == "normal":
                self.master._canvas_on_enable()

class Combobox(tk.Frame):
    """
    A combobox that's meant to look like ttk.Combobox (on windows), but is made entirely of tk widgets
    to look the same across platforms.
    """

    def __init__(self, master=None, values=[], height=10, font=None, **kwargs):

        super().__init__(master)

        height = min(height, len(values))

        self.button_image_normal = ImageTk.PhotoImage(Image.open("./img/buttons/chevron_down_normal.png"))
        self.button_image_disabled = ImageTk.PhotoImage(Image.open("./img/buttons/chevron_down_disabled.png"))

        self.entry = ValidatedEntry(self, font=font, **kwargs)
        self.entry.pack(side="left", fill="both", expand=True, padx=(0, 16), ipadx=1, ipady=1)

        # the drop down button is a canvas because we don't want the relief to change on button press (among other visual things I don't like)
        self.canvas = _Canvas(self, borderwidth=0, background="#ffffff", border=0, highlightthickness=0, 
                                width=17, height=self.entry.winfo_reqheight())
        
        self.canvas_image = self.canvas.create_image(8, self.entry.winfo_reqheight()/2, anchor="center", image=self.button_image_normal, disabledimage=self.button_image_disabled)
        self.outline1 = self.canvas.create_line(0, 0, 16, 0, 16, self.entry.winfo_reqheight()-1, -1, self.entry.winfo_reqheight()-1, fill="#7a7a7a")
        self.outline2 = self.canvas.create_line(0, 1, 0, self.entry.winfo_reqheight()-1, fill="#ffffff")

        self.listbox_frame = _ListboxFrame(self.winfo_toplevel(), bg="#ffffff", borderwidth=0, highlightthickness=1, 
                                      highlightbackground="#7a7a7a", highlightcolor="#7a7a7a")
        
        self.listbox = tk.Listbox(self.listbox_frame, relief="flat", activestyle="none", height=height, 
                                  selectmode="single", selectbackground="#0078D7", selectforeground="#ffffff",
                                  borderwidth=0, highlightthickness=0, font=font)

        self.listbox_scrollbar = ttk.Scrollbar(self.listbox_frame, orient="vertical", command=self.listbox.yview)
        self.listbox['yscrollcommand'] = self.listbox_scrollbar.set

        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox_scrollbar.pack(side="right", fill="y")
        
        # A bunch of bindings to make everything look and work properly, this is why I typically use ttk...
        self.winfo_toplevel().bind("<Button-1>", self._on_focusout)
        self.winfo_toplevel().bind("<Escape>", self._on_focusout) # WARNING, The toplevel bindings CAN be overwritten, see self._on_focusout for more detail

        self.entry.bind("<Enter>", self._entry_on_enter)
        self.entry.bind("<Leave>", self._entry_on_leave)
        self.entry.bind("<FocusIn>", self._entry_on_focusin)
        self.entry.bind("<FocusOut>", self._entry_on_focusout)
        self.entry.bind("<Configure>", self._configure_canvas)

        self.canvas.bind("<Button-1>", self._canvas_on_click)
        self.canvas.bind("<Enter>", self._canvas_on_enter)
        self.canvas.bind("<Leave>", self._canvas_on_leave)

        self.listbox.bind("<Button-1>", self._listbox_on_click)
        self.listbox.bind("<Motion>", self._listbox_on_mouse_motion)
        

        self.sel_index = -1 # Set an internal index, it's faster to access this variable than to do a function call to tk
        self.listbox.selection_set(0)

        self.canvas.place(in_=self.entry, x=self.entry.winfo_reqwidth()-1, relheight=1, width=17, bordermode="outside")

        if values is not None:
            self._values = values
            for i, value in enumerate(self._values):
                self.listbox.insert(i, value)
    
    def __getitem__(self, key):
        if key == "values":
            return self._values
        else:
            return super().__getitem__(key)
    
    def __setitem__(self, key, value):
        if key == "values":
            self.values = value
        else:
            return super().__setitem__(key, value)
    
    @property
    def values(self):
        return self._values
    
    @values.setter
    def values(self, new_values):
        """
        Make sure if we try to do Combobox.values (or Combobox["values"]) = list, we properly insert them into the tk.Listbox
        """
        self.entry.delete(0, "end")
        self._values = new_values
        for i, value in enumerate(new_values):
                self.listbox.insert(i, value)



    def _on_focusout(self, event: tk.Event):
        """
        If we click outside of the drop down menu, make sure we close out of it. Since this method is bound to root,
        it WILL get overridden by another Combobox object (or any other root bindings, so be careful!!). 
        To counter this, we iterate through the widget tree to close out of ALL listboxes, regardless of which one is open.
        (since if they have already lost focus they should be closed anyway)
        """
        if event.char != "\x1b": # \x1b is the string representation of the escape key
            for widget in self.winfo_toplevel().winfo_children():
                if isinstance(widget, _ListboxFrame):
                    if event.widget not in widget.winfo_children() and not isinstance(event.widget, _Canvas):
                        widget.place_forget()
                    
        else: # Triggers on pressing the escape key
            for widget in self.winfo_toplevel().winfo_children():
                if isinstance(widget, _ListboxFrame):
                    widget.place_forget()

    def _canvas_on_disable(self):
        """
        Properly grey out the surrounding border around the canvas widget when disabling
        """
        self.canvas.itemconfigure(self.outline1, fill="#cccccc")

    def _canvas_on_enable(self):
        """
        Properly set the color surrounding border around the canvas widget when enabling
        """
        self.canvas.itemconfigure(self.outline1, fill="#7a7a7a")


    
    def _entry_on_enter(self, event):
        """
        If we enter the entry widget, make sure to also tell the canvas widget to update
        its border colors to black
        """
        self.entry._on_enter(event)
        if self.focus_get() != self.entry and self.canvas.cget("state") == "normal":
            self.canvas.itemconfig(self.outline1, fill="#000000")

    def _entry_on_leave(self, event):
        """
        If we enter the entry widget, make sure to also tell the canvas widet to reset
        its border colors back to grey
        """
        self.entry._on_leave(event)
        if self.focus_get() != self.entry and self.canvas.cget("state") == "normal":
            self.canvas.itemconfigure(self.outline1, fill="#7a7a7a")
    
    def _entry_on_focusin(self, event):
        """
        If we focus on (by clicking on) the entry widget, make sure to tell the canvas to
        update its border colors to blue
        """
        self.canvas.itemconfigure(self.outline1, fill="#0078d7")
    
    def _entry_on_focusout(self, event):
        """
        If we lose focus on the entry widget, make sure to tell the canvas and entry widgets to
        reset their border colors to grey (or blue in the case we defocus the entry to enter the canvas)
        """
        self._canvas_on_leave(event)
    
    def _configure_canvas(self, event):
        """
        Make sure the canvas "button" actually goes where we want it to. Rescale the canvas to fit the correct xpos and height
        """
        if self.canvas.winfo_height() != self.entry.winfo_height():
            self.canvas.config(height=self.entry.winfo_height())
            self.canvas.coords(self.canvas_image, 8, self.entry.winfo_height()/2)
            self.canvas.coords(self.outline1, 0, 0, 16, 0, 16, self.entry.winfo_height()-1, -1, self.entry.winfo_height()-1)
            self.canvas.coords(self.outline2, 0, 1, 0, self.entry.winfo_height()-1)
        if self.canvas.winfo_x() != self.entry.winfo_width()-1:
            self.canvas.place_forget()
            self.canvas.place(in_=self.entry, x=self.entry.winfo_width()-1, relheight=1, width=17, bordermode="outside")



    def _canvas_on_click(self, event):
        """
        Create the listbox drop down menu when clicking on the canvas
        """
        if self.canvas.cget("state") == "normal":
            if self.listbox_frame.winfo_ismapped():
                self.listbox_frame.place_forget()
            else:
                self.listbox_frame.lift()
                self.listbox_frame.place(in_=self, x=0, rely=1, relwidth=1, bordermode="outside")
    
    def _canvas_on_enter(self, event):
        """
        If we enter the canvas widget, update the border colors to blue
        and background to (light baby blue? I'm not sure what to call this color)
        """
        if self.canvas.cget("state") == "normal":
            self.entry._on_enter(event)
            self.canvas.config(bg="#E5F1FB")
            self.canvas.itemconfigure(self.outline1, fill="#0078D7")
            self.canvas.itemconfigure(self.outline2, fill="#0078D7")
    
    def _canvas_on_leave(self, event):
        """
        If we leave the canvas widget, update the border colors to blue or grey
        and background to white. If we leave towards the entry widget, the grey color
        gets immediately overwritten by the call to _entry_on_enter() and turns black
        """
        if self.canvas.cget("state") == "normal":
            self.entry._on_leave(event)
            self.canvas.config(bg="#ffffff")
            if self.focus_get() != self.entry:
                self.canvas.itemconfigure(self.outline1, fill="#7a7a7a")
                self.canvas.itemconfigure(self.outline2, fill="#ffffff")
            else:
                self.canvas.itemconfigure(self.outline1, fill="#0078D7")
                self.canvas.itemconfigure(self.outline2, fill="#ffffff")
    

    
    def _listbox_on_click(self, event: tk.Event):
        """
        When clicking on a listbox item, close out of the listbox and write that
        item to the entry widget
        """
        entry_index = self.listbox.nearest(event.y)
        self.listbox.selection_set(entry_index)
        self.entry.delete(0, "end")
        self.entry.insert(0, str(self.listbox.selection_get()))
        self.listbox_frame.place_forget()

    def _listbox_on_mouse_motion(self, event: tk.Event):
        """
        "Highlights" the listbox entry closest to the mouse. Under the hood its
        actually selecting the item to get the effect.
        """
        entry_index = self.listbox.nearest(event.y)
        if entry_index != self.sel_index:
            try:
                self.listbox.selection_clear(self.sel_index)
            except IndexError:
                pass
            self.sel_index = entry_index
            self.listbox.selection_set(entry_index)