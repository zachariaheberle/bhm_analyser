# Written by Rohith Saradhy rohithsaradhy@gmail.com and Zachariah Eberle zachariah.eberle@gmail.com

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
import matplotlib.dates as mdates
import pandas as pd
import seaborn as sns
import warnings

import tools.dt_conv as dt_conv
import tools.commonVars as commonVars
import tools.hw_info as hw_info
import tools.calibration as calib
import tools.dt_conv as dt_conv
from tools.bhm import bhm_analyser

beam_side = {
        "4" :"+Z Side",
        "11":"-Z Side"
    }

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

def rate_plots(uHTR4: bhm_analyser, uHTR11: bhm_analyser, start_time=0, lumi_bins=None, delivered_lumi=None, beam_status=None):
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

    def plot_lumi(ax: plt.Axes, lumi_time, scale_factor, max_rate):
        ax.plot(lumi_time, delivered_lumi*scale_factor, color="#a600ff", label="CMS Lumi")
        ax.fill_between(lumi_time, np.where(beam_status=="STABLE BEAMS", max_rate, 0), 0, color=beam_status_color_map["STABLE BEAMS"], alpha=0.1, step="post", label="Stable Beams")
        ax.fill_between(lumi_time, np.where(beam_status=="ADJUST", max_rate, 0), 0, color=beam_status_color_map["ADJUST"], alpha=0.1, step="post", label="Adjust")
        ax.fill_between(lumi_time, np.where(beam_status=="SQUEEZE", max_rate, 0), 0, color=beam_status_color_map["SQUEEZE"], alpha=0.1, step="post", label="Squeeze")
        ax.fill_between(lumi_time, np.where(beam_status=="FLAT TOP", max_rate, 0), 0, color=beam_status_color_map["FLAT TOP"], alpha=0.1, step="post", label="Flat Top")
        ax.fill_between(lumi_time, np.where(beam_status=="OTHER", max_rate, 0), 0, color=beam_status_color_map["OTHER"], alpha=0.1, step="post", label="Other")
        ax.set_ylabel(unit_labels[scale_factor])
        ax.set_yscale('symlog')
        ax.set_ylim(0.1, max_rate*1.05)
        
    def plot_bhm(ax: plt.Axes, x1, x2, y1, y2, max_rate, region):

        if x1 is not None:
            ax.plot(x1, y1, color='r',label=f"+Z {region}")
        if x2 is not None:
            ax.plot(x2, y2, color='k',label=f"-Z {region}")
        ax.set_xlabel("Time Approximate")
        ax.set_ylabel("BHM Event Rate")
        ax.set_ylim(0.1, max_rate*1.05)
        ax.set_yscale('symlog')
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
        max_rate = 0
        i += 1

        x1 = x2 = y1 = y2 = None # Placeholders to prevent UnboundLocalError

        if commonVars.root and region4.empty and region11.empty:
            try:
                ax = commonVars.rate_fig.axes[i-1]
            except IndexError:
                ax = commonVars.rate_fig.add_subplot(2, 1, i)  
            xfmt = mdates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(xfmt)
            plot_bhm(ax, None, None, None, None, 10, region_name)
            continue

        elif region4.empty and region11.empty:
            continue

        if not region4.empty:
            x1,y1,binx = uHTR4.get_rate(region4,bins=lumi_bins,start_time=start_time,uHTR11=False)
            if max(y1) > max_rate: max_rate = max(y1)

        if not region11.empty:
            x2,y2,_ = uHTR11.get_rate(region11,bins=lumi_bins,start_time=start_time,uHTR11=True)
            if max(y2) > max_rate: max_rate = max(y2)

        if lumi_bins is not None:
            lumi_ax = ax.twinx()
            for scale_factor in [10**i for i in range(-9, 6, 3)]:
                if np.min(delivered_lumi[np.nonzero(delivered_lumi)])*scale_factor >= 1:
                    break
            if max(delivered_lumi)*scale_factor > max_rate: max_rate = max(delivered_lumi)*scale_factor

            plot_lumi(lumi_ax, lumi_time, scale_factor, max_rate)

        plot_bhm(ax, x1, x2, y1, y2, max_rate, region_name)

        #if not region4.empty or not region11.empty:
        bhm_lines, bhm_labels = ax.get_legend_handles_labels()
        try:
            lumi_lines, lumi_labels = lumi_ax.get_legend_handles_labels()
        except UnboundLocalError:
            lumi_lines, lumi_labels = ([], [])
        
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
            try:
                ax = commonVars.rate_fig.axes[2*(i-1)]
            except IndexError:
                ax = commonVars.rate_fig.add_subplot(2, 1, i)  
            xfmt = mdates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(xfmt)

            if lumi_bins is not None:
                try:
                    lumi_ax = commonVars.rate_fig.axes[2*i-1]
                except:
                    lumi_ax = ax.twinx()
                plot_lumi(lumi_ax, lumi_time, scale_factor, max_rate)

            plot_bhm(ax, x1, x2, y1, y2, max_rate, region_name)

            bhm_lines, bhm_labels = ax.get_legend_handles_labels()
            try:
                lumi_lines, lumi_labels = lumi_ax.get_legend_handles_labels()
            except UnboundLocalError:
                lumi_lines, lumi_labels = ([], [])

            ax_bbox = ax.get_position()

            if not region4.empty or not region11.empty:
                # Seperate out the color map from the rest of the legend
                lines1, labels1 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                    if label.upper() not in beam_status_color_map.keys()])
                ax.legend(handles=lines1, labels=labels1, loc="upper left", bbox_to_anchor=(ax_bbox.x0+ax_bbox.width+0.05, ax_bbox.y0+ax_bbox.height), 
                          bbox_transform=commonVars.rate_fig.transFigure, frameon=1)

            if lumi_bins is not None:
                # color map stuff
                lines2, labels2 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                    if label.upper() in beam_status_color_map.keys()])
                lumi_ax.legend(handles=lines2, labels=labels2, loc="lower left", bbox_to_anchor=(ax_bbox.x0+ax_bbox.width+0.05, ax_bbox.y0), 
                          bbox_transform=commonVars.rate_fig.transFigure, title="LHC\nBeam Status", frameon=1)
        
        plt.close()

