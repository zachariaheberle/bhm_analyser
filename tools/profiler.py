# Written by Zachariah Eberle zachariah.eberle@gmail.com

"""
This tool is used to help keep track of how long things are taking in the program
"""
import time
#import copy
import numpy as np
import tools.commonVars as commonVars

class NotParentError(Exception):
    pass

class TimerError(Exception):
    pass

class Profiler():

    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children = [] # immediate children
        commonVars.profilers[name] = self # keep track of all the profilers in the system by name
        if isinstance(self.parent, Profiler):
            self.level = parent.level + 1
            self.parent.children.append(self)
        else:
            self.level = 0

    def start(self):
        print(" "*self.level*4 + f"Running {self.name}...")
        self.start_time = time.time()
    
    def stop(self):
        try: self.start_time
        except: raise TimerError("Cannot stop timer! Profiler.start() hasn't been called!")
        print(" "*self.level*4 + f"Completed {self.name}!")
        self.stop_time = time.time()
        self.total_time = self.stop_time - self.start_time
    
    # def _get_all_children(self):
    #     _children = copy.deepcopy(self.children)
    #     if _children == []:
    #         return
    #     for child in self.children:
    #         _children += [child._get_all_children()]
    #     return _children
    
    def _format_print(self):
        title = self.name + " Info"
        spacer = "-"
        parent_time_info = "#"*75 + "\n" + f"{title:{spacer}^{75}}\n" + f"Total Run Time: {self.total_time:.3f}s\n\nTotal Run Time Breakdown:\n\n"
        children_time_info = self._format_children_print(50)
        return parent_time_info + children_time_info
        
    def _format_children_print(self, l_adjust):
        spacer = "-"
        adjust = (l_adjust - self.level*4)
        output = " "*self.level*4 + f"{self.name+':':<{adjust}} |  Run Time: {self.total_time:.3f}s  |\n"
        output += f"{spacer:{spacer}<{len(output)}}\n"
        if self.children == []:
            return output
        for child in self.children:
            output = output + child._format_children_print(l_adjust)
        return output

    def dump(self, file):
        output = self._format_print()
        with open(file, "a") as fp:
            fp.write(output + "#"*75 + "\n\n\n\n")

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
