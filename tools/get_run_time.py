# Written by Zachariah Eberle zachariah.eberle@gmail.com
"""
Important note: This script is only designed to be run on a CMS User Account, otherwise the link
to the OMS API will NOT work!! This script is meant to be run from the command line
of a CMS User Account with some arguments given in the command line -> python3 get_run_time.py -(run number).
"""
import sys
from urllib.request import urlopen

def csv_parser(data):
    """
    Converts string into comma seperated list, ensures lists like [item1,item2,item3]
    don't get seperated by str.split(",") into ['[item1', 'item2', 'item3]']
    This also means that this parser is *very* fragile, a change in the api formatting
    will break this.
    """
    unfiltered_data = data.split(",")
    filtered_data = []
    join_items = False
    for i, item in enumerate(unfiltered_data):
        if "[" in item and "]" not in item:
            join_items = True
            start = i
        elif "]" in item and "[" not in item and join_items:
            join_items = False
            filtered_data.append(unfiltered_data[start:i+1])
        elif not join_items:
            filtered_data.append(item)
    return filtered_data

def query_run(run: int = 325000):
    url = f"http://cmsoms.cms/agg/api/v1/runs/csv?filter[run_number][EQ]={run}"
    run_info = urlopen(url)
    time_index = []
    headers = csv_parser(run_info.readline().decode())
    values = csv_parser(run_info.readline().decode())
    for i, header in enumerate(headers):
        if "start_time" in header:
            start = values[i]
        elif "end_time" in header:
            end = values[i]
    return (start, end) # These are timestamp strings, they still need to be converted to UTC milliseconds

if __name__ == "__main__":
    try:
        min_run = sys.argv[1]
        start_UTC_timestamp = query_run(min_run)[0]
        print(start_UTC_timestamp)
    except IndexError:
        print("Error: No run argument given.")
    except ValueError:
        print("Error: Invalid run number given (not an integer).")
    except TypeError:
        print("Error: Run number doesn't exist!")
    except:
        print("Error: An unknown error occured!")