def get_poly(counts, width, color, label=""):
    """
    This saves a very small amount of time, but is *technically* faster. Generates the polygon for a bar chart
    based on histogram data.
    """
    verticies = []
    bin_edges = [i-width/2 for i in range(21)]
    for j in range(len(counts)): # Generates the verticies of the new polygon
        verticies.append((bin_edges[j], 0))
        verticies.append((bin_edges[j], counts[j]))
        verticies.append((bin_edges[j] + width, counts[j]))
        verticies.append((bin_edges[j] + width, 0))
        if j == len(counts) - 1:
            verticies.append((bin_edges[0], 0))
    #print(verticies)
    return Polygon(verticies, closed=True, facecolor=color, label=label)


def plot_lego_gui(uHTR, xbins, ybins, h):

    if uHTR == "4":
        try:
            ax3d = commonVars.lego_fig.axes[0]
        except IndexError:
            ax3d = commonVars.lego_fig.add_subplot(121, azim=50, elev=30, projection="3d", proj_type="persp")
    elif uHTR == "11":
        try:
            ax3d = commonVars.lego_fig.axes[1]
        except:
            ax3d = commonVars.lego_fig.add_subplot(122, azim=50, elev=30, projection="3d", proj_type="persp")
    
    if h is None: # Draw empty plot in gui if data empty
        ax3d.set_title(f"{beam_side[uHTR]}")
        ax3d.set_xlabel("TDC [a.u]")
        ax3d.set_ylabel("Ampl [a.u]")
        ax3d.set_zlabel("Events")
        ax3d.set_xlim3d(left=0, right=50)
        ax3d.set_ylim3d(bottom=0, top=180)
        return
    
    ax = lego(h, xbins, ybins, ax=ax3d)
    ax3d.set_title(f"{beam_side[uHTR]}")
    ax3d.set_xlabel("TDC [a.u]")
    ax3d.set_ylabel("Ampl [a.u]")
    ax3d.set_zlabel("Events")
    ax3d.set_xlim3d(left=0, right=50)
    ax3d.set_ylim3d(bottom=0, top=180)
    
    
