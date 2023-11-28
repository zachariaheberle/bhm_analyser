# Written by Zachariah Eberle zachariah.eberle@gmail.com

from urllib.request import urlopen
import pandas as pd
from urllib.error import URLError
import shlex
import numpy as np
from io import StringIO
import subprocess
from tools.profiler import Profiler
import tools.commonVars as commonVars
# import requests
# import json
# import socket

# class OMS_Proxy():

#     def __init__(self) -> None:
#         self.process = None

#     def create_proxy(self):
#         cmd = "ssh -v -N -L 1080:cmsusr:22"
#         #print("trying to connect")
#         self.process = subprocess.Popen(cmd.split(), bufsize=0, stderr=subprocess.PIPE, shell=False)
#         for line in self.process.stderr:
#             if "Local forwarding listening on 127.0.0.1 port 1080." in line.decode("utf-8").strip():
#                 return self
#             if "Connection closed by remote host" in line.decode("utf-8").strip():
#                 raise ConnectionAbortedError(line.decode("utf-8").strip())
#             elif "ssh: Could not resolve hostname" in line.decode("utf-8").strip():
#                 raise ConnectionRefusedError(line.decode("utf-8").strip())

#     def kill_proxy(self):
#         if self.process is not None:
#             print("termination attempted")
#             self.process.terminate()
#             self.process.wait(timeout=30)
#             self.process.kill()
        
#     def is_connected(self):
#         with socket.socket() as sock:
#             try:
#                 sock.connect(("127.0.0.1", 1080))
#                 return True
#             except socket.error:
#                 return False
    
#     def __exit__(self, exception_type, exception_value, exception_traceback):
#         self.kill_proxy()
    
#     def __enter__(self):
#         try:
#             self.create_proxy()
#         except:
#             self.kill_proxy()
#             raise

#         if self.process is not None:
#             return self
#         else:
#             raise ConnectionError("Failed to connect to cmsusr!")

def query_run(run: int = 375000):
    p = Profiler(name="query_run", parent=commonVars.profilers["get_run_info"])
    url = f"http://cmsoms.cms/agg/api/v1/runs/csv?filter[run_number][EQ]={run}"
    try:
        run_info = pd.read_csv(url).squeeze()

    except URLError:
        cmd = f"ssh cmsusr \"curl -g -s {url}\""
        process = subprocess.run(shlex.split(cmd), text=True, capture_output=True)
        run_info = pd.read_csv(StringIO(process.stdout)).squeeze()
    
    finally:
        p.start()
        if process.stderr != "" and "warning" not in process.stderr.lower():
            raise Exception(process.stderr)
        start = run_info.start_time
        end = run_info.end_time
        p.stop()
        return (int(pd.Timestamp(start).replace().timestamp()*1e3), int(pd.Timestamp(end).replace().timestamp()*1e3))


def get_lumisections(runs: list = [375000]):
    try:
        cmd = f"brilcalc lumi --byls --tssec --output-style csv --normtag /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_BRIL.json --begin {min(runs)} --end {max(runs)}"
        process = subprocess.run(shlex.split(cmd), text=True, capture_output=True)

    except (FileNotFoundError, OSError):
        cmd = f"ssh lxplus \"~/.local/bin/brilcalc lumi --byls --tssec --output-style csv --normtag /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_BRIL.json --begin {min(runs)} --end {max(runs)}\""
        process = subprocess.run(shlex.split(cmd), text=True, capture_output=True)
            

    finally:
        p = Profiler(name="get_lumisections", parent=commonVars.profilers["get_run_info"])
        p.start()
        if process.stderr != "" and "warning" not in process.stderr.lower():
            raise Exception(process.stderr)
        lumi_info = pd.read_csv(StringIO(process.stdout), 
                                names=["run:fill", "ls", "time", "beamstatus", "energy", "delivered_lumi", "recorded_lumi", "avgpu", "source"],
                                skiprows=2, skipfooter=3, engine="python").squeeze()
        if not lumi_info.empty:
            lumi_info[["run", "fill"]] = lumi_info["run:fill"].str.split(":", expand=True).astype(np.int32)
            lumi_info = lumi_info.drop(columns=["run:fill"])
        
        for run in runs:
            if run not in np.unique(lumi_info["run"].to_numpy()):
                # Create empty entries for runs that don't exist in brilcalc, this signals in our cache that we have
                # attempted to grab run info, but there is none
                df = pd.DataFrame({ 
                                   "ls" : [None],
                                 "time" : [None],
                           "beamstatus" : [None],
                               "energy" : [None],
                       "delivered_lumi" : [None],
                        "recorded_lumi" : [None],
                                "avgpu" : [None],
                               "source" : [None],
                                  "run" : [run],
                                 "fill" : [None]
                       })
                lumi_info = pd.concat((lumi_info, df))
        p.stop()
        return lumi_info