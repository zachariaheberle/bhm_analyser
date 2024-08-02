# Written by Rohith Saradhy rohithsaradhy@gmail.com


import tools.parser as parser
import tools.hw_info as hw_info
import tools.plotting as plotting
import tools.dt_conv as dt_conv
import tools.calibration as calib
import tools.commonVars as commonVars





import numpy as np
from mpl_toolkits.mplot3d.axes3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import scipy.stats as stats
import seaborn as sns
import os
import time
import warnings

class bhm_analyser():
    __version__ ="0.1"
    beam_side = {
        "4" :"+Z Side",
        "11":"-Z Side"
    }

    def __init__(self,uHTR="4") -> None:
        #print(f"Initialized {self.beam_side[uHTR]}")
        self.uHTR=uHTR
        self.figure_folder = "./figures"
        self.save_fig = True # Default value to prevent stuff from breaking
        # during testing

        self.adc_plt_tdc_width = 1

        if self.uHTR=="4":
            self.CMAP = hw_info.get_uHTR4_CMAP()
        elif self.uHTR=="11":
            self.CMAP = hw_info.get_uHTR11_CMAP()
        else:
            raise ValueError("Wrong Format for uHTR!!!")

    def create_figure_folder(self,folder=None):
        '''
        create a folder to save the figures in ...
        folder==None will result in using the commonVars.folder_name variable 
        '''
        if folder==None:
            if commonVars.folder_name == "":
                print("Please set commonVars.folder_name or provide a folder_name as the argument")
                return 0 
            else:
                self.figure_folder = commonVars.folder_name
        else:
            self.figure_folder = folder
        def mkdir(newpath):
            if not os.path.exists(newpath):
                os.makedirs(newpath)

        mkdir(self.figure_folder)
        mkdir(f"{self.figure_folder}/adc_peaks")
        mkdir(f"{self.figure_folder}/tdc_peaks")



        pass


    def load_data(self,folder_name, data_type):
        '''
        Parsing Data and loads it into memory
        '''

        def is_sorted(arr):
            """
            Checks if array is sorted. Must be given numpy array
            """
            return np.all(arr[:-1] <= arr[1:])

        if data_type == "binary":
            evt, ch,ampl, tdc,tdc_2, bx,orbit,run  = parser.parse_bin_file(f"{folder_name}")

        elif data_type == "text":
            evt, ch,ampl, tdc,tdc_2, bx,orbit,run  = parser.parse_text_file(f"{folder_name}")
        else:
            raise ValueError(f"{data_type} is not a valid data type")

        if not is_sorted(evt):
            commonVars.data_corrupted = True

        if len(evt) > 0: # only run if data isn't empty
            self.ch = ch
            self.ampl = ampl
            self.tdc = tdc
            self.tdc_2 = tdc_2
            self.bx = bx
            self.orbit = orbit
            self.run = run
            self.ch_mapped= ch.T[0]*10 + ch.T[1] #Quick Channel Mapping

    def removeNC(self):
        '''
        remove non connected channels
        '''
        start = time.time()
        #removing non_connected_channels
        for i, ch in enumerate(hw_info.not_connected_channels): # Create singular truth array 
            if i == 0:
                theCut = self.ch_mapped != ch
            else:
                theCut = theCut & (self.ch_mapped != ch)
        self.bx = self.bx[theCut]
        self.ampl   = self.ampl[theCut]
        self.tdc    = self.tdc[theCut]
        self.tdc_2  = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit  = self.orbit[theCut]
        self.run    = self.run[theCut]
        self.peak_ampl = self.ampl.max(axis=1)

        #Remove TDC value of 62!!!
    
    def remove62(self):
        '''
        remove if the TDC has a 62 flag
        '''
        theCut = (self.tdc_2 != 62) & (self.tdc < 50)
        self.bx           = self.bx[theCut]
        self.ampl         = self.ampl[theCut]
        self.tdc          = self.tdc[theCut]
        self.tdc_2        = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit        = self.orbit[theCut]
        self.run          = self.run[theCut]
        self.peak_ampl    = self.peak_ampl[theCut]

    def remove25glich(self):
        """
        Removes all 25 tdc entries with 188 ampl peaks
        """
        theCut = ((self.tdc != 25) | (self.peak_ampl != 188))

        #total_cuts = np.count_nonzero((self.tdc == 25) & (self.peak_ampl == 188))

        self.bx           = self.bx[theCut]
        self.ampl         = self.ampl[theCut]
        self.tdc          = self.tdc[theCut]
        self.tdc_2        = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit        = self.orbit[theCut]
        self.run          = self.run[theCut]
        self.peak_ampl    = self.peak_ampl[theCut]

        #self.cut_188_25 = total_cuts

    def remove124amp0tdc(self):
        """
        Removes all 0 tdc 124 ampl peak entries
        """
        theCut = (self.tdc != 0) | (self.peak_ampl != 124)

        #total_cuts = np.count_nonzero((self.tdc == 0) & (self.peak_ampl == 124))

        self.bx           = self.bx[theCut]
        self.ampl         = self.ampl[theCut]
        self.tdc          = self.tdc[theCut]
        self.tdc_2        = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit        = self.orbit[theCut]
        self.run          = self.run[theCut]
        self.peak_ampl    = self.peak_ampl[theCut]

        #self.cut_124_0 = total_cuts

    def clean_data(self):
        """
        We add this functionality so that the available runs are accurate in the final_analysis.py file, otherwise
        we tend to have extraneous runs that may include data that will eventually be purged
        """
        self.removeNC()
        self.remove62()
        self.remove25glich()
        self.remove124amp0tdc()

    def select_runs(self, run_cut, custom_range=False):
        '''
        run_cut [inclusive] --> give the lower and upper bound of the runs you are interested in if range = true
        OR if fed an integer, it will choose that run only
        OR you can feed an array of runs to choose from if range is set to false
        '''
        if isinstance(run_cut, (int, np.integer)): # checks for single value instead of range
            theCut = (self.run == run_cut)
            
        elif custom_range: # choice values
            theCut = np.full(len(self.run), False)
            for condition in run_cut:
                theCut = theCut | (self.run == condition)

        else: # range of values
            theCut = (self.run >= run_cut[0]) & (self.run <= run_cut[1])
        
        self.bx           = self.bx[theCut]
        self.ampl         = self.ampl[theCut]
        self.tdc          = self.tdc[theCut]
        self.tdc_2        = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit        = self.orbit[theCut]
        self.run          = self.run[theCut]
        self.peak_ampl    = self.peak_ampl[theCut]


    def get_legoPlt(self):
        '''
        Lego Plot of peak ampl vs tdc
        '''
        if len(self.run) == 0 and commonVars.root: # Draw empty plot in gui if data empty
            plotting.plot_lego_gui(self.uHTR, None, None, None)
            return
        
        xdata = self.tdc#[self.ch_mapped == self.CMAP["MN05"]]
        ydata = self.peak_ampl#[self.ch_mapped == self.CMAP["MN05"]]
        h, xbins, ybins = np.histogram2d(xdata,ydata, bins=(np.arange(-0.5,50,1),np.arange(0,180,1)))
        # if you want to create your 3d axes in the current figure (plt.gcf()):

        if self.save_fig:

            f = plt.figure()

            ax3d = Axes3D(fig=f, rect=None, azim=50, elev=30, proj_type='persp')

            # lego plot
            ax = plotting.lego(h, xbins, ybins, ax=ax3d)
            ax3d.set_xlabel("TDC [a.u]")
            ax3d.set_ylabel("Ampl [a.u]")
            ax3d.set_zlabel("Events")
            ax3d.set_title(f"{self.beam_side[self.uHTR]}")
            ax3d.set_xlim3d(left=0, right=50)
            ax3d.set_ylim3d(bottom=0, top=180)
            plt.savefig(f"{self.figure_folder}/uHTR{self.uHTR}_lego.png",dpi=300)

        if commonVars.root:
            plotting.plot_lego_gui(self.uHTR, xbins, ybins, h)

        plt.close()

    def saveADCplots(self,binx=None,binx_tick=None):
        """
        Plots the ADC Peaks plots
        """
        if binx is None:
            binx = np.arange(120,181,1)  # Changed 119.5 to 120 to remove .5 from x-axis scale.
        if binx_tick is None:    
            binx_tick = np.arange(120,181,5) # Changed 119.5 to 120 to remove .5 from x-axis scale.

        if self.save_fig:
            f, ax = plt.subplots()
        for i, ch in enumerate(self.CMAP.keys()):

            if len(self.run) == 0 and commonVars.root:
                plotting.plot_adc_gui(ch, None, binx, binx_tick, self.adc_plt_tdc_width)
                continue

            x = self.peak_ampl[(np.abs(self.tdc-calib.TDC_PEAKS[ch]) < self.adc_plt_tdc_width)&(self.ch_mapped == self.CMAP[ch])]

            if self.save_fig:
                if i == 0:
                    line = ax.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
                    if min(binx) < 120:
                        ax.set_xticks(binx_tick)
                        ax.set_xticklabels(labels=binx_tick, rotation=45, fontsize=5)
                    else:
                        ax.set_xticks(binx_tick)
                        ax.set_xticklabels(labels=binx_tick, rotation=45)
                    ax.set_xlabel("ADC [a.u]")
                    text_obj = plotting.textbox(0.5,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {self.adc_plt_tdc_width}")
                    counts, bins, polygon = ax.hist(x,bins=binx+0.5, histtype="stepfilled")
                    if max(counts) > 0:
                        ax.set_ylim(top=max(counts)/.95)
                    else:
                        ax.set_ylim(top=1)
                else:
                    """
                    It is *ever* so slightly faster (about 30-40ms faster per render on my machine) to change only the things we need to
                    (textbox, ylimits, histogram) on each iteration of the loop
                    """
                    hist, bin_edges = np.histogram(x, bins=binx)
                    verticies = []
                    for j in range(len(hist)): # Generates the verticies of the new histogram polygon
                        if j == 0:
                            verticies.append((bin_edges[0]+0.5, 0))
                            verticies.append((bin_edges[0]+0.5, hist[1]))
                        elif j == len(hist) - 1:
                            verticies.append((bin_edges[j]+0.5, hist[j]))
                            verticies.append((bin_edges[j+1]+0.5, hist[j]))
                            verticies.append((bin_edges[j+1]+0.5, 0))
                            verticies.append((bin_edges[0]+0.5, 0))
                        else:
                            verticies.append((bin_edges[j]+0.5, hist[j]))
                            verticies.append((bin_edges[j]+0.5, hist[j+1]))
                    polygon[0].set_xy(verticies)
                    line.set_xdata([calib.ADC_CUTS[ch]]*2)
                    text_obj.set_text(f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {self.adc_plt_tdc_width}")
                    if max(hist) > 0:
                        ax.set_ylim(top=max(hist)/.95)
                    else:
                        ax.set_ylim(top=1)

                f.savefig(f"{self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{ch}.png",dpi=300)

            if commonVars.root:
                plotting.plot_adc_gui(ch, x, binx, binx_tick, self.adc_plt_tdc_width)

        plt.close()

    def saveTDCplots(self,delay=10):
        '''
            TDC distance of the peak from 0; This can be used if there is a activation peak that shadows the BH peak
        '''
        if self.save_fig:
            f,ax = plt.subplots()

        for i, ch in enumerate(self.CMAP.keys()):

            if len(self.run) == 0 and commonVars.root:
                plotting.plot_tdc_gui(ch, None, None)
                continue

            x = self.tdc[(self.peak_ampl > calib.ADC_CUTS[ch])&(self.ch_mapped == self.CMAP[ch])]
            binx = np.arange(-.5,50,1)

            if self.save_fig:
                if i == 0:
                    # start = time.time()
                    text_obj = plotting.textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15, ax=ax)
                    plotting.textbox(0.0,1.11,'Preliminary',15, ax=ax)
                    plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15, ax=ax)
                    ax.set_xlabel("TDC [a.u]")
                    counts, bins, polygon = ax.hist(x,bins=binx,histtype='step',color='r')
                    peak = np.argmax(counts[delay:])
                    line = ax.axvline(peak+delay,color='k',linestyle='--')
                    if max(counts) > 0:
                        ax.set_ylim(top=max(counts)/.95)
                    else:
                        ax.set_ylim(top=1)
                else:
                    """
                    It is *ever* so slightly faster (about 50-100ms faster per render on my machine) to change only the things we need to
                    (textboxes, ylimits, histogram) on each iteration of the loop
                    """
                    # start = time.time()
                    hist, bin_edges = np.histogram(x, bins=binx)
                    verticies = []
                    for j in range(len(hist)): # Generates the verticies of the new histogram polygon
                        if j == 0:
                            verticies.append((bin_edges[0], 0))
                            verticies.append((bin_edges[0], hist[1]))
                        elif j == len(hist) - 1:
                            verticies.append((bin_edges[j], hist[j]))
                            verticies.append((bin_edges[j+1], hist[j]))
                            verticies.append((bin_edges[j+1], 0))
                            verticies.append((bin_edges[0], 0))
                        else:
                            verticies.append((bin_edges[j], hist[j]))
                            verticies.append((bin_edges[j], hist[j+1]))
                    polygon[0].set_xy(verticies)
                    peak = np.argmax(hist[delay:])
                    line.set_xdata([peak+delay-1]*2)
                    text_obj.set_text(f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}')
                    if max(hist) > 0:
                        ax.set_ylim(top=max(hist)/.95)
                    else:
                        ax.set_ylim(top=1)

                f.savefig(f"{self.figure_folder}/tdc_peaks/{ch}.png",dpi=300)
            
            else:
                hist, bin_edges = np.histogram(x, bins=binx)
                peak = np.argmax(hist[delay:])

            if commonVars.root:
                plotting.plot_tdc_gui(ch, x, peak, delay)

            plt.close()
    

    def auto_align_adc_tdc(self):
        """
        Automatically determines the peak TDC value and ADC Cut value

        TDC peak is determined by the adc array that has the largest peak value within the region of adc > 127 and tdc < 15

        ADC Cut is determined by finding the approximate standard deviation (~68% of area within +/- 15 bins of peak adc value) 
        of the peak_ampl array at tdc == tdc peak value
        """

        for ch in self.CMAP.keys():
            adc = self.peak_ampl[self.ch_mapped == self.CMAP[ch]]
            tdc = self.tdc[self.ch_mapped == self.CMAP[ch]]

            # We set the tdc peak as the max value of the tdc/adc lego plot with the region tdc < 15 and adc > 127, since the signal region should be there,
            # given that the detectors are properly aligned (hardware level)
            h, tdc_bins, adc_bins = np.histogram2d(tdc, adc, bins=(np.arange(-0.5,15,1),np.arange(128,180,1)))
            max_index = list(h.flatten()).index(np.max(h))
            tdc_peak, adc_peak = int(max_index / h.shape[1]), max_index % h.shape[1] # Note, adc peak is offset by -128 here and does not reflect the actual adc value

            calib.TDC_PEAKS[ch] = tdc_peak
            adc_vals = h[tdc_peak]

            area_ratio = 0
            left_bound = right_bound = adc_peak
            min_index = max(0, adc_peak-15) # prevent index errors by establishing max and min values for index bounds
            max_index = min(50, adc_peak + 16)
            total_counts = sum(adc_vals[min_index:max_index])

            while area_ratio < .68 and total_counts != 0: # Use ~1 sigma bounds as the adc cut
                if left_bound >= min_index:
                    left_bound -= 1
                if right_bound < max_index:
                    right_bound += 1
                area_ratio = sum(adc_vals[left_bound+1:right_bound]) / total_counts # non-inclusive cut of endpoints

            if total_counts == 0: 
                calib.ADC_CUTS[ch] = calib.ADC_CUTS_v2[ch] # if channel is empty, we don't want this to break, set cut to manually derived approximations
            else:
                while adc_vals[left_bound+1] == 0:# If left bound is hovering over a data void (ie a hardware cut that is greater than it),
                # then move left bound next to nearest non-zero point (this is primarily a visual thing, and should have no effect on analysis) 
                        left_bound += 1
                
                calib.ADC_CUTS[ch] = left_bound + 128
        
        


    def convert2pandas(self):
        self.df = pd.DataFrame()
        self.df['bx']           =self.bx
        # self.df['ampl']         =self.ampl
        self.df['tdc']          =self.tdc
        self.df['tdc_2']        =self.tdc_2
        self.df['ch']           =self.ch_mapped

        self.inverted_CMAP = {v: k for k, v in self.CMAP.items()}
        self.df["ch_name"] = self.df["ch"].map(self.inverted_CMAP)

        self.df['orbit']        =self.orbit
        self.df['run']          =self.run
        self.df['peak_ampl']    =self.peak_ampl
        pass

    def get_SR_BR_AR_CP(self):
        '''
        BR --> Bkg Region (Collisions & Activation)
        SR --> Signal Region i.e, BIB region
        AR --> Activation Region (Bkg Regiion minus Collisions)
        CP --> Collision Products
        applys the cuts and splits the data into CR & SR
        '''

        self.convert2pandas()

        # Much more optimal
        SR = []
        BR = []
        CP = []
        AR = []
        
        #width of the TDC window
        tdc_window = 1 # +/- 1
        #col_prod = "(tdc > 28) & (tdc < 34) & (peak_ampl > 80) & (peak_ampl < 140)"

        for ch in self.CMAP.keys():
            ch_num = self.CMAP[ch]
            ch_df = self.df[self.df["ch"].values==ch_num]
            
            sr = ch_df[(ch_df["tdc"].values >= calib.TDC_PEAKS[ch]-tdc_window) & (ch_df["tdc"].values <= calib.TDC_PEAKS[ch]+tdc_window) & (ch_df["peak_ampl"] >= calib.ADC_CUTS[ch])]
            br = ch_df[((ch_df["tdc"].values < calib.TDC_PEAKS[ch]-tdc_window) | (ch_df["tdc"].values > calib.TDC_PEAKS[ch]+tdc_window)) | (ch_df["peak_ampl"] < calib.ADC_CUTS[ch])]
            cp = ch_df[(ch_df["tdc"].values > 28) & (ch_df["tdc"].values < 34) & (ch_df["peak_ampl"].values > 80) & (ch_df["peak_ampl"].values < 140)]
            ar = br[~((br["tdc"].values > 28) & (br["tdc"].values < 34) & (br["peak_ampl"].values > 80) & (br["peak_ampl"].values < 140))]

            SR.append(sr)
            BR.append(br)
            CP.append(cp)
            AR.append(ar)

        self.SR = pd.concat(SR)
        self.BR = pd.concat(BR)
        self.CP = pd.concat(CP)
        self.AR = pd.concat(AR)


    def plot_OccupancySRBR(self):
        '''
        plot occupancy histogram (Events in BX)
        Collision & Activation against  BIB
        '''
        # print(f"self.BR.bx: {self.BR.bx}")
        # print(f"self.SR.bx: {self.SR.bx}")
        if len(self.run) == 0 and commonVars.root:
            plotting.plot_occupancy_gui(self.uHTR, None, None)
            return
        
        if self.save_fig:
            f, ax = plt.subplots()
            ax.set_yscale('log')
            plotting.textbox(0.0,1.11,'Preliminary',15, ax=ax)
            plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15, ax=ax)
            ax.set_xlabel('BX ID')
            ax.set_ylabel('Events/1')
            ax.hist(self.BR.bx, bins=np.arange(-0.5,3564,1), color='k', histtype="stepfilled", label="Collision $\&$ Activation")
            ax.hist(self.SR.bx, bins=np.arange(-0.5,3564,1), color='r', histtype="stepfilled", label="BIB")
            ax.legend(loc='upper right',frameon=1)
            plt.savefig(f"{self.figure_folder}/occupancy_uHTR{self.uHTR}.png",dpi=300)

        if commonVars.root:
            plotting.plot_occupancy_gui(self.uHTR, self.BR.bx, self.SR.bx)

        plt.close()

    #Data Quality Plots
    def tdc_stability(self):
        '''
        Plots the stability, and calculates the MVP of the TDC

        MVP kept in self.tdc_correction
        '''
        #Should only apply ADC cuts

        if len(self.run) == 0 and commonVars.root:
            plotting.plot_tdc_stability_gui(self.uHTR, None, None, None, None, None)
            return
        
        if "df" not in self.__dict__.keys():
            print("df not found: Calling convert2pandas()")
            self.convert2pandas()

        t_df = []
        channels = []
        _mean = []
        _mode = []
        _std_dev = []
        for ch in self.CMAP.keys():
            ch_num = self.CMAP[ch]
            # print(f"ch: {ch}")
            # print(f"sr condition: (ch=={ch_num})&(peak_ampl >= {calib.ADC_CUTS[ch]})&(tdc >= {calib.TDC_PEAKS[ch]-5})&(tdc < {calib.TDC_PEAKS[ch]+5})")
            sr = self.df[(self.df["ch"].values == ch_num) & (self.df["peak_ampl"].values >= calib.ADC_CUTS[ch]) & (self.df["tdc"].values >= (calib.TDC_PEAKS[ch]-5)) & (self.df["tdc"].values < (calib.TDC_PEAKS[ch]+5))]
            #sr2 = self.df.query(f"(ch=={ch_num})&(peak_ampl >= {calib.ADC_CUTS[ch]})&(tdc >= {calib.TDC_PEAKS[ch]-5})&(tdc < {calib.TDC_PEAKS[ch]+5})")
            # print(f"sr.tdc: {sr.tdc}")
            # print(f"sr.tdc.mean(): {sr.tdc.mean()}")
            # print(f"sr.tdc.mode(): {sr.tdc.mode()}")
            # print(f"sr.tdc.mode()[0]: {sr.tdc.mode()[0]}")
            channels.append(ch)
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


        #Computing the re
        # self.tdc_correction = pd.DataFrame()
        # self.tdc_correction['CH']  = channels
        # self.tdc_correction['MVP'] = _mode


        t_df = pd.concat(t_df)

        try:
            _mode_val = t_df.tdc.mode()[0]
        except KeyError: # If we get a KeyError, this means the data is empty
            pass
        else:

            if len(t_df.tdc) == 1: # ensure std() doesn't break due to only one entry existing
                _sig = 0
            else:
                _sig = t_df.tdc.std()

        if self.save_fig:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')

                #Violin Plot
                f,ax = plt.subplots(figsize=(8,6))
                sns.violinplot(data = t_df,x='ch_name',y='tdc',cut=0,bw=.15,scale='count')
                plt.xticks(rotation=45, ha='center',fontsize=15)
                plotting.textbox(0.0,1.11,'Preliminary',30)
                plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',30)
                plt.ylabel("TDC [a.u]",fontsize=30)
                plt.xlabel("Channels",fontsize=30)
                plt.ylim(0,15)
                plt.savefig(f"{self.figure_folder}/tdc_uHTR{self.uHTR}_stability_violin.png",dpi=300)
                plt.close()


                #MVP Vanilla Stability Plots
                f,ax = plt.subplots()
                ax.errorbar(channels, _mode,yerr=_std_dev
                            ,fmt='r.',ecolor='k',capsize=2
                            ,label="MPV of TDC"
                        )

                plt.axhline(_mode_val,color='black',linewidth=2,linestyle='-.',label=r"MVP All Channels")
                plt.fill_between(channels, _mode_val+_sig, _mode_val-_sig,color='orange',alpha=.5,label=r"$\sigma$ All Channels")
                
                plotting.textbox(0.0,1.11,'Preliminary',15)
                plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15)
                plt.xticks(rotation=45, ha='center',fontsize=5)
                plt.ylabel("TDC [a.u]",fontsize=15)
                plt.xlabel("Channels",fontsize=15)
                plt.ylim(0,15)
                plt.legend(loc='upper right',frameon=True)
                plt.savefig(f"{self.figure_folder}/tdc_uHTR{self.uHTR}_stability.png",dpi=300)

        if commonVars.root:
            plotting.plot_tdc_stability_gui(self.uHTR, t_df, _mode, _mode_val, _std_dev, _sig)
            
        plt.close()

    def plot_channel_events(self):
        """
        Checks the events per channel to ensure angular and HV consistency
        """

        if len(self.run) == 0 and commonVars.root:
            plotting.plot_channel_events_gui(self.uHTR, None, None, None)
            return
        
        if "df" not in self.__dict__.keys():
            print("df not found: Calling get_SR_BR_CP_AR()")
            self.get_SR_BR_AR_CP()

        channels = [ch for ch in self.CMAP.keys()]
        SR_events = self.SR["ch"].value_counts(sort=False)#.to_numpy()
        # BR_events = self.BR["ch"].value_counts(sort=False)#.to_numpy()

        for ch in self.CMAP.values(): # Pad pd.Series with zeros to ensure proper plotting
            if ch not in SR_events:
                SR_events.loc[ch] = 0
            # if ch not in BR_events:
            #     BR_events.loc[ch] = 0
        SR_events.sort_index(inplace=True)
        # BR_events.sort_index(inplace=True)

        if self.save_fig:

            f = plt.figure(figsize=(6.5,6.5), dpi=300)
            ax: plotting.EllipseAxes = f.add_subplot(axes_class=plotting.EllipseAxes, ab_ratio=1/.95, min_angle=-45, max_angle=225)
            angle_map = commonVars.angle_map

            ax.set_xticks(angle_map)
            ax.set_xticklabels(labels=channels, fontsize=8)
            ax.grid(axis="both")
            
            ax.bar(angle_map, SR_events.to_numpy(), width=np.max(SR_events.to_numpy()) / 5, facecolor="red", label="BIB")
            ax.set_xlabel("Channels", fontsize=15)
            ax.set_ylabel("Event Count", fontsize=15)

            plotting.textbox(0.0,1.05,'Preliminary', 15, ax=ax)
            plotting.textbox(0.5,1.05,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]', 15, ax=ax)
            #textbox(1,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax, horizontalalignment="right")

            ax.legend(loc='upper right', frameon=True)

            plt.savefig(f"{self.figure_folder}/uHTR{self.uHTR}_channel_events.png", bbox_inches="tight")

        if commonVars.root:
            plotting.plot_channel_events_gui(self.uHTR, channels, SR_events)
            
        plt.close()
        

    def computeCorrection(self,alignment_target,currentConfig):
        if "tdc_correction" not in self.__dict__.keys():
            print("tdc_correction DataFrame has not been computed")
            print("Please run tdc_stability method before running compute Corrections!!!")
            pass

        def qie_add(val,changeBy):
            min_value = 50 #inclusive
            max_value = 63 #inclusive
            _sum = val+changeBy
            #Crossing Conditions
            # delta +
            # val < min_val
            # sum > min_val
            # Add 14

            #delta -
            # val > max_val
            # sum < max_val
            # Sub 14
            if(val in range(min_value,max_value+1)):
                print("ERROR!!!!")
                print("val in forbidden region; Check Current Configurations!!!")
                pass
            if changeBy>= 0:
                if (val < min_value) & (_sum >= min_value):
                    return _sum + 14
                else:
                    return _sum
            elif changeBy< 0:
                if (val > max_value)&(_sum <=  max_value):
                    return _sum - 14
                else:
                    return _sum

            ''' Quick Test
                for i in range(36,78):
                    if i  not in range(50,64):
                        qie_add(i,-14)
                for i in range(36,78):
                    if i  not in range(50,64):
                        qie_add(i,14)
            '''   



        config = np.asarray([int(x) for x in currentConfig]) #Converting string list to int np.array
        self.tdc_correction['delta'] = self.tdc_correction.MVP - alignment_target
        self.tdc_correction['current_config'] = config
        self.tdc_correction['QIE'] = [qie_add(value, changeBy)for changeBy,value in zip(self.tdc_correction.delta, config)]

        qie_phase = list(  [str(x) for x in self.tdc_correction['QIE'].values])
        qie_phase.insert(10,'0')
        qie_phase.insert(10,'0')
        qie_phase.insert(22,'0')
        qie_phase.insert(22,'0')
        # print(qie_phase)
        print((" ".join(qie_phase)))
        print("$"*100)
        print(self.tdc_correction.QIE - (self.tdc_correction.current_config + self.tdc_correction.delta))



    @staticmethod
    def get_rate(df, start_time=0, bins=None, ch=None):
        '''
        start_time --> Offset for the run (time in UTC millisecond)
        '''
        if ch: # ch value given in human readable format (MN05, PN08, etc.) or number (40, 41, 42, etc.)
            if isinstance(ch, str):
                df = df.query("ch_name == ch")
            elif isinstance(ch, (int, np.integer)):
                df = df.query("ch_mapped == ch")
            else:
                raise TypeError

        df = df.sort_values("orbit")

        # Very important to cast to 64bit float to prevent crashing!!

        # x = start_time+(df.orbit.to_numpy().astype(np.float64)-commonVars.reference_orbit)*(3564*25*10**-6)## miliseconds

        # LHC length -> 26_659 m, speed of light -> 299_792_458 m/s. 
        # Provides a much more accurate orbit time than 25ns per bx (of which there are 3564)
        x = start_time+(df.orbit.to_numpy().astype(np.float64)-commonVars.reference_orbit)*(26_659/299_792_458*1000)## milliseconds
        if len(x) == 1:
            return [dt_conv.get_date_time(x[0])], [1], [None]
        if bins==None:
            y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=np.arange(np.min(x),np.max(x),23.5*1000)) # bins--> every sec
        else:
            if bins[-1] < np.max(x): # If lumi data cannot cover all of BHM data, artifically extend it
                bins = bins[:] # Make a shallow copy if we need to modify the lumi_bins list because we need lumi_bins to be constant in plotting.py
                bins.extend(np.arange(bins[-1] + 23500, np.max(x)+1, 23500)) # +1 to capture end point
            if bins[0] > np.min(x): # If BHM data exists before lumi data, add artificial bins
                early_bins = list(np.arange(np.min(x), bins[0], 23500))
                bins = early_bins + bins # Add extra bins in beginning

            y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=bins)
        # if uHTR11:
        #     y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=np.arange(np.min(x),np.max(x),25000))
        # else:
        #     y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=bins)

        # plotting.textbox(1.1,0.7,f"Run No:{run}")
        # x = binx[:-1] + (binx[1:]-binx[:-1])*0.5
        x = [dt_conv.get_date_time(i) for i in binx[:-1]]

        # Cast float64 to int64 for use with by_lumi plots (y vals are already integers anyway)
        y: np.ndarray = y.astype(np.int64) 
        return x,y,binx
    
    def print_values(self):
        """
        Prints out uHTR values, debug purposes only
        """
        self.convert2pandas()
        print(f"print values for uHTR{self.uHTR}:\n{self.df}")

    def analyse(self, reAdjust=True, run_cut=None, custom_range=False, plot_lego=False, plot_ch_events=False, save_fig=True):
        '''
        Runs the steps in sequence
        Make sure you set the correct ADC Cuts & TDC Cuts in calib.ADC_CUTS & calib.TDC_PEAKS
        Make sure you run self.clean_data() before running analysis!!!
        '''
        self.save_fig = save_fig # Sets a flag of whether or not we should be saving any figures to disk

        # select runs if applicable
        if run_cut:
            self.select_runs(run_cut, custom_range=custom_range)

        #self.print_values() # debug
        

        if len(self.run) == 0 and not commonVars.root: # make sure it doesn't analyse data that doesn't exist if there is no gui to display
            return
            
        #plotting lego, ADC, and TDC plots
        if plot_lego:
            self.get_legoPlt()

        if reAdjust and len(self.run) != 0:
            self.auto_align_adc_tdc()

        adc_binx = np.arange(min(120, min(calib.ADC_CUTS.values())), 181, 1)
        adc_binx_tick = np.arange(min(120, min(calib.ADC_CUTS.values())//5*5), 181, 5)
        self.saveADCplots(binx=adc_binx, binx_tick=adc_binx_tick)
        self.saveTDCplots(delay=0) # this derives the MVP for the beam halo peaks

        if self.uHTR == '4':
            detector_side='P'
        elif self.uHTR == '11':
            detector_side='M'

        # combine all the plots into pdfs
        if len(self.run) != 0:
            if save_fig:
                # montage is a command line executable of ImageMagick, so if we are failing here, you may not have it installed
                os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{detector_side}F*.png  {self.figure_folder}/adc_{detector_side}F.pdf")
                os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{detector_side}N*.png  {self.figure_folder}/adc_{detector_side}N.pdf")
                os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/tdc_peaks/{detector_side}F*.png  {self.figure_folder}/tdc_{detector_side}F.pdf")
                os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/tdc_peaks/{detector_side}N*.png  {self.figure_folder}/tdc_{detector_side}N.pdf")

            self.get_SR_BR_AR_CP()# separates the data into signal region, background region, activation region, and collision products
        
        self.plot_OccupancySRBR()# plots the occupancy
        self.tdc_stability()
        if plot_ch_events:
            self.plot_channel_events()


        

    