# Written by Rohith Saradhy rohithsaradhy@gmail.com

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import tools.dt_conv as dt_conv
import tools.commonVars as commonVars
import pandas as pd



def textbox(x,y,text,size=14,frameon=False, ax=None):
    if ax == None:
        text_obj = plt.gca().text(x, y, text, transform=plt.gca().transAxes, fontsize=size,
            verticalalignment='top'
    #          , bbox=dict(facecolor='white', alpha=0.5)
            )
    else:
        text_obj = ax.text(x, y, text, transform=ax.transAxes, fontsize=size,
                verticalalignment='top'
        #          , bbox=dict(facecolor='white', alpha=0.5)
                )
    return text_obj


from mpl_toolkits.mplot3d.axes3d import Axes3D

# (fig, rect=None, *args, azim=-60, elev=30, zscale=None, sharez=None, proj_type='persp', **kwargs)[source]¶

def lego(h, xbins, ybins, ax=None, **plt_kwargs):
    '''Function to make a lego plot out of a 2D histo matplotlib/numpy generated
    - Provide explicit axes to choose where to plot it, otherwise the current axes will be used'''
      
    if ax==None:
        fig = plt.gcf() # get current axes
#         ax = fig.add_subplot(111,projection='3d')
        ax = Axes3D(fig, rect=None, azim=-60, elev=30, proj_type='persp')
    # look for this key in the axes properies
    # -> not-so-elegant check
    
    if ax.properties().get('xlim3d',None) == None :
        print('Error, ax is not 3d')
        return None
    
    _xx, _yy = np.meshgrid(xbins[:-1], ybins[:-1],indexing='ij')
    bottom = np.zeros_like(_xx)
    top = h
    width = xbins[1]-xbins[0]
    depth = ybins[1]-ybins[0]
    mask = (h.flatten() == 0)
    ax.bar3d(_xx.flatten()[~mask], _yy.flatten()[~mask], bottom.flatten()[~mask], width, depth, h.flatten()[~mask], shade=True,color='red')
    return ax  

