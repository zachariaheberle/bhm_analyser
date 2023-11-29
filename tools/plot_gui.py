# Written by Zachariah Eberle zachariah.eberle@gmail.com

"""
It is VERY essential that this is run in the main process, otherwise plots will never make it to gui
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import warnings
import tools.commonVars as commonVars
import tools.plotting as plotting
import tools.calibration as calib
import tools.hw_info as hw_info


beam_side = {
        "4" :"+Z Side",
        "11":"-Z Side"
    }

def plot_lego_gui(queue):

    print("running plot_lego_gui!")
    sides_complete = 0
    while sides_complete != 2: # Don't leave function until we have plotted both +Z (uHTR4) and -Z (uHTR11) sides
        uHTR, h, xbins, ybins = queue.get()
        print(sides_complete)

        if uHTR == "4":
            ax3d = commonVars.lego_fig.add_subplot(121, azim=50, elev=30, projection="3d", proj_type="persp")
        elif uHTR == "11":
            ax3d = commonVars.lego_fig.add_subplot(122, azim=50, elev=30, projection="3d", proj_type="persp")
        
        if h is None: # Draw empty plot in gui if data empty
            ax3d.set_title(f"{beam_side[uHTR]}")
            ax3d.set_xlabel("TDC [a.u]")
            ax3d.set_ylabel("Ampl [a.u]")
            ax3d.set_zlabel("Events")
            ax3d.set_xlim3d(left=0, right=50)
            ax3d.set_ylim3d(bottom=0, top=180)
            sides_complete += 1
            continue
        
        ax = plotting.lego(h, xbins, ybins, ax=ax3d)
        ax3d.set_title(f"{beam_side[uHTR]}")
        ax3d.set_xlabel("TDC [a.u]")
        ax3d.set_ylabel("Ampl [a.u]")
        ax3d.set_zlabel("Events")
        ax3d.set_xlim3d(left=0, right=50)
        ax3d.set_ylim3d(bottom=0, top=180)

        sides_complete += 1
    
    print("finished plot_lego_gui!")
    return

def plot_adc_gui(queue):
    print("running plot_adc_gui!")
    sides_complete = 0
    while sides_complete != 40: # Don't leave function until we have plotted both +Z (uHTR4) and -Z (uHTR11) sides (40 total plots)

        ch, x, binx, binx_tick, adc_plt_tdc_width = queue.get()

        # Very complex way to map from channel name (ie PN01, MF05, PF03, etc. to an index position for subplot)
        # PN## occupies odd indices from 1 - 19, PF## occupies odd indices from 21 - 39
        # MN## occupies even indices from 2 - 20, MF## occupies even indices from 22 - 40
        ax = commonVars.adc_fig.add_subplot(20, 2, int((78-ord(ch[1]))*2.5 + 2*int(ch[2:]) - (ord(ch[0])-77)/3)) 
                                                       # +20 or +0    |   odd or even index  | -1 or -0 

        if x is None:
            ax.set_xlabel("ADC [a.u]")
            ax.set_xticks(binx_tick)
            ax.set_xticklabels(labels=binx_tick, rotation=45)
            x_val_range = (binx[-1] - binx[0])
            margin = ((x_val_range/10) - int(x_val_range/10))/2 + (x_val_range/10) // 2 # Cursed 5% margins
            # matplot lib uses """5%""" margins, but the right margin always seems to be +1 of the left margin
            # Both still add up to 10% regardless. Cursed but oh well
            ax.set_xlim(binx[0]-margin, binx[-1]+margin+1)
            sides_complete += 1
            continue

        
        ax.hist(x,bins=binx+0.5, histtype="stepfilled")
        plotting.textbox(0.6,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {adc_plt_tdc_width}", size=15, ax=ax)
        ax.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
        ax.set_xticks(binx_tick)
        ax.set_xticklabels(labels=binx_tick, rotation=45)
        ax.set_xlabel("ADC [a.u]")

        sides_complete += 1
    print("finished plot_adc_gui!")
    return

def plot_tdc_gui(queue):

    print("running plot_tdc_gui!")
    sides_complete = 0
    while sides_complete != 40: # Don't leave function until we have plotted both +Z (uHTR4) and -Z (uHTR11) sides (40 total plots)

        ch, x, peak, delay = queue.get()

        # Cursed index notation, see plot_adc_gui above for explanation
        ax = commonVars.tdc_fig.add_subplot(20, 2, int((78-ord(ch[1]))*2.5 + 2*int(ch[2:]) - (ord(ch[0])-77)/3)) 

        if x is None:
            margin = ((50/10) - int(50/10))/2 + (50/10) // 2 # Cursed 5% margins
            # Margins have a -1 on the left rather than a +1 on the right.
            ax.set_xlim(-margin-1, 50+margin)
            ax.set_xlabel("TDC [a.u]")
            sides_complete += 1
            continue

        ax.hist(x, bins=np.arange(-0.5, 50, 1), histtype="step", color="r")
        plotting.textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15, ax=ax)
        ax.axvline(peak+delay,color='k',linestyle='--')
        ax.set_xlabel("TDC [a.u]")

        sides_complete += 1
    
    print("finished plot_tdc_gui!")
    return


def plot_occupancy_gui(queue):

    print("running plot_occupancy_gui!")
    sides_complete = 0
    while sides_complete != 2: # Don't leave function until we have plotted both +Z (uHTR4) and -Z (uHTR11) sides

        uHTR, BR_bx, SR_bx = queue.get()
        if uHTR == "4":
            ax = commonVars.occupancy_fig.add_subplot(121)
        elif uHTR == "11":
            ax = commonVars.occupancy_fig.add_subplot(122)

        if BR_bx is None:
            
            x_val_range = (3563.5 - -0.5)
            margin = x_val_range/20 # Sane 5% margins
            plotting.textbox(0.0,1.05,'Preliminary',15, ax=ax)
            plotting.textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=ax)
            ax.set_xlabel('BX ID')
            ax.set_ylabel('Events/1')
            ax.set_xlim(-0.5-margin, 3563.5+margin)
            sides_complete += 1
            continue

        ax.set_yscale('log')
        plotting.textbox(0.0,1.05,'Preliminary',15, ax=ax)
        plotting.textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=ax)
        ax.set_xlabel('BX ID')
        ax.set_ylabel('Events/1')
        ax.hist(BR_bx, bins=np.arange(-0.5,3564,1), color='k', histtype="stepfilled", label="Collision $\&$ Activation")
        ax.hist(SR_bx, bins=np.arange(-0.5,3564,1), color='r', histtype="stepfilled", label="BIB")
        ax.legend(loc='upper right',frameon=1)

        sides_complete += 1
    
    print("finished plot_occupancy_gui!")
    return

def plot_tdc_stability_gui(queue):
    print("running plot_tdc_stability_gui!")
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
        sides_complete = 0
        while sides_complete != 2: # Don't leave function until we have plotted both +Z (uHTR4) and -Z (uHTR11) sides

            uHTR, t_df, _mode, _mode_val, _std_dev, _sig = queue.get()
            

            if uHTR == "4":
                violin_ax = commonVars.tdc_stability_fig.add_subplot(223)
                vanilla_ax = commonVars.tdc_stability_fig.add_subplot(221)
                CMAP = hw_info.get_uHTR4_CMAP()
            elif uHTR == "11":
                violin_ax = commonVars.tdc_stability_fig.add_subplot(224)
                vanilla_ax = commonVars.tdc_stability_fig.add_subplot(222)
                CMAP = hw_info.get_uHTR11_CMAP()
            
            channels = [ch for ch in CMAP.keys()]

            if t_df is None:
                # Violin filler
                plotting.textbox(0.0,1.11,'Preliminary',15, ax=violin_ax)
                plotting.textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=violin_ax)
                violin_ax.set_xticks(np.arange(20))
                violin_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
                violin_ax.set_ylabel("TDC [a.u]",fontsize=15)
                violin_ax.set_xlabel("Channels",fontsize=15)
                margin = 0.5 # fixed margin
                violin_ax.set_ylim(0,15)
                violin_ax.set_xlim(-margin, 19+margin)
                
                # Vanilla filler
                plotting.textbox(0.0,1.11,'Preliminary',15, ax=vanilla_ax)
                plotting.textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=vanilla_ax)
                vanilla_ax.set_xticks(np.arange(20))
                vanilla_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
                vanilla_ax.set_ylabel("TDC [a.u]",fontsize=15)
                vanilla_ax.set_xlabel("Channels",fontsize=15)
                vanilla_ax.set_ylim(0,15)
                margin = 19/20 # Sane 5% margins
                vanilla_ax.set_xlim(-margin, 19+margin)
                sides_complete += 1
                continue

            # Violin plot
            sns.violinplot(ax=violin_ax, data = t_df,x='ch_name',y='tdc',cut=0,bw=.15,scale='count')
            plotting.textbox(0.0,1.11,'Preliminary',15, ax=violin_ax)
            plotting.textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=violin_ax)
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

            plotting.textbox(0.0,1.11,'Preliminary',15, ax=vanilla_ax)
            plotting.textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=vanilla_ax)
            vanilla_ax.set_xticks(np.arange(20))
            vanilla_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            vanilla_ax.set_ylabel("TDC [a.u]",fontsize=15)
            vanilla_ax.set_xlabel("Channels",fontsize=15)
            vanilla_ax.set_ylim(0,15)

            sides_complete += 1
    
    print("finished plot_tdc_stability_gui!")
    return


def plot_channel_events_gui(queue):

    print("running plot_channel_events_gui!")
    sides_complete = 0
    while sides_complete != 2: # Don't leave function until we have plotted both +Z (uHTR4) and -Z (uHTR11) sides

        uHTR, channels, SR_events, BR_events = queue.get()

        if uHTR == "4":
            ax = commonVars.ch_events_fig.add_subplot(121)
            CMAP = hw_info.get_uHTR4_CMAP()
        elif uHTR == "11":
            ax = commonVars.ch_events_fig.add_subplot(122)
            CMAP = hw_info.get_uHTR11_CMAP()

        if channels is None:
            
            plotting.textbox(0.0,1.05,'Preliminary', 15, ax=ax)
            plotting.textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax)
            ax.set_xticks(np.arange(20))
            ax.set_xticklabels(labels=[ch for ch in CMAP.keys()], rotation=45, ha="center", fontsize=8)
            ax.set_xlabel("Channels", fontsize=15)
            ax.set_ylabel("Events/1", fontsize=15)
            ax.set_xlim(-1, 20)
            sides_complete += 1
            continue

        width = 0.9
        sr_poly = plotting.get_poly(SR_events.to_numpy(), width, "r", label="BIB") # You cannot just copy the same Artist into different axes because reasons (? matplotlib black magic ?)
        br_poly = plotting.get_poly(BR_events.to_numpy(), width, "k", label="Collision $\&$ Activation") # Not a big deal, generating polygons is very quick
        ax.add_patch(br_poly)
        ax.add_patch(sr_poly)
        # ax.bar(channel_vals, BR_events, width=width, align="center",color='k',label = "Collision $\&$ Activation")
        # ax.bar(channel_vals, SR_events, width=width, align="center",color='r', label = "BIB")
        plotting.textbox(0.0,1.05,'Preliminary', 15, ax=ax)
        plotting.textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax)
        ax.set_xticks(np.arange(20))
        ax.set_xticklabels(labels=channels, rotation=45, ha="center", fontsize=8)
        ax.set_xlabel("Channels", fontsize=15)
        ax.set_ylabel("Events/1", fontsize=15)
        ax.set_yscale("log")
        ax.set_xlim(-1, 20)
        ax.legend(loc='upper right', frameon=True)

        sides_complete += 1
    
    print("finished plot_channel_events_gui!")
    return
