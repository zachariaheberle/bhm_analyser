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

class bhm_analyser():
    __version__ ="0.1"
    beam_side = {
        "4" :"+Z Side",
        "11":"-Z Side"
    }

    def __init__(self,uHTR="4") -> None:
        print(f"Initialized {self.beam_side[uHTR]}")
        self.uHTR=uHTR
        self.figure_folder = "./figures"

        self.adc_plt_tdc_width = 1
        pass

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

    def load_data_from_memory(self,ch,ampl, tdc,tdc_2, bx,orbit,run):
        '''
        quick load for debugging purposes
        will be removed
        '''
        self.ch = ch
        self.ampl = ampl
        self.tdc = tdc
        self.tdc_2 = tdc_2
        self.bx = bx
        self.orbit = orbit
        self.run = run
        self.ch_mapped= ch.T[0]*10 + ch.T[1] #Quick Channel Mapping


    def load_data(self,folder_name, data_type):
        '''
        Parsing Data and loads it into memory
        '''
        if data_type == "binary":
            ch,ampl, tdc,tdc_2, bx,orbit,run  = parser.parse_bin_file(f"{folder_name}")

        elif data_type == "text":
            ch,ampl, tdc,tdc_2, bx,orbit,run  = parser.parse_text_file(f"{folder_name}")
        else:
            raise ValueError(f"{data_type} is not a valid data type")

        self.ch = ch
        self.ampl = ampl
        self.tdc = tdc
        self.tdc_2 = tdc_2
        self.bx = bx
        self.orbit = orbit
        self.run = run
        self.ch_mapped= ch.T[0]*10 + ch.T[1] #Quick Channel Mapping
        pass

    def removeNC(self):
        '''
        remove non connected channels
        '''
        #removing non_connected_channels
        for i in hw_info.not_connected_channels:
            theCut  = (self.ch_mapped != i)
            self.bx = self.bx[theCut]
            self.ampl   = self.ampl[theCut]
            self.tdc    = self.tdc[theCut]
            self.tdc_2  = self.tdc_2[theCut]
            self.ch_mapped    = self.ch_mapped[theCut]
            self.orbit  = self.orbit[theCut]
            self.run    = self.run[theCut]
        self.peak_ampl = self.ampl.max(axis=1)

        if self.uHTR=="4":
            self.CMAP = hw_info.get_uHTR4_CMAP()
        elif self.uHTR=="11":
            self.CMAP = hw_info.get_uHTR11_CMAP()
        else:
            print("Wrong Format for uHTR!!!")

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
        Removes all 25 tdc entries with 188 ampl peaks and also counts how many items were removed
        """
        theCut = (self.tdc != 25) & (self.peak_ampl != 188)

        total_cuts = np.count_nonzero((self.tdc == 25) & (self.peak_ampl == 188))

        self.bx           = self.bx[theCut]
        self.ampl         = self.ampl[theCut]
        self.tdc          = self.tdc[theCut]
        self.tdc_2        = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit        = self.orbit[theCut]
        self.run          = self.run[theCut]
        self.peak_ampl    = self.peak_ampl[theCut]

        self.cut_124_0 = total_cuts

    def remove124amp0tdc(self):
        """
        Removes all 0 tdc 124 ampl peak entries and also counts how many items were removed
        """
        theCut = (self.tdc != 0) & (self.peak_ampl != 124)

        total_cuts = np.count_nonzero((self.tdc == 0) & (self.peak_ampl == 124))

        self.bx           = self.bx[theCut]
        self.ampl         = self.ampl[theCut]
        self.tdc          = self.tdc[theCut]
        self.tdc_2        = self.tdc_2[theCut]
        self.ch_mapped    = self.ch_mapped[theCut]
        self.orbit        = self.orbit[theCut]
        self.run          = self.run[theCut]
        self.peak_ampl    = self.peak_ampl[theCut]

        self.cut_25 = total_cuts

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
        xdata = self.tdc#[self.ch_mapped == self.CMAP[ch]]
        ydata = self.peak_ampl#[self.ch_mapped == self.CMAP[ch]]
        h, xbins, ybins = np.histogram2d(xdata,ydata, bins=(np.arange(-0.5,50,1),np.arange(0,180,1)))
        # if you want to create your 3d axes in the current figure (plt.gcf()):

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
            if self.uHTR == "4":
                ax3d = commonVars.lego_fig.add_subplot(121, azim=50, elev=30, projection="3d", proj_type="persp")
            elif self.uHTR == "11":
                ax3d = commonVars.lego_fig.add_subplot(122, azim=50, elev=30, projection="3d", proj_type="persp")
            ax = plotting.lego(h, xbins, ybins, ax=ax3d)
            ax3d.set_title(f"{self.beam_side[self.uHTR]}")
            ax3d.set_xlabel("TDC [a.u]")
            ax3d.set_ylabel("Ampl [a.u]")
            ax3d.set_zlabel("Events")
            ax3d.set_xlim3d(left=0, right=50)
            ax3d.set_ylim3d(bottom=0, top=180)

        plt.close()

    def saveADCplots(self,binx=None,binx_tick=None):
        if binx is None:
            binx = np.arange(120,180,1)  # Changed 119.5 to 120 to remove .5 from x-axis scale.
        if binx_tick is None:    
            binx_tick = np.arange(120,180,5) # Changed 119.5 to 120 to remove .5 from x-axis scale.
        self.ADC_Cuts = {}

        f, ax = plt.subplots()        
        #time_list = []
        for i, ch in enumerate(self.CMAP.keys()):
            x = self.peak_ampl[(np.abs(self.tdc-calib.TDC_PEAKS[ch]) < self.adc_plt_tdc_width)&(self.ch_mapped == self.CMAP[ch])]
            if i == 0:
                #start = time.time()
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
                #start = time.time()
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

            # peak_index = np.argmax(counts)
            # area_ratio = 0
            # left_bound = right_bound = peak_index
            # total_counts = sum(counts)
            # while area_ratio < .68 and len(x) != 0:
            #     if left_bound > 0:
            #         left_bound -= 1
            #     if right_bound < len(counts):
            #         right_bound += 1
            #     area_ratio = sum(counts[left_bound:right_bound + 1]) / total_counts # + 1 on right bound because of the way slicing works

            # if int(total_counts) == 0:
            #     self.ADC_Cuts[ch] = 120 # if channel is empty, we don't want this to break, set cut to 120 (lowest value on ADC graphs)
            # else:
            #     self.ADC_Cuts[ch] = int(vals[left_bound])

            # the following lines are place holders
            #plt.axvline(vals[left_bound] - 0.5, color="magenta", linestyle="--")
            #plt.axvline(vals[right_bound] + 1.5, color="magenta", linestyle="--")
            #plt.axvline(vals[peak_index] + 0.5, color="k", linestyle="--")
            # end placeholders

            f.savefig(f"{self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{ch}.png",dpi=300)

            #end = time.time()
            #time_list.append((end-start)*1000)
            #print(f"Render time: {(end-start)*1000:.3f}ms")

            if commonVars.root:
                if self.uHTR == "4":
                    gui_ax = commonVars.adc_fig.add_subplot(20, 2, (2*i + 1))
                elif self.uHTR == "11":
                    gui_ax = commonVars.adc_fig.add_subplot(20, 2, (2*i + 2))
                gui_ax.hist(x,bins=binx+0.5, histtype="stepfilled")
                plotting.textbox(0.6,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {self.adc_plt_tdc_width}", size=15, ax=gui_ax)
                gui_ax.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
                gui_ax.set_xticks(binx_tick)
                gui_ax.set_xticklabels(labels=binx_tick, rotation=45)
                gui_ax.set_xlabel("ADC [a.u]")

        plt.close()
        #print(f"Initial Render time: {time_list[0]:.3f}ms")
        #print(f"Avg Extra Render time: {np.mean(time_list[1:]):.3f}ms")
            # if self.ADC_Cuts[ch] != calib.ADC_CUTS[ch]:
            #     print(f"For channel {ch} the left cut is at {self.ADC_Cuts[ch]} with ADC_CUTS at {calib.ADC_CUTS[ch]}")

    def saveTDCplots(self,delay=10):
        '''
            TDC distance of the peak from 0; This can be used if there is a activation peak that shadows the BH peak
        '''
        self.TDC_Peaks = {}
        f,ax = plt.subplots()
        for i, ch in enumerate(self.CMAP.keys()):
            x = self.tdc[(self.peak_ampl > calib.ADC_CUTS[ch])&(self.ch_mapped == self.CMAP[ch])]
            binx = np.arange(-.5,50,1)
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
            
            self.TDC_Peaks[ch] = peak+delay

            f.savefig(f"{self.figure_folder}/tdc_peaks/{ch}.png",dpi=300)
            # end = time.time()
            # if i == 0:
            #     print(f"Initial {(end-start)*1000:.3f}ms")
            # else:
            #     print(f"Extra render {(end-start)*1000:.3f}ms")

            if commonVars.root:
                if self.uHTR == "4":
                    gui_ax = commonVars.tdc_fig.add_subplot(20, 2, (2*i + 1))
                elif self.uHTR == "11":
                    gui_ax = commonVars.tdc_fig.add_subplot(20, 2, (2*i + 2))
                gui_ax.hist(x, bins=np.arange(-0.5, 50, 1), histtype="step", color="r")
                plotting.textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15, ax=gui_ax)
                gui_ax.axvline(peak+delay,color='k',linestyle='--')
                gui_ax.set_xlabel("TDC [a.u]")

            plt.close()
            # if self.TDC_Peaks[ch] != calib.TDC_PEAKS[ch]:
            #     print(f"For channel {ch} the peak is at {peak} with ADC_CUTS at {calib.ADC_CUTS[ch]}")


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
            br = ch_df[((ch_df["tdc"].values < calib.TDC_PEAKS[ch]-tdc_window) | (ch_df["tdc"].values > calib.TDC_PEAKS[ch]+tdc_window)) & (ch_df["peak_ampl"] < calib.ADC_CUTS[ch])]
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
            if self.uHTR == "4":
                ax = commonVars.occupancy_fig.add_subplot(121)
            elif self.uHTR == "11":
                ax = commonVars.occupancy_fig.add_subplot(122)
            ax.set_yscale('log')
            plotting.textbox(0.0,1.05,'Preliminary',15, ax=ax)
            plotting.textbox(0.5,1.05,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15, ax=ax)
            ax.set_xlabel('BX ID')
            ax.set_ylabel('Events/1')
            ax.hist(self.BR.bx, bins=np.arange(-0.5,3564,1), color='k', histtype="stepfilled", label="Collision $\&$ Activation")
            ax.hist(self.SR.bx, bins=np.arange(-0.5,3564,1), color='r', histtype="stepfilled", label="BIB")
            ax.legend(loc='upper right',frameon=1)

        plt.close()

    #Data Quality Plots
    def tdc_stability(self):
        '''
        Plots the stability, and calculates the MVP of the TDC

        MVP kept in self.tdc_correction
        '''
        #Should only apply ADC cuts
        
        if "df" not in self.__dict__.keys():
            print("df not found: Calling convert2pandas()")
            self.convert2pandas()

        df = self.df
        t_df = []
        channels = []
        _mean = []
        _mode = []
        _std_dev = []
        for ch in self.CMAP.keys():
            ch_num = self.CMAP[ch]
            # print(f"ch: {ch}")
            # print(f"sr condition: (ch=={ch_num})&(peak_ampl >= {calib.ADC_CUTS[ch]})&(tdc >= {calib.TDC_PEAKS[ch]-5})&(tdc < {calib.TDC_PEAKS[ch]+5})")
            sr = df.query(f"(ch=={ch_num})&(peak_ampl >= {calib.ADC_CUTS[ch]})&(tdc >= {calib.TDC_PEAKS[ch]-5})&(tdc < {calib.TDC_PEAKS[ch]+5})")
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
        self.tdc_correction = pd.DataFrame()
        self.tdc_correction['CH']  = channels
        self.tdc_correction['MVP'] = _mode


        t_df = pd.concat(t_df)
        #print(t_df)

        # print(f"sr: {sr}")
        # print(f"t_df:\n{t_df}")

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

        if commonVars.root:
            if self.uHTR == "4":
                ax = commonVars.tdc_stability_fig.add_subplot(223)
            elif self.uHTR == "11":
                ax = commonVars.tdc_stability_fig.add_subplot(224)
            sns.violinplot(ax=ax, data = t_df,x='ch_name',y='tdc',cut=0,bw=.15,scale='count')
            plotting.textbox(0.0,1.11,'Preliminary',15, ax=ax)
            plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15, ax=ax)
            ax.set_xticks(np.arange(20))
            ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            ax.set_ylabel("TDC [a.u]",fontsize=15)
            ax.set_xlabel("Channels",fontsize=15)
            ax.set_ylim(0,15)

        plt.close()


        #MVP Vanilla Stability Plots
        f,ax = plt.subplots()
        ax.errorbar(channels, _mode,yerr=_std_dev
                    ,fmt='r.',ecolor='k',capsize=2
                    ,label="MPV of TDC"
                )
        
        _mode_val = t_df.tdc.mode()[0]

        if len(t_df.tdc) == 1: # ensure std() doesn't break due to only one entry existing
            _sig = 0
        else:
            _sig = t_df.tdc.std()

        # print(f"tdc length: {len(t_df.tdc)}")
        # print(f"Is len == 1: {len(t_df.tdc) == 1}")
        # print(type(_mode))
        # print(f"_mode:\n{_mode}")
        # print(type(_sig))
        # print(f"_sig: {_sig}")

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
            if self.uHTR == "4":
                ax = commonVars.tdc_stability_fig.add_subplot(221)
            elif self.uHTR == "11":
                ax = commonVars.tdc_stability_fig.add_subplot(222)
            ax.errorbar(channels, _mode, yerr=_std_dev, fmt='r.', ecolor='k', capsize=2, label="MPV of TDC")
            ax.axhline(_mode_val,color='black',linewidth=2,linestyle='-.',label=r"MVP All Channels")
            ax.fill_between(channels, _mode_val+_sig, _mode_val-_sig,color='orange',alpha=.5,label=r"$\sigma$ All Channels")
            plotting.textbox(0.0,1.11,'Preliminary',15, ax=ax)
            plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15, ax=ax)
            ax.set_xticks(np.arange(20))
            ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            ax.set_ylabel("TDC [a.u]",fontsize=15)
            ax.set_xlabel("Channels",fontsize=15)
            ax.set_ylim(0,15)
            ax.legend(loc='upper right',frameon=True)

        plt.close()

    def plot_channel_events(self):
        """
        Checks the events per channel to ensure angular and HV consistency
        """
        if "df" not in self.__dict__.keys():
            print("df not found: Calling convert2pandas()")
            self.convert2pandas()

        f, ax = plt.subplots()
        SR = self.SR
        BR = self.BR
        channels = [ch for ch in self.CMAP.keys()]
        SR_events = [len(SR.query(f"ch_name=='{ch_name}'")) for ch_name in channels]
        BR_events = [len(BR.query(f"ch_name=='{ch_name}'")) for ch_name in channels]
        channel_vals = np.arange(len(channels))
        width=0.9
        ax.bar(channel_vals, BR_events, width=width, align="center",color='k',label = "Collision $\&$ Activation")
        ax.bar(channel_vals, SR_events, width=width, align="center",color='r', label = "BIB")
        plotting.textbox(0.0,1.11,'Preliminary', 15, ax=ax)
        plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]', 15, ax=ax)
        ax.set_xticks(np.arange(20))
        ax.set_xticklabels(labels=channels, rotation=45, ha="center", fontsize=5)
        ax.set_xlabel("Channels", fontsize=15)
        ax.set_ylabel("Events/1", fontsize=15)
        ax.set_yscale("log")
        ax.legend(loc='upper right', frameon=True)
        plt.savefig(f"{self.figure_folder}//uHTR{self.uHTR}_channel_events.png", dpi=300)

        if commonVars.root:
            if self.uHTR == "4":
                ax = commonVars.ch_events_fig.add_subplot(121)
            elif self.uHTR == "11":
                ax = commonVars.ch_events_fig.add_subplot(122)
            ax.bar(channel_vals, BR_events, width=width, align="center",color='k',label = "Collision $\&$ Activation")
            ax.bar(channel_vals, SR_events, width=width, align="center",color='r', label = "BIB")
            plotting.textbox(0.0,1.05,'Preliminary', 15, ax=ax)
            plotting.textbox(0.5,1.05,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]', 15, ax=ax)
            ax.set_xticks(np.arange(20))
            ax.set_xticklabels(labels=channels, rotation=45, ha="center", fontsize=8)
            ax.set_xlabel("Channels", fontsize=15)
            ax.set_ylabel("Events/1", fontsize=15)
            ax.set_yscale("log")
            ax.legend(loc='upper right', frameon=True)
            
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




    def get_rate(self,df,start_time=0,bins=None,uHTR11=False, ch=None):
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
        x = start_time+(df.orbit.values-df.orbit.values[0])*3564*25*10**-6## miliseconds 
        if bins==None:
            y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=np.arange(np.min(x),np.max(x),25*1000)) # bins--> every sec
        else:
            y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=bins)
        # if uHTR11:
        #     y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=np.arange(np.min(x),np.max(x),25000))
        # else:
        #     y,binx,_ = stats.binned_statistic(x,np.ones(x.size),statistic='sum',bins=bins)

        # plotting.textbox(1.1,0.7,f"Run No:{run}")
        x = binx[:-1] + (binx[1]-binx[0])*0.5
        x = [dt_conv.get_date_time(i) for i in x]
        return x,y,binx
    
    def print_values(self):
        """
        Prints out uHTR values, debug purposes only
        """
        self.convert2pandas()
        print(f"print values for uHTR{self.uHTR}:\n{self.df}")

    def analyse(self, reAdjust=True, run_cut=None, custom_range=False, plot_lego=False, plot_ch_events=False):
        '''
        Runs the steps in sequence
        Make sure you set the correct ADC Cuts & TDC Cuts in calib.ADC_CUTS & calib.TDC_PEAKS
        '''
        #cleaning up data
        self.removeNC()
        self.remove62()
        self.remove25glich()
        self.remove124amp0tdc()

        # select runs if applicable
        if run_cut:
            self.select_runs(run_cut, custom_range=custom_range)

        #self.print_values() # debug
        

        if len(self.run) == 0: # make sure it doesn't analyse data that doesn't exist
            return
            
        #plotting lego, ADC, and TDC plots
        if plot_lego:
            self.get_legoPlt()
    
        if not reAdjust: 
            adc_binx = np.arange(min(120, min(calib.ADC_CUTS.values())), 181, 1)
            adc_binx_tick = np.arange(min(120, min(calib.ADC_CUTS.values())//5*5), 181, 5)
            self.saveADCplots(binx=adc_binx, binx_tick=adc_binx_tick)

        self.saveTDCplots(delay=0) # this derives the MVP for the beam halo peaks
        #Readjusting the TDC Peaks to specific values # Run after saveTDCplots()
        ## self.saveADCplots() # this derivates the 68% cuts from MVP for ADC plots
        if reAdjust:
            """
            There is definitely a more efficient way of doing this, will do later
            """
            i = 0
            while i == 0:#not (all([calib.TDC_PEAKS[key] == self.TDC_Peaks[key] for key in self.TDC_Peaks]) and all([calib.ADC_CUTS[key] == self.ADC_Cuts[key] for key in self.ADC_Cuts])) and i < 5:
                # Loops over and over trying to get best possible adjustment, limited to 5 loops to avoid infinite looping
                for key in self.TDC_Peaks:
                    calib.TDC_PEAKS[key] = self.TDC_Peaks[key]
                # for key in self.ADC_Cuts:
                #     calib.ADC_CUTS[key] = self.ADC_Cuts[key] 
                
                #self.saveTDCplots(delay=0)
                self.saveADCplots() # Running again to derive the 
                i += 1

        if self.uHTR == '4':
            detector_side='P'
        elif self.uHTR == '11':
            detector_side='M'

        # combine all the plots into pdfs
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{detector_side}F*.png  {self.figure_folder}/adc_{detector_side}F.pdf")
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{detector_side}N*.png  {self.figure_folder}/adc_{detector_side}N.pdf")
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/tdc_peaks/{detector_side}F*.png  {self.figure_folder}/tdc_{detector_side}F.pdf")
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/tdc_peaks/{detector_side}N*.png  {self.figure_folder}/tdc_{detector_side}N.pdf")

        self.get_SR_BR_AR_CP()# separates the data into signal region, background region, activation region, and collision products
        self.plot_OccupancySRBR()# plots the occupancy
        if plot_ch_events:
           self.plot_channel_events()
        if not self.SR.empty:
            self.tdc_stability()
        else:
            print("Signal region is empty, ignoring tdc stability plots...")


        

    