def plot_adc_gui(ch, x, binx, binx_tick, adc_plt_tdc_width):

    try:
        # More complex ord mapping
        ax = commonVars.adc_fig.axes[int(20*(80 - ord(ch[0]))/3 + 10*(78-ord(ch[1]))/8 + int(ch[2:]) - 1)]
        #                                           +20 or +0   |      +10 or +0       |  + digits at end - 1   

        # Very complex way to map from channel name (ie PN01, MF05, PF03, etc. to an index position for subplot)
        # PN## occupies odd indices from 1 - 19, PF## occupies odd indices from 21 - 39
        # MN## occupies even indices from 2 - 20, MF## occupies even indices from 22 - 40
    except IndexError:
        ax = commonVars.adc_fig.add_subplot(20, 2, int((78-ord(ch[1]))*2.5 + 2*int(ch[2:]) - (ord(ch[0])-77)/3)) 
                                                    # +20 or +0    |   odd or even index  | -1 or -0

    textbox(0.6,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {adc_plt_tdc_width}", size=15, ax=ax)

    if x is None or len(x) == 0:
        ax.set_xlabel("ADC [a.u]")
        ax.set_xticks(binx_tick)
        ax.set_xticklabels(labels=binx_tick, rotation=45)
        x_val_range = (binx[-1] - binx[0])
        margin = ((x_val_range/10) - int(x_val_range/10))/2 + (x_val_range/10) // 2 # Cursed 5% margins
        # matplot lib uses """5%""" margins, but the right margin always seems to be +1 of the left margin
        # Both still add up to 10% regardless. Cursed but oh well
        ax.set_xlim(binx[0]-margin, binx[-1]+margin+1)
        return
    
    ax.hist(x,bins=binx+0.5, histtype="stepfilled")
    ax.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
    ax.set_xticks(binx_tick)
    ax.set_xticklabels(labels=binx_tick, rotation=45)
    ax.set_xlabel("ADC [a.u]")
    

def plot_tdc_gui(ch, x, peak, delay=0):

    try:
        ax = commonVars.tdc_fig.axes[int(20*(80 - ord(ch[0]))/3 + 10*(78-ord(ch[1]))/8 + int(ch[2:]) - 1)]
    except IndexError:
        # Cursed index notation, see plot_adc_gui above for explanation
        ax = commonVars.tdc_fig.add_subplot(20, 2, int((78-ord(ch[1]))*2.5 + 2*int(ch[2:]) - (ord(ch[0])-77)/3))

    textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15, ax=ax) 

    if x is None or len(x) == 0:
        margin = ((50/10) - int(50/10))/2 + (50/10) // 2 # Cursed 5% margins
        # Margins have a -1 on the left rather than a +1 on the right.
        ax.set_xlim(-margin-1, 50+margin)
        ax.set_xlabel("TDC [a.u]")
        return

    ax.hist(x, bins=np.arange(-0.5, 50, 1), histtype="step", color="r")
    ax.axvline(peak+delay,color='k',linestyle='--')
    ax.set_xlabel("TDC [a.u]")


def plot_occupancy_gui(uHTR, BR_bx, SR_bx):

    if uHTR == "4":
        try:
            ax = commonVars.occupancy_fig.axes[0]
        except IndexError:
            ax = commonVars.occupancy_fig.add_subplot(121)
    elif uHTR == "11":
        try:
            ax = commonVars.occupancy_fig.axes[1]
        except IndexError:
            ax = commonVars.occupancy_fig.add_subplot(122)

    if BR_bx is None:
        
        x_val_range = (3563.5 - -0.5)
        margin = x_val_range/20 # Sane 5% margins
        textbox(0.0,1.05,'Preliminary',15, ax=ax)
        textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=ax)
        ax.set_xlabel('BX ID')
        ax.set_ylabel('Events/1')
        ax.set_xlim(-0.5-margin, 3563.5+margin)
        return

    ax.set_yscale('log')
    textbox(0.0,1.05,'Preliminary',15, ax=ax)
    textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=ax)
    ax.set_xlabel('BX ID')
    ax.set_ylabel('Events/1')
    ax.hist(BR_bx, bins=np.arange(-0.5,3564,1), color='k', histtype="stepfilled", label="Collision $\&$ Activation")
    ax.hist(SR_bx, bins=np.arange(-0.5,3564,1), color='r', histtype="stepfilled", label="BIB")
    ax.legend(loc='upper right',frameon=1)
    
    return


