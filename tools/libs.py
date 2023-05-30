# Written by Rohith Saradhy rohithsaradhy@gmail.com
'''
Importing common libraries that are frequently used
'''
import numpy as np
import pandas as pd
import glob as glob
import tables as tables
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from   scipy import stats
from   copy  import deepcopy, copy
import scienceplots



#Importing the tools library
import tools.parser as parser
import tools.hw_info as hw_info
import tools.plotting as plotting
import tools.dt_conv as dt_conv
from   tools.bhm import bhm_analyser
import tools.calibration as calib
from   scipy.signal import find_peaks as fp
import tools.commonVars as commonVars

# setting matplot style; if science style is not installed comment it out! 
import matplotlib
matplotlib.style.available
matplotlib.style.use(['seaborn-darkgrid', "science"])
# plt.rcParams['figure.figsize'] = [4, 3]
plt.rcParams['figure.dpi'] = 300