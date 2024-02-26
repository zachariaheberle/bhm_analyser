# BHM Analyser
## Introduction
### Self Trigger Tool
For a uHTR (backend), it is possible to capture data based on the signals seen in BHM. This "event-level" information can be used for detailed analysis of the detector performance. There are two such uHTR for the Beam Halo Monitors.

- uHTR4: acquires data from the +Z Side detectors looking for muons from Beam 1
- uHTR11: acquires data from the -Z Side detectors looking for muons from Beam 2

This repo provides a set of tools to parse the self-trigger tool data, and produce data quality plots from event level information. These plots can be used to derive cuts to isolate beam halo events from collision products and activation.

## Python Packages Required
```bash
pandas                     1.5.1
numpy                      1.24.4
matplotlib                 3.5.3
scienceplots               2.0.1
scipy                      1.9.1
seaborn                    0.12.2
```

## Additional Requirements
This program will additionally require a few other things to run, these include:
- Tk (this usually comes with python3)
- LaTeX
- ImageMagick
  - If on linux, you may have to disable some security policies to allow for .png -> .pdf conversions. From /etc/ImageMagick-#/policy.xml (where # is the ImageMagick version number), remove this line from the end of the file:
```bash
<policy domain="coder" rights="none" pattern="PDF" />
```


## Procedure
Run final_analysis.py with the required modules listed above. Note, if you run in a conda environment, text may not render properly. By default, the program will look for uHTR data folders in a subdirectory of the script titled "data". Make sure to create and place any data there for the program to work.

### SSH Setup
When the program attempts to grab information about a particular run, it will try to grab info from the OMS API. If it fails to connect from your local machine, the program will ssh (from terminal) into your CMS User account instead and contact the API from there. To ensure this works, you must have your ssh config setup with 'cmsusr' as the hostname for your cmsusr account. You can do this by pasting the following into your ssh config file and replacing 'username' with your own username:
```bash
Host cmsusr
        HostName cmsusr.cern.ch
        User username
        #ProxyCommand ssh -W %h:%p username@lxplus.cern.ch
```
You may or may not need a proxy command to connect to connect to cmsusr. If so, you can use an ssh connection to lxplus as a proxy by uncommenting the ProxyCommand line and filling in your username.

### brilcalc Setup
In order to grab lumisection data from CMS, we use the brilcalc tool on LXPLUS. In order to use this, you must have brilcalc set up on your LXPLUS user account. To set up brilcalc, simply enter this command on LXPLUS:
```bash
/cvmfs/cms-bril.cern.ch/brilconda310/bin/python3 -m pip install --user --upgrade brilws
```
This should install brilcalc in ~/.local/bin/brilcalc. 

---
## Status
This project is in its intial stage. If you find bugs, please reach out to zachariah.eberle@gmail.com or raise an issue.

### To-Do
- Run level plots
- Automate TDC Window [TDC Peaks are automatically derived]
---
