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
Run final_analysis.py OR
Follow analysis_template.ipynb step by step.

This framework requires the best estimate for the ADC, TDC cuts.  If the plots look incorrect, revisit the ADC & TDC cuts that are set. The TDC estimate needs to be within +/- 2.5ns of the peak
- Timing of the Beam Halo Events could change for various reasons
- If HV bias for the PMTs were optimized, one needs to rederive the ADC Thresholds

---
## Status
This project is in its intial stage. If you find bugs, please reach out to rohithsaradhy@gmail.com, zachariah.eberle@gmail.com, or raise an issue
The code needs special care with data that is acquired during specials scans. I suggest running the steps in bhm_analyser.analyse() individually to troubleshoot.

### To-Do
- Run level plots
- Correct orbit time to UTC [Talk to OMS system]
- Error Handling for channels with no data (Done)
- Automate derivation of ADC Peak without best estimate
- Automate TDC Window [TDC Peaks are automatically derived]
- XML configuration generator
- Hardcoded value of MN05 needs to be removed. General method to remove list of channels needs to be implemented.
---


## Python Packages Required
```bash
pandas                     1.4.0
numpy                      1.21.5
matplotlib                 3.5.1
scienceplots               1.0.8
scipy                      1.8.0
```
