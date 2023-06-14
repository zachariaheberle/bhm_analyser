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


    def load_data(self,folder_name):
        '''
        Parsing Data and loads it into memory
        '''
        ch,ampl, tdc,tdc_2, bx,orbit,run  = parser.parse_text_file(f"{folder_name}")
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
        if type(run_cut) == int: # checks for single value instead of range
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

        plt.close()

    def saveADCplots(self,binx=None,binx_tick=None):
        if binx == None:
            binx = np.arange(120,180,1)  # Changed 119.5 to 120 to remove .5 from x-axis scale.
        if binx_tick == None:    
            binx_tick = np.arange(120,180,5) # Changed 119.5 to 120 to remove .5 from x-axis scale.
        self.ADC_Cuts = {}
        for i, ch in enumerate(self.CMAP.keys()):
            f,ax = plt.subplots()
            # print(ch)
            x = self.peak_ampl[(np.abs(self.tdc-calib.TDC_PEAKS[ch]) < self.adc_plt_tdc_width)&(self.ch_mapped == self.CMAP[ch])]
            counts, vals, _ = plt.hist(x,bins=binx+0.5) 
            peak_index = np.argmax(counts)
            area_ratio = 0
            left_bound = right_bound = peak_index
            total_counts = sum(counts)
            if int(total_counts) == 0:
                self.ADC_Cuts[ch] = 120 # if channel is empty, we don't want this to break, set cut to 120 (lowest value on ADC graphs)
                continue
            while area_ratio < .68:
                if left_bound > 0:
                    left_bound -= 1
                if right_bound < len(counts):
                    right_bound += 1
                area_ratio = sum(counts[left_bound:right_bound + 1]) / total_counts # + 1 on right bound because of the way slicing works

            self.ADC_Cuts[ch] = int(vals[left_bound])

            plotting.textbox(0.5,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {self.adc_plt_tdc_width}")
            # the following lines are place holders
            plt.axvline(vals[left_bound] - 0.5, color="magenta", linestyle="--")
            #plt.axvline(vals[right_bound] + 1.5, color="magenta", linestyle="--")
            plt.axvline(vals[peak_index] + 0.5, color="k", linestyle="--")
            # end placeholders
            plt.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
            plt.xticks(binx_tick,rotation = 45)
            plt.xlabel("ADC [a.u]")
            plt.savefig(f"{self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{ch}.png",dpi=300)

            if commonVars.root:
                if self.uHTR == "4":
                    ax = commonVars.adc_fig.add_subplot(20, 2, (2*i + 1))
                elif self.uHTR == "11":
                    ax = commonVars.adc_fig.add_subplot(20, 2, (2*i + 2))
                ax.hist(x,bins=binx+0.5)
                plotting.textbox(0.6,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {self.adc_plt_tdc_width}", size=15, ax=ax)
                ax.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
                ax.set_xticks(binx_tick)
                ax.set_xticklabels(labels=binx_tick, rotation=45)
                ax.set_xlabel("ADC [a.u]")

            plt.close()
            # if self.ADC_Cuts[ch] != calib.ADC_CUTS[ch]:
            #     print(f"For channel {ch} the left cut is at {self.ADC_Cuts[ch]} with ADC_CUTS at {calib.ADC_CUTS[ch]}")

    def saveTDCplots(self,delay=10):
        '''
            TDC distance of the peak from 0; This can be used if there is a activation peak that shadows the BH peak
        '''
        self.TDC_Peaks = {}
        for i, ch in enumerate(self.CMAP.keys()):
            f,ax = plt.subplots()
            x = self.tdc[(self.peak_ampl > calib.ADC_CUTS[ch])&(self.ch_mapped == self.CMAP[ch])]
            counts,_,_ = plt.hist(x,bins=np.arange(-.5,50,1),histtype='step',color='r')
            plotting.textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15)
            plotting.textbox(0.0,1.11,'Preliminary',15)
            plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15)
            peak = np.argmax(counts[delay:])
            plt.axvline(peak+delay,color='k',linestyle='--')
            self.TDC_Peaks[ch] = peak+delay
            plt.xlabel("TDC [a.u]")
            plt.savefig(f"{self.figure_folder}/tdc_peaks/{ch}.png",dpi=300)

            if commonVars.root:
                if self.uHTR == "4":
                    ax = commonVars.tdc_fig.add_subplot(20, 2, (2*i + 1))
                elif self.uHTR == "11":
                    ax = commonVars.tdc_fig.add_subplot(20, 2, (2*i + 2))
                ax.hist(x, bins=np.arange(-0.5, 50, 1), histtype="step", color="r")
                plotting.textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15, ax=ax)
                ax.axvline(peak+delay,color='k',linestyle='--')
                ax.set_xlabel("TDC [a.u]")

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
        self.df['ch_name']      = [self.inverted_CMAP[x] for x in self.ch_mapped ]


        self.df['orbit']        =self.orbit
        self.df['run']          =self.run
        self.df['peak_ampl']    =self.peak_ampl
        pass

    def get_SR_BR_CP(self):
        '''
        BR --> Bkg Region (Collisions & Activation)
        SR --> Signal Region i.e, BIB region
        applys the cuts and splits the data into CR & SR
        '''

        self.convert2pandas()

        #Not the most optimum way, but works just fine...
        self.SR = []
        self.BR = []
        self.CP = []

        #width of the TDC window
        tdc_window = 1 # +/- 1
        col_prod = "(tdc > 28) & (tdc < 34) & (peak_ampl > 80) & (peak_ampl < 140)"

        for ch in self.CMAP.keys():
            ch_num = self.CMAP[ch]
            sr = self.df.query(f"(ch=={ch_num})& (tdc >= {calib.TDC_PEAKS[ch]-tdc_window})&(tdc <= {calib.TDC_PEAKS[ch]+tdc_window}) &(peak_ampl >= {calib.ADC_CUTS[ch]})")
            cr = self.df.query(f"(ch=={ch_num})&((tdc < {calib.TDC_PEAKS[ch]-tdc_window})|(tdc > {calib.TDC_PEAKS[ch]+tdc_window}))&(peak_ampl < {calib.ADC_CUTS[ch]})")
            cp = self.df.query(f"(ch=={ch_num}) & ({col_prod})")
            self.SR.append(sr)
            self.BR.append(cr)
            self.CP.append(cp)
        self.SR = pd.concat(self.SR)
        self.BR = pd.concat(self.BR)
        self.CP = pd.concat(self.CP)
        # print("SR Dataframe:")
        # print(self.SR)
        # print("BR Dataframe:")
        # print(self.BR)
        # print("CP Dataframe:")
        # print(self.CP)
        pass


    def plot_OccupancySRBR(self):
        '''
        plot occupancy histogram (Events in BX)
        Collision & Activation against  BIB
        '''
        # print(f"self.BR.bx: {self.BR.bx}")
        # print(f"self.SR.bx: {self.SR.bx}")
        f, ax = plt.subplots()
        plt.hist(self.BR.bx,bins=np.arange(-0.5,3564,1),color='k',label = "Collision $\&$ Activation")
        plt.hist(self.SR.bx,bins=np.arange(-0.5,3564,1),color='r',label = "BIB")
        plt.yscale('log')
        plotting.textbox(0.0,1.11,'Preliminary',15)
        plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15)
        plt.xlabel('BX ID')
        plt.ylabel('Events/1')
        plt.legend(loc='best',frameon=1)
        plt.savefig(f"{self.figure_folder}/occupancy_uHTR{self.uHTR}.png",dpi=300)

        if commonVars.root:
            if self.uHTR == "4":
                ax = commonVars.occupancy_fig.add_subplot(121)
            elif self.uHTR == "11":
                ax = commonVars.occupancy_fig.add_subplot(122)
            ax.hist(self.BR.bx,bins=np.arange(-0.5,3564,1),color='k',label = "Collision $\&$ Activation")
            ax.hist(self.SR.bx,bins=np.arange(-0.5,3564,1),color='r',label = "BIB")
            ax.set_yscale('log')
            plotting.textbox(0.0,1.05,'Preliminary',15, ax=ax)
            plotting.textbox(0.5,1.05,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15, ax=ax)
            ax.set_xlabel('BX ID')
            ax.set_ylabel('Events/1')
            ax.legend(loc='best',frameon=1)

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
                _mean.append(0)
                _mode.append(0)
                _std_dev.append(0)
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




    def get_rate(self,df,start_time=0,bins=None,uHTR11=False):
        '''
        start_time --> Offset for the run (time in UTC millisecond)
        '''
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

    def analyse(self, reAdjust=True, run_cut=None, custom_range=False, plot_lego=False):
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
            
        if not reAdjust: self.saveADCplots() #for debugging

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

        self.get_SR_BR_CP()# separates the data into signal & background region
        self.plot_OccupancySRBR()# plots the occupancy
        if not self.SR.empty:
            self.tdc_stability()
        else:
            print("Signal region is empty, ignoring tdc stability plots...")


        

    