def rate_plots(uHTR4, uHTR11, start_time=0, lumi_bins=None, delivered_lumi=None, beam_status=None):
    '''
    After analysis step has been completed, and the plots look reasonable, you can get the rate plot
    uHTR4  --> BHM Analyser object for uHTR4 
    uHTR11 --> BHM Analyser object for uHTR11 
    Run Level needs to be implemented

    '''
    if len(uHTR4.run) == 0:
        uHTR4.SR = pd.DataFrame()
        uHTR4.CP = pd.DataFrame()
    if len(uHTR11.run) == 0:
        uHTR11.SR = pd.DataFrame()
        uHTR11.CP = pd.DataFrame()

    if delivered_lumi is not None:
        delivered_lumi = np.asarray(delivered_lumi)

    unit_labels = {
        1_000_000 : r"CMS Delivered Luminosity [$b^{-1}$]",
        1000 : r"CMS Delivered Luminosity [$mb^{-1}$]",
        1 : r"CMS Delivered Luminosity [$\mu b^{-1}$]",
        1/1000 : r"CMS Delivered Luminosity [$nb^{-1}$]",
        1/1_000_000 : r"CMS Delivered Luminosity [$pb^{-1}$]",
        1/1_000_000_000 : r"CMS Delivered Luminosity [$fb^{-1}$]",
    }

    beam_status_color_map = {
        "OTHER" : "#000000",
        "STABLE BEAMS" : "#00ff00",
        "FLAT TOP" : "#0000ff",
        "ADJUST" : "#ff0000",
        "SQUEEZE" : "#ffff00"
    }

    beam_status = np.asarray(beam_status)

    # get correct binx
    # binx = np.arange(np.min(uHTR4.orbit),np.max(uHTR4.orbit),3564*25*10**-6*25000)# 25 secs



    #Plotting the Run No:
    def plot_runNo(uHTR):
        for run in np.unique(uHTR.run)[:]:
            orbit_value = (np.min(uHTR.orbit[uHTR.run == run])-uHTR.orbit[0])*3564*25*10**-6 + start_time # time in mille-seconds
            x=dt_conv.get_date_time(orbit_value)
            ax.axvline(x,color='k',linestyle='--')
            # ax.text(x, 1.2, run, transform=ax.transAxes, fontsize=10,
            #         verticalalignment='top',rotation=90)

    def plot_lumi(ax, x, scale_factor, max_val):
        ax.plot(x, delivered_lumi*scale_factor, color="#a600ff", label="CMS Lumi")
        ax.fill_between(x, np.where(beam_status=="STABLE BEAMS", max_val, 1), 1, color=beam_status_color_map["STABLE BEAMS"], alpha=0.1, step="post", label="Stable Beams")
        ax.fill_between(x, np.where(beam_status=="ADJUST", max_val, 1), 1, color=beam_status_color_map["ADJUST"], alpha=0.1, step="post", label="Adjust")
        ax.fill_between(x, np.where(beam_status=="SQUEEZE", max_val, 1), 1, color=beam_status_color_map["SQUEEZE"], alpha=0.1, step="post", label="Squeeze")
        ax.fill_between(x, np.where(beam_status=="FLAT TOP", max_val, 1), 1, color=beam_status_color_map["FLAT TOP"], alpha=0.1, step="post", label="Flat Top")
        ax.fill_between(x, np.where(beam_status=="OTHER", max_val, 1), 1, color=beam_status_color_map["OTHER"], alpha=0.1, step="post", label="Other")
        ax.set_ylabel(unit_labels[scale_factor])
        ax.set_yscale('log')
        ax.set_ylim(1, max_val*1.05)
        
    def plot_bhm(ax, x1, x2, y1, y2, max_val, region):

        if x1 is not None:
            ax.plot(x1, y1, color='r',label=f"+Z {region}")
        if x2 is not None:
            ax.plot(x2, y2, color='k',label=f"-Z {region}")
        ax.set_xlabel("Time Approximate")
        ax.set_ylabel("BHM Event Rate")
        ax.set_ylim(1, max_val*1.05)
        ax.set_yscale('log')
        if start_time != 0:
            textbox(0.0,1.11, f"Start Date: {dt_conv.utc_to_string(start_time)}" , 14, ax=ax)

    
    # x,y,_ = uHTR4.get_rate(uHTR4.BR)
    # plt.plot(x[:N], y[:N],color='g',label="+Z BR")

    if lumi_bins is not None:
        lumi_time = [dt_conv.get_date_time(utc_ms) for utc_ms in lumi_bins]
    else:
        lumi_time = None
    
    i = 0 # index for gui plotting

    for region_name, region4, region11 in [("SR", uHTR4.SR, uHTR11.SR), ("CP", uHTR4.CP, uHTR11.CP)]:

        f,ax = plt.subplots()
        f.autofmt_xdate()
        xfmt = mdates.DateFormatter('%H:%M')
        ax.xaxis.set_major_formatter(xfmt)
        lumi_ax = ax.twinx()
        max_val = 0

        x1 = x2 = y1 = y2 = None # Placeholders to prevent UnboundLocalError

        if not region4.empty:
            x1,y1,binx_ = uHTR4.get_rate(region4,bins=lumi_bins,start_time=start_time,uHTR11=False)
            if max(y1) > max_val: max_val = max(y1)

        if not region11.empty:
            x2,y2,_ = uHTR11.get_rate(region11,bins=lumi_bins,start_time=start_time,uHTR11=True)
            if max(y2) > max_val: max_val = max(y2)

        if lumi_bins is not None:
            for scale_factor in [10**i for i in range(-9, 6, 3)]:
                if max(delivered_lumi)*scale_factor > 10:
                    break
            if max(delivered_lumi)*scale_factor > max_val: max_val = max(delivered_lumi)*scale_factor

            plot_lumi(lumi_ax, lumi_time, scale_factor, max_val)

        plot_bhm(ax, x1, x2, y1, y2, max_val, region_name)

        #if not region4.empty or not region11.empty:
        bhm_lines, bhm_labels = ax.get_legend_handles_labels()
        lumi_lines, lumi_labels = lumi_ax.get_legend_handles_labels()

        
        if not region4.empty or not region11.empty:
            # Seperate out the color map from the rest of the legend
            lines1, labels1 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                if label.upper() not in beam_status_color_map.keys()])
            ax.legend(handles=lines1, labels=labels1, loc=(1.2,0.8), frameon=1)

        if lumi_bins is not None:
            # color map stuff
            lines2, labels2 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                if label.upper() in beam_status_color_map.keys()])
            lumi_ax.legend(handles=lines2, labels=labels2, loc=(1.2, 0), title="LHC Beam Status", frameon=1)

        f.savefig(f"{uHTR4.figure_folder}/rates_{region_name}.png",dpi=300)

        if commonVars.root:
            i += 1
            ax = commonVars.rate_fig.add_subplot(2, 1, i)  
            xfmt = mdates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(xfmt)
            lumi_ax = ax.twinx()

            if lumi_bins is not None:
                plot_lumi(lumi_ax, lumi_time, scale_factor, max_val)

            plot_bhm(ax, x1, x2, y1, y2, max_val, region_name)

            bhm_lines, bhm_labels = ax.get_legend_handles_labels()
            lumi_lines, lumi_labels = lumi_ax.get_legend_handles_labels()

            if not region4.empty or not region11.empty:
                # Seperate out the color map from the rest of the legend
                lines1, labels1 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                    if label.upper() not in beam_status_color_map.keys()])
                ax.legend(handles=lines1, labels=labels1, loc=(1.1, 0.7), frameon=1)

            if lumi_bins is not None:
                # color map stuff
                lines2, labels2 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                    if label.upper() in beam_status_color_map.keys()])
                lumi_ax.legend(handles=lines2, labels=labels2, loc=(1.1, 0), title="LHC\nBeam Status", frameon=1)
        
        plt.close()