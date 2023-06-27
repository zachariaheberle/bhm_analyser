# Written by Zachariah Eberle zachariah.eberle@gmail.com
"""
Important note: This script is only designed to be run on a CMS User Account, otherwise the link
to the OMS API will NOT work!! This script is meant to be copied from the host and run from the command line
of a CMS User Account with some arguments given in the command line -> python3 get_run_time.py -(run number).
This does require that pandas is installed, on the CMS machine, but that seem to always be the case.
"""
import sys
import pandas

def query_run(run: int = 325000):
    url = f"http://cmsoms.cms/agg/api/v1/runs/csv?filter[run_number][EQ]={run}"
    run_info = pandas.read_csv(url).squeeze()
    start = run_info.start_time
    end = run_info.end_time
    start_UTC_ms = int(pandas.Timestamp(start).replace().timestamp()*1e3)
    end_UTC_ms = int(pandas.Timestamp(end).replace().timestamp()*1e3)
    return (start_UTC_ms, end_UTC_ms)

if __name__ == "__main__":
    try:
        min_run = sys.argv[1]
        start_UTC_ms = query_run(min_run)[0]
        print(start_UTC_ms)
    except IndexError:
        print("Error: No run argument given.")
    except ValueError:
        print("Error: Invalid run number given (not an integer).")
    except TypeError:
        print("Error: Run number doesn't exist!")
    except:
        print("Error: An unknown error occured!")