def plot_tdc_stability_gui(uHTR, t_df, _mode, _mode_val, _std_dev, _sig):

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
        

        if uHTR == "4":
            try:
                violin_ax = commonVars.tdc_stability_fig.axes[0]
                vanilla_ax = commonVars.tdc_stability_fig.axes[1]
            except IndexError:
                violin_ax = commonVars.tdc_stability_fig.add_subplot(223)
                vanilla_ax = commonVars.tdc_stability_fig.add_subplot(221)
            CMAP = hw_info.get_uHTR4_CMAP()
        elif uHTR == "11":
            try:
                violin_ax = commonVars.tdc_stability_fig.axes[2]
                vanilla_ax = commonVars.tdc_stability_fig.axes[3]
            except IndexError:
                violin_ax = commonVars.tdc_stability_fig.add_subplot(224)
                vanilla_ax = commonVars.tdc_stability_fig.add_subplot(222)
            CMAP = hw_info.get_uHTR11_CMAP()
        
        channels = [ch for ch in CMAP.keys()]

        if t_df is None:
            # Violin filler
            textbox(0.0,1.11,'Preliminary',15, ax=violin_ax)
            textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=violin_ax)
            violin_ax.set_xticks(np.arange(20))
            violin_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            violin_ax.set_ylabel("TDC [a.u]",fontsize=15)
            violin_ax.set_xlabel("Channels",fontsize=15)
            margin = 0.5 # fixed margin
            violin_ax.set_ylim(0,15)
            violin_ax.set_xlim(-margin, 19+margin)
            
            # Vanilla filler
            textbox(0.0,1.11,'Preliminary',15, ax=vanilla_ax)
            textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=vanilla_ax)
            vanilla_ax.set_xticks(np.arange(20))
            vanilla_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            vanilla_ax.set_ylabel("TDC [a.u]",fontsize=15)
            vanilla_ax.set_xlabel("Channels",fontsize=15)
            vanilla_ax.set_ylim(0,15)
            margin = 19/20 # Sane 5% margins
            vanilla_ax.set_xlim(-margin, 19+margin)
            return

        # Violin plot
        sns.violinplot(ax=violin_ax, data = t_df,x='ch_name',y='tdc',cut=0,bw=.15,scale='count')
        textbox(0.0,1.11,'Preliminary',15, ax=violin_ax)
        textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=violin_ax)
        violin_ax.set_xticks(np.arange(20))
        violin_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
        violin_ax.set_ylabel("TDC [a.u]",fontsize=15)
        violin_ax.set_xlabel("Channels",fontsize=15)
        violin_ax.set_ylim(0,15)

        # Vanilla plot
        if _mode_val is not None:
            vanilla_ax.errorbar(channels, _mode, yerr=_std_dev, fmt='r.', ecolor='k', capsize=2, label="MPV of TDC")
            vanilla_ax.axhline(_mode_val,color='black',linewidth=2,linestyle='-.',label=r"MVP All Channels")
            vanilla_ax.fill_between(channels, _mode_val+_sig, _mode_val-_sig,color='orange',alpha=.5,label=r"$\sigma$ All Channels")
            vanilla_ax.legend(loc='upper right',frameon=True)

        textbox(0.0,1.11,'Preliminary',15, ax=vanilla_ax)
        textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=vanilla_ax)
        vanilla_ax.set_xticks(np.arange(20))
        vanilla_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
        vanilla_ax.set_ylabel("TDC [a.u]",fontsize=15)
        vanilla_ax.set_xlabel("Channels",fontsize=15)
        vanilla_ax.set_ylim(0,15)
    
    return


def plot_channel_events_gui(uHTR, channels, SR_events, BR_events):

    if uHTR == "4":
        try:
            ax = commonVars.ch_events_fig.axes[0]
        except IndexError:
            ax = commonVars.ch_events_fig.add_subplot(121)
        CMAP = hw_info.get_uHTR4_CMAP()
    elif uHTR == "11":
        try:
            ax = commonVars.ch_events_fig.axes[1]
        except IndexError:
            ax = commonVars.ch_events_fig.add_subplot(122)
        CMAP = hw_info.get_uHTR11_CMAP()

    if channels is None:
        
        textbox(0.0,1.05,'Preliminary', 15, ax=ax)
        textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax)
        ax.set_xticks(np.arange(20))
        ax.set_xticklabels(labels=[ch for ch in CMAP.keys()], rotation=45, ha="center", fontsize=8)
        ax.set_xlabel("Channels", fontsize=15)
        ax.set_ylabel("Events/1", fontsize=15)
        ax.set_xlim(-1, 20)
        return

    width = 0.9
    sr_poly = get_poly(SR_events.to_numpy(), width, "r", label="BIB") # You cannot just copy the same Artist into different axes because reasons (? matplotlib black magic ?)
    br_poly = get_poly(BR_events.to_numpy(), width, "k", label="Collision $\&$ Activation") # Not a big deal, generating polygons is very quick
    ax.add_patch(br_poly)
    ax.add_patch(sr_poly)
    textbox(0.0,1.05,'Preliminary', 15, ax=ax)
    textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax)
    ax.set_xticks(np.arange(20))
    ax.set_xticklabels(labels=channels, rotation=45, ha="center", fontsize=8)
    ax.set_xlabel("Channels", fontsize=15)
    ax.set_ylabel("Events/1", fontsize=15)
    ax.set_yscale("log")
    ax.set_xlim(-1, 20)
    ax.legend(loc='upper right', frameon=True)
    
    return