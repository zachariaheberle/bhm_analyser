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

    def select_runs(self,run_bounds):
        '''
        run_bounds [inclusive] --> give the lower and upper bound of the runs you are interested in
        '''
        theCut = (self.run >= run_bounds[0]) & (self.run <= run_bounds[1])
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
        xdata = self.tdc#[self.bx > 50]
        ydata = self.peak_ampl#[self.bx > 50]
        h, xbins, ybins = np.histogram2d(xdata,ydata, bins=(np.arange(-0.5,50,1),np.arange(90.5,180,5)))

        # if you want to create your 3d axes in the current figure (plt.gcf()):

        ax3d = Axes3D(fig=plt.gcf(), rect=None, azim=60-10, elev=30, proj_type='persp')

        # lego plot
        ax = plotting.lego(h, xbins, ybins, ax=ax3d)
        ax.set_xlabel("TDC [a.u]")
        ax.set_ylabel("Ampl [a.u]")
        ax.set_zlabel("Events")
        ax.set_title(f"{self.beam_side[self.uHTR]}")
        plt.savefig(f"{self.figure_folder}/uHTR{self.uHTR}_lego.png",dpi=300)
        plt.close()

    def saveADCplots(self,binx=None,binx_tick=None):
        if binx == None:
            binx = np.arange(119.5,180,1)
        if binx_tick == None:    
            binx_tick = np.arange(119.5,180,5)
        for ch in self.CMAP.keys():
                f,ax = plt.subplots()
                # print(ch)
                x = self.peak_ampl[(np.abs(self.tdc-calib.TDC_PEAKS[ch]) < self.adc_plt_tdc_width)&(self.ch_mapped == self.CMAP[ch])]
                _=plt.hist(x,bins=binx)
                plotting.textbox(0.5,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {self.adc_plt_tdc_width}")
                plt.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
                plt.xticks(binx_tick,rotation = 45)
                plt.xlabel("ADC [a.u]")
                plt.savefig(f"{self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{ch}.png",dpi=300)
                plt.close()

    def saveTDCplots(self,delay=10):
        '''
            TDC distance of the peak from 0; This can be used if there is a activation peak that shadows the BH peak
        '''
        self.TDC_Peaks = {}
        f,ax = plt.subplots()
        for ch in self.CMAP.keys():
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
            plt.close()


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

    def get_SR_BR(self):
        '''
        BR --> Bkg Region (Collisions & Activation)
        SR --> Signal Region i.e, BIB region
        applys the cuts and splits the data into CR & SR
        '''

        self.convert2pandas()

        #Not the most optimum way, but works just fine...
        self.SR = []
        self.BR = []

        #width of the TDC window
        tdc_window = 1 # +/- 1
        for ch in self.CMAP.keys():
            ch_num = self.CMAP[ch]
            sr = self.df.query(f"(ch=={ch_num})& (tdc >= {calib.TDC_PEAKS[ch]-tdc_window})&(tdc <= {calib.TDC_PEAKS[ch]+tdc_window}) &(peak_ampl >= {calib.ADC_CUTS[ch]})")
            cr = self.df.query(f"(ch=={ch_num})&((tdc < {calib.TDC_PEAKS[ch]-tdc_window})|(tdc > {calib.TDC_PEAKS[ch]+tdc_window}))&(peak_ampl < {calib.ADC_CUTS[ch]})")
            self.SR.append(sr)
            self.BR.append(cr)
        self.SR = pd.concat(self.SR)
        self.BR = pd.concat(self.BR)
        pass


    def plot_OccupancySRBR(self):
        '''
        plot occupancy histogram (Events in BX)
        Collision & Activation agains  BIB
        '''
        plt.hist(self.BR.bx,bins=np.arange(-0.5,3564,1),color='k',label = "Collision $\&$ Activation")
        plt.hist(self.SR.bx,bins=np.arange(-0.5,3564,1),color='r',label = "BIB")
        plt.yscale('log')
        plotting.textbox(0.0,1.11,'Preliminary',15)
        plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15)
        plt.xlabel('BX ID')
        plt.ylabel('Events/1')
        plt.legend(loc='best',frameon=1)
        plt.savefig(f"{self.figure_folder}/occupancy_uHTR{self.uHTR}.png",dpi=300)
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
            sr = df.query(f"(ch=={ch_num})&(peak_ampl >= {calib.ADC_CUTS[ch]})&(tdc >= {calib.TDC_PEAKS[ch]-5})&(tdc < {calib.TDC_PEAKS[ch]+5})")
            channels.append(ch)
            _mean.append(sr.tdc.mean())
            if ch != "MN05":
                _mode.append(sr.tdc.mode()[0])
            else:
                _mode.append(0)
            _std_dev.append(sr.tdc.std())

            t_df.append(sr)


        #Computing the re
        self.tdc_correction = pd.DataFrame()
        self.tdc_correction['CH']  = channels
        self.tdc_correction['MVP'] = _mode


        t_df = pd.concat(t_df)

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

        _mode = t_df.tdc.mode()[0]
        _sig = t_df.tdc.std()

        plt.axhline(_mode,color='black',linewidth=2,linestyle='-.',label=r"MVP All Channels")
        plt.fill_between(channels, _mode+_sig, _mode-_sig,color='orange',alpha=.5,label=r"$\sigma$ All Channels")
        plotting.textbox(0.0,1.11,'Preliminary',15)
        plotting.textbox(0.5,1.11,f'{self.beam_side[self.uHTR]} [uHTR-{self.uHTR}]',15)
        plt.xticks(rotation=45, ha='center',fontsize=5)
        plt.ylabel("TDC [a.u]",fontsize=15)
        plt.xlabel("Channels",fontsize=15)
        plt.ylim(0,15)
        plt.legend(loc='upper right',frameon=True)
        plt.savefig(f"{self.figure_folder}/tdc_uHTR{self.uHTR}_stability.png",dpi=300)
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

    def analyse(self,reAdjust=True):
        '''
        Runs the steps in sequence
        Make sure you set the correct ADC Cuts & TDC Cuts in calib.ADC_CUTS & calib.TDC_PEAKS
        '''
        #cleaning up data
        self.removeNC()
        self.remove62()

        #plotting lego, ADC, and TDC plots
        self.get_legoPlt()
        if not reAdjust: self.saveADCplots() #for debugging
        self.saveTDCplots(delay=0) # this derives the MVP for the beam halo peaks
        #Readjusting the TDC Peaks to specific values # Run after saveTDCplots()
        if reAdjust:
            for key in self.TDC_Peaks:
                calib.TDC_PEAKS[key] = self.TDC_Peaks[key] 
            self.saveADCplots() # Running again to derive the 

        if self.uHTR == '4':
            detector_side='P'
        elif self.uHTR == '11':
            detector_side='M'

        # combine all the plots into pdfs
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{detector_side}F*.png  {self.figure_folder}/adc_{detector_side}F.pdf")
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/adc_peaks/uHTR_{self.uHTR}_{detector_side}N*.png  {self.figure_folder}/adc_{detector_side}N.pdf")
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/tdc_peaks/{detector_side}F*.png  {self.figure_folder}/tdc_{detector_side}F.pdf")
        os.system(f"montage -density 300 -tile 2x0 -geometry +5+50 -border 10  {self.figure_folder}/tdc_peaks/{detector_side}N*.png  {self.figure_folder}/tdc_{detector_side}N.pdf")


        self.get_SR_BR()# separates the data into signal & background region
        self.plot_OccupancySRBR()# plots the occupancy
        self.tdc_stability()

        

    