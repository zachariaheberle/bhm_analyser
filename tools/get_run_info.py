# Written by Zachariah Eberle zachariah.eberle@gmail.com

from urllib.request import urlopen
import pandas as pd
from urllib.error import URLError
import shlex
import numpy as np
from io import StringIO
import subprocess
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
    url = f"http://cmsoms.cms/agg/api/v1/runs/csv?filter[run_number][EQ]={run}"
    try:
        run_info = pd.read_csv(url).squeeze()

    except URLError:
        cmd = f"ssh cmsusr \"curl -g -s {url}\""
        process = subprocess.run(shlex.split(cmd), text=True, capture_output=True)
        if process.stderr != "" and "warning" not in process.stderr.lower():
            raise Exception(process.stderr)
        run_info = pd.read_csv(StringIO(process.stdout)).squeeze()
    
    start = run_info.start_time
    end = run_info.end_time
    return (int(pd.Timestamp(start).replace().timestamp()*1e3), int(pd.Timestamp(end).replace().timestamp()*1e3))


def get_lumisections(runs: list = [375000]):
    try:
        # We run two seperate brilcalcs because we want the delivered lumi data with the normtag, but want the beamstatus from the data without a normtag
        # Note: because we assume we are not running on lxplus (or linux for that matter), for this to work, ensure the brilcalc is added to your path
        cmd1 = f"brilcalc lumi --byls --tssec --output-style csv --normtag /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_BRIL.json --begin {min(runs)} --end {max(runs)}"
        cmd2 = f"brilcalc lumi --byls --tssec --output-style csv --begin {min(runs)} --end {max(runs)}"
        process1 = subprocess.run(shlex.split(cmd1), text=True, capture_output=True)
        process2 = subprocess.run(shlex.split(cmd2), text=True, capture_output=True)

        stdout = process1.stdout + process2.stdout
        stderr = process1.stderr + process2.stderr

    except (FileNotFoundError, OSError):
        # We can use ~ and && here since the ssh command is executed in the shell (bash I think?) of lxplus
        cmd = f"ssh lxplus \"~/.local/bin/brilcalc lumi --byls --tssec --output-style csv --normtag /cvmfs/cms-bril.cern.ch/cms-lumi-pog/Normtags/normtag_BRIL.json --begin {min(runs)} --end {max(runs)} && " +\
            f"~/.local/bin/brilcalc lumi --byls --tssec --output-style csv --begin {min(runs)} --end {max(runs)}\""
        process = subprocess.run(shlex.split(cmd), text=True, capture_output=True)

        stdout = process.stdout
        stderr = process.stderr
            

    if "Connection closed" in stderr:
        raise ConnectionAbortedError(stderr)
    elif stderr != "" and "warning" not in stderr.lower():
        raise Exception(stderr)
    norm_data, web_data, _ = stdout.split("#Summary:\n") # Split data from data collected with normtag and without normtag

    norm_lumi_info = pd.read_csv(StringIO(norm_data), 
                            names=["run:fill", "ls", "time", "beamstatus", "energy", "delivered_lumi", "recorded_lumi", "avgpu", "source"],
                            skiprows=2).squeeze()
    norm_lumi_info["normtag"] = [True]*len(norm_lumi_info["ls"])

    web_lumi_info = pd.read_csv(StringIO(web_data), 
                            names=["run:fill", "ls", "time", "beamstatus", "energy", "delivered_lumi", "recorded_lumi", "avgpu", "source"],
                            skiprows=4).squeeze()
    web_lumi_info["normtag"] = [False]*len(web_lumi_info["ls"])

    lumi_info = pd.concat((norm_lumi_info, web_lumi_info)).drop_duplicates(subset=["run:fill", "ls"], keep="first").reset_index(drop=True)

    if not lumi_info.empty:
        lumi_info[["run", "fill"]] = lumi_info["run:fill"].str.split(":", expand=True).astype(np.int32)
        lumi_info = lumi_info.drop(columns=["run:fill"])
    else:
        lumi_info["run"] = pd.Series(dtype=np.int32)
        lumi_info["fill"] = pd.Series(dtype=np.int32)
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
                            "normtag" : [None],
                                "run" : [run],
                                "fill" : [None],
                    })
            lumi_info = pd.concat((lumi_info, df))

    return lumi_info