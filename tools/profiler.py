# Written by Zachariah Eberle zachariah.eberle@gmail.com

"""
This tool is used to help keep track of how long things are taking in the program
"""
import time
from datetime import datetime
#import copy
import numpy as np
import tools.commonVars as commonVars

class NotParentError(Exception):
    pass

class TimerError(Exception):
    pass

TIME_DUMP_FILE = commonVars.TIME_DUMP_FILE
LOG_DUMP_FILE = commonVars.LOG_DUMP_FILE

class Profiler():

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children = [] # immediate children
        self.l_adjust = 50
        commonVars.profilers[name] = self # keep track of all the profilers in the system by name
        if isinstance(self.parent, Profiler):
            self.level = parent.level + 1
            self.parent.children.append(self)
        else:
            self.level = 0

    def start(self):
        self.start_output = datetime.now().isoformat(timespec="milliseconds", sep=" ") + ":" + " "*(self.level+1)*4 + f"Running {self.name}...\n"
        print(self.start_output, end="")
        with open(LOG_DUMP_FILE, "a") as fp:
            fp.write(self.start_output)
        self.start_time = time.time()
    
    def stop(self):
        try: self.start_time
        except: raise TimerError("Cannot stop timer! Profiler.start() hasn't been called!")
        self.stop_time = time.time()
        self.stop_output = datetime.now().isoformat(timespec="milliseconds", sep=" ") + ":" + " "*(self.level+1)*4 + f"Completed {self.name}!\n"
        print(self.stop_output, end="")
        with open(LOG_DUMP_FILE, "a") as fp:
            fp.write(self.stop_output)
        self.total_time = self.stop_time - self.start_time
        with open(TIME_DUMP_FILE, "a") as fp:
            adjust = (self.l_adjust - self.level*4)
            fp.write(" "*(self.level)*4 + f"{self.name+':':<{adjust}} |  Run Time: {self.total_time:.3f}s  |\n")
    
    # def _get_all_children(self):
    #     _children = copy.deepcopy(self.children)
    #     if _children == []:
    #         return
    #     for child in self.children:
    #         _children += [child._get_all_children()]
    #     return _children
    
    def _format_time_print(self):
        title = self.name + " Info"
        spacer = "-"
        parent_time_info = "#"*75 + "\n" + f"{title:{spacer}^{75}}\n" + f"Total Run Time: {self.total_time:.3f}s\n\nTotal Run Time Breakdown:\n\n"
        children_time_info = self._format_time_children_print()
        return parent_time_info + children_time_info
    
    def _format_log_print(self):
        title = self.name + " Info"
        spacer = "-"
        parent_log_info = "#"*75 + "\n" + f"{title:{spacer}^{75}}\n" + "Subprocess Breakdown:\n\n"
        children_log_info = self._format_log_children_print()
        return parent_log_info + children_log_info
    
    def _format_log_children_print(self):
        spacer = "-"
        output = self.start_output
        if self.children == []:
            output += self.stop_output
            return output
        for child in self.children:
            output = output + child._format_log_children_print()
        return output + self.stop_output
        
    def _format_time_children_print(self):
        spacer = "-"
        adjust = (self.l_adjust - self.level*4)
        output = " "*(self.level)*4 + f"{self.name+':':<{adjust}} |  Run Time: {self.total_time:.3f}s  |\n"
        output += f"{spacer:{spacer}<{len(output)}}\n"
        if self.children == []:
            return output
        for child in self.children:
            output = output + child._format_time_children_print()
        return output

    def dump(self, time_info_file, log_info_file):
        time_output = self._format_time_print()
        log_output = self._format_log_print()
        with open(time_info_file, "a") as fp:
            fp.write(time_output + "#"*75 + "\n\n\n\n")
        with open(log_info_file, "a") as fp:
            fp.write(log_output + "#"*75 + "\n\n\n\n")

# def func_timer(name=None, parent=None):
#     """
#     Wrapper function that will automatically create and name a Profiler
#     when used with a function. Can input an optional name and parent function.
#     """
#     def decorator(func):

#         def wrap(*args, **kwargs):
#             nonlocal name
#             if name == None:
#                 name = func.__name__
#             profiler = Profiler(name, parent=parent)
#             profiler.start()
#             response = func(*args, **kwargs)
#             profiler.stop()
#             return response
        
#         return wrap
    
#     return decorator
