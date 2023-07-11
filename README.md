# BHM Analyser
---
## Introduction
#### Self Trigger Tool
For a uHTR (backend), it is possible to capture data based on the signals seen in BHM. This "event-level" information can be used for detailed analysis of the detector performance. There are two such uHTR for the Beam Halo Monitors.

- uHTR4: acquires data from the +Z Side detectors looking for muons from Beam 1
- uHTR11: acquires data from the -Z Side detectors looking for muons from Beam 2

This repo provides a set of tools to parse the self-trigger tool data, and produce data quality plots from event level information. These plots can be used to derive cuts to isolate beam halo events from collision products and activation.

---

## Procedure
Run final_analysis.py in a conda environment with the required modules listed below. By default, the program will look for uHTR data folders in a subdirectory of the script titled "data". Make sure to create and place any data there for the program to work.

This framework requires the best estimate for the ADC, TDC cuts.  If the plots look incorrect, revisit the ADC & TDC cuts that are set. The TDC estimate needs to be within +/- 2.5ns of the peak
- Timing of the Beam Halo Events could change for various reasons
- If HV bias for the PMTs were optimized, one needs to rederive the ADC Thresholds

---
## Status
This project is in its intial stage. If you find bugs, please reach out to rohithsaradhy@gmail.com, zachariah.eberle@gmail.com, or raise an issue
The code needs special care with data that is acquired during specials scans. I suggest running the steps in bhm_analyser.analyse() individually to troubleshoot.

### To-Do
- Run level plots
- Correct orbit time to UTC [Talk to OMS system] (Done)
- Error Handling for channels with no data (Done)
- Automate derivation of ADC Peak without best estimate
- Automate TDC Window [TDC Peaks are automatically derived]
- XML configuration generator (Done in JSON, not XML)
- Hardcoded value of MN05 needs to be removed. General method to remove list of channels needs to be implemented. (Done)
---


## Python Packages Required
```bash
pandas                     1.5.1
numpy                      1.24.4
matplotlib                 3.5.3
scienceplots               2.0.1
scipy                      1.9.1
seaborn                    0.12.2
```
