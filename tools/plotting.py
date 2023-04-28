# Written by Rohith Saradhy rohithsaradhy@gmail.com

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.dates as mdates
import tools.dt_conv as dt_conv


def textbox(x,y,text,size=14,frameon=False):
    plt.gca().text(x, y, text, transform=plt.gca().transAxes, fontsize=size,
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
    ax.bar3d(_xx.flatten(), _yy.flatten(), bottom.flatten(), width, depth, h.flatten(), shade=True,color='red')
    return ax  

def rate_plots(uHTR4,uHTR11,binx=300,N=-1,start_time=0,):
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
            orbit_value = (np.min(uHTR.orbit[uHTR.run == run])-uHTR.orbit[0])*3564*25*10**-6 + start_time
            x=dt_conv.get_date_time(orbit_value)
            ax.axvline(x,color='k',linestyle='--')
            # ax.text(x, 1.2, run, transform=ax.transAxes, fontsize=10,
            #         verticalalignment='top',rotation=90)



    # plot_runNo(uHTR4)
    # x,y = uHTR11.get_rate(uHTR11.BR)
    # plt.plot(x[:N], y[:N],color='k',label="-Z BR")

    
    # x,y = uHTR4.get_rate(uHTR4.BR)
    # plt.plot(x[:N], y[:N],color='g',label="+Z BR")

    x1,y1,binx_ =uHTR4.get_rate(uHTR4.SR,bins=binx,start_time=start_time,uHTR11=True)
    plt.plot(x1[:N], y1[:N],color='r',label="+Z SR")

    x2,y2,_ = uHTR11.get_rate(uHTR11.SR,bins=binx,start_time=start_time,uHTR11=True)
    plt.plot(x2[:N], y2[:N],color='k',label="-Z SR")





    # plt.xlabel("Time [Start Not Accurate] ")
    # plt.ylabel("Event Rate BIB [a.u]")
    # # plt.yscale('log')
    # plt.legend(loc=(1.1,0.8),frameon=1)
    # plt.yscale('log')

    ax2 = ax#.twinx()
    x1 = np.asarray(x1)
    x2 = np.asarray(x2)
    y1 = np.asarray(y1)
    y2 = np.asarray(y2)


    if x1.size < x2.size:
        x2 = x2[:x1.size]
        y2 = y2[:x1.size]
    elif x2.size < x1.size:
        x1 = x1[:x2.size]
        y1 = y1[:x2.size]

    # ax2.plot(x1, y1/y2,color='g',label="+Z/-Z Ratio")
    # ax2.plot(x2, y1/y2,color='b',label="+Z/-Z Ratio")
    # ax2.plot(x2, y1,color='k',label="+Z Side")
    # ax2.plot(x2, y1,color='r',label="-Z Side")


    
    ax2.legend(loc=(1.3,0.6),frameon=1)
    # ax2.set_ylim(0,5)
    ax2.set_ylabel("Events")
    plt.yscale("log")


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
    # ax2.legend(loc=(1.3,0.5),frameon=1)
    # ax2.set_yscale('log')
    plt.savefig(f"{uHTR4.figure_folder}/rates.png",dpi=300)
    