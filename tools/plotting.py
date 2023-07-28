# Written by Rohith Saradhy rohithsaradhy@gmail.com

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import tools.dt_conv as dt_conv
import tools.commonVars as commonVars
from tools.profiler import Profiler



def textbox(x,y,text,size=14,frameon=False, ax=None):
    if ax == None:
        plt.gca().text(x, y, text, transform=plt.gca().transAxes, fontsize=size,
            verticalalignment='top'
    #          , bbox=dict(facecolor='white', alpha=0.5)
            )
        return
    ax.text(x, y, text, transform=ax.transAxes, fontsize=size,
            verticalalignment='top'
    #          , bbox=dict(facecolor='white', alpha=0.5)
            )


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

def rate_plots(uHTR4,uHTR11,binx=None,N=-1,start_time=0,):
    p = Profiler(name="rate_plots", parent=commonVars.profilers["Main Analysis"])
    p.start()
    '''
    After analysis step has been completed, and the plots look reasonable, you can get the rate plot
    uHTR4  --> BHM Analyser object for uHTR4 
    uHTR11 --> BHM Analyser object for uHTR11 
    Run Level needs to be implemented

    '''
    f,ax = plt.subplots()
    f.autofmt_xdate()
    xfmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)

    


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



    # plot_runNo(uHTR4)
    # x,y,_ = uHTR11.get_rate(uHTR11.BR)
    # plt.plot(x[:N], y[:N],color='k',label="-Z BR")

    
    # x,y,_ = uHTR4.get_rate(uHTR4.BR)
    # plt.plot(x[:N], y[:N],color='g',label="+Z BR")


    if not uHTR4.SR.empty: # basic checks to ensure data isn't empty
        x1,y1,binx_ = uHTR4.get_rate(uHTR4.SR,bins=binx,start_time=start_time,uHTR11=False)
        ax.plot(x1[:N], y1[:N],color='r',label="+Z SR")
    if not uHTR11.SR.empty:
        x2,y2,_ = uHTR11.get_rate(uHTR11.SR,bins=binx,start_time=start_time,uHTR11=True)
        ax.plot(x2[:N], y2[:N],color='k',label="-Z SR")

    if not uHTR4.SR.empty or not uHTR11.SR.empty: # SR plots
        ax.set_xlabel("Time Approximate ")
        ax.set_ylabel("Event Rate")
        ax.legend(loc=(1.1,0.8),frameon=1)
        ax.set_yscale('log')
        if start_time != 0:
            textbox(0.0,1.11, f"Start Date: {dt_conv.utc_to_string(start_time)}" , 14, ax=ax)

        #ax2 = ax#.twinx()
        # x1 = np.asarray(x1)
        # x2 = np.asarray(x2)
        # y1 = np.asarray(y1)
        # y2 = np.asarray(y2)

        # if x1.size < x2.size:
        #     x2 = x2[:x1.size]
        #     y2 = y2[:x1.size]
        # elif x2.size < x1.size:
        #     x1 = x1[:x2.size]
        #     y1 = y1[:x2.size]

        f.savefig(f"{uHTR4.figure_folder}/rates_SR.png",dpi=300)


        if commonVars.root: # I'm sure I can implement this better
            ax = commonVars.rate_fig.add_subplot(121)
            commonVars.rate_fig.autofmt_xdate()
            xfmt = mdates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(xfmt)
            if not uHTR4.SR.empty:
                ax.plot(x1[:N], y1[:N],color='r',label="+Z SR")
            if not uHTR11.SR.empty:
                ax.plot(x2[:N], y2[:N],color='k',label="-Z SR")
            ax.set_xlabel("Time Approximate ")
            ax.set_ylabel("Event Rate")
            ax.legend(loc=(1.1,0.8),frameon=1)
            ax.set_yscale('log')
            if start_time != 0:
                textbox(0.0,1.05, f"Start Date: {dt_conv.utc_to_string(start_time)}" , 15, ax=ax)

        plt.close()

    f,ax = plt.subplots()
    f.autofmt_xdate()
    xfmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(xfmt)


    if not uHTR4.CP.empty:
        x3,y3,_ = uHTR4.get_rate(uHTR4.CP,bins=binx,start_time=start_time,uHTR11=False)
        ax.plot(x3[:N], y3[:N],color='r',label="+Z CP")
    if not uHTR11.CP.empty:
        x4,y4,_ = uHTR11.get_rate(uHTR11.CP,bins=binx,start_time=start_time,uHTR11=True)
        ax.plot(x4[:N], y4[:N],color='k',label="-Z CP")
    
    if not uHTR4.CP.empty or not uHTR11.CP.empty: # CP plots
        ax.set_xlabel("Time Approximate ")
        ax.set_ylabel("Event Rate")
        ax.legend(loc=(1.1,0.8),frameon=1)
        ax.set_yscale('log')
        if start_time != 0:
            textbox(0.0,1.11, f"Start Date: {dt_conv.utc_to_string(start_time)}" , 14, ax=ax)

        # x3 = np.asarray(x3)
        # x4 = np.asarray(x4)
        # y3 = np.asarray(y3)
        # y4 = np.asarray(y4)

        # if x3.size < x4.size:
        #     x4 = x4[:x3.size]
        #     y4 = y4[:x3.size]
        # elif x4.size < x3.size:
        #     x3 = x3[:x4.size]
        #     y3 = y3[:x4.size]
        

        f.savefig(f"{uHTR4.figure_folder}/rates_CP.png",dpi=300)

        if commonVars.root: # There's a better way to do this
            ax = commonVars.rate_fig.add_subplot(122)
            commonVars.rate_fig.autofmt_xdate()
            xfmt = mdates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(xfmt)
            if not uHTR4.CP.empty:
                ax.plot(x3[:N], y3[:N],color='r',label="+Z CP")
            if not uHTR11.CP.empty:
                ax.plot(x4[:N], y4[:N],color='k',label="-Z CP")
            ax.set_xlabel("Time Approximate ")
            ax.set_ylabel("Event Rate")
            ax.legend(loc=(1.1,0.8),frameon=1)
            ax.set_yscale('log')
            if start_time != 0:
                textbox(0.0,1.05, f"Start Date: {dt_conv.utc_to_string(start_time)}" , 15, ax=ax)

        plt.close()

    # f,ax = plt.subplots()
    # f.autofmt_xdate()
    # xfmt = mdates.DateFormatter('%H:%M')
    # ax.xaxis.set_major_formatter(xfmt)

    # plt.plot(x2, y1/y2,color='b',label="+Z/-Z BHN Ratio")
    # plt.plot(x4, y3/y4,color='r',label="+Z/-Z CP Ratio")
    # plt.legend()
    # plt.ylabel("Ratios +Z/-Z")
   
    # N=-1
    # binx=300
    # # x,y = uHTR11.get_rate(uHTR11.SR)
    # # plt.plot(x[:N], y[:N],color='r',label="-Z SR")

    # x,y = uHTR11.get_rate(uHTR11.BR,bins=binx)
    # ax2.plot(x[:N], y[:N],color='g',label="-Z BR")


    # # x,y =uHTR4.get_rate(uHTR4.SR)
    # # plt.plot(x[:N], y[:N],color='b',label="+Z SR")

    # x,y = uHTR4.get_rate(uHTR4.BR,bins=binx)


    # ax2.plot(x[:N], y[:N],color='b',label="+Z BR")
    # ax2.set_ylabel("Event Rate Coll $\&$ Act [a.u]")
    # plt.legend(loc=(1.3,0.5),frameon=1)
    # plt.yscale('log')
    # plt.savefig(f"{uHTR4.figure_folder}/rates.png",dpi=300)
    # plt.close()
    p.stop()