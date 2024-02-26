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

## Procedure
### Creating the Local Environment
This repo contains scripts for setting up all the module and path requirements for running the program. To create the environment, simply run the "makeEnv.sh" script and give it a directory to install the environment:
```bash
./makeEnv /path/to/env
```
After this, you will want to source the "setPaths.sh" file and give the path to the environment you just generated:
```bash
source ./setPaths.sh /path/to/env
```
This should additionally activate the virtual environment necessary to run the program. You can leave this environment at any time by typing "deactivate" into the terminal:
```bash
deactivate
```
### Using the Centralized Environment
WIP

---
After the environment is setup and activated, simply run final_analysis.py.

### SSH Setup
When the program attempts to grab information about a particular run, it will try to grab info from the OMS API. If it fails to connect from LXPLUS, the program will ssh (from terminal) into your CMS User account instead and contact the API from there. This should just work without modifiying your ssh config, however, in the event that it doesn't, you must have your ssh config setup with 'cmsusr' as the hostname for your cmsusr account. You can do this by pasting the following into your ssh config file and replacing 'username' with your own username:
```bash
Host cmsusr
        HostName cmsusr.cern.ch
        User username
```

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
