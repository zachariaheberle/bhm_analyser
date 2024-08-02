# Written by Rohith Saradhy rohithsaradhy@gmail.com and Zachariah Eberle zachariah.eberle@gmail.com

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np
import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, PathPatch, Polygon
from matplotlib.path import Path
from matplotlib.ticker import AutoLocator, MaxNLocator
from matplotlib.transforms import Transform
from matplotlib.backend_bases import ResizeEvent
import pandas as pd
import seaborn as sns
import warnings
import re

import tools.dt_conv as dt_conv
import tools.commonVars as commonVars
import tools.hw_info as hw_info
import tools.calibration as calib
import tools.dt_conv as dt_conv
from tools.bhm import bhm_analyser

beam_side = {
        "4" :"+Z Side",
        "11":"-Z Side"
    }

unit_labels = {
    1_000_000 : r"CMS Delivered Luminosity [$b^{-1}$]",
    1000 : r"CMS Delivered Luminosity [$mb^{-1}$]",
    1 : r"CMS Delivered Luminosity [$\mu b^{-1}$]",
    1/1000 : r"CMS Delivered Luminosity [$nb^{-1}$]",
    1/1_000_000 : r"CMS Delivered Luminosity [$pb^{-1}$]",
    1/1_000_000_000 : r"CMS Delivered Luminosity [$fb^{-1}$]",
}

beam_status_color_map = {
    "OTHER" : "#000000",
    "STABLE BEAMS" : "#00ff00",
    "FLAT TOP" : "#0000ff",
    "ADJUST" : "#ff0000",
    "SQUEEZE" : "#ffff00"
}

uHTR4_CMAP = hw_info.get_uHTR4_CMAP()
uHTR11_CMAP = hw_info.get_uHTR11_CMAP()


class EllipseAxes(Axes):

    class EllipticalTransform(Transform):
        """
        Performs the transformation from elliptical space (theta, r) to
        cartesian space (x, y)
        """

        input_dims = output_dims = 2

        def __init__(self, a, b):
            self.a = a
            self.b = b
            super().__init__()

        def normal(self, x_base, y_base):
            """
            Returns the normal slope as ellipse base points x_base, y_base (x_base, y_base must follow x_base**2/self.a**2 + y_base**2/self.b**2 == 1)
            (Basically only input points on the ellipse itself)
            """
            a2_x2 = self.a**2-x_base**2
            a2_x2[a2_x2 < 0] = 0 # Clamp down negative values to just be zero

            slopes = np.divide(self.a*np.sqrt(a2_x2), (self.b*x_base), where=np.abs(x_base) >= 1e-9) * np.sign(y_base) # Main calculation, ignores divide zero points
            return np.where(np.abs(x_base) < 1e-9,
                            1e50 * np.sign(y_base), 
                            slopes)
        
        def normal_vector(self, theta_r):
            """
            Yields normalized normal vectors pointing outwards from the ellipse (positive r)
            """
            theta, r = theta_r.T
            x_base, y_base = self.transform(np.column_stack([theta, np.zeros(theta.size)])).T
            slopes = self.normal(x_base, y_base)

            vectors = np.where(np.abs(x_base) <= 1e-9,
                                    np.stack([np.zeros(slopes.size), np.sign(slopes)]),
                                    np.sign(x_base) * np.stack([np.ones(slopes.size), slopes])
                                    ).T

            return np.where(np.abs(x_base) <= 1e-9, 
                                vectors.T,
                                vectors.T / np.hypot(*vectors.T)).T
        
        def tangent(self, x_base, y_base):
            """
            Returns the tangent slope as ellipse base points x_base, y_base (x_base, y_base must follow x_base**2/self.a**2 + y_base**2/self.b**2 == 1)
            (Basically only input points on the ellipse itself)
            """
            a2_x2 = self.a**2-x_base**2
            a2_x2[a2_x2 < 0] = 0 # Clamp down negative values to just be zero

            slopes = np.divide(-(self.b*x_base), (self.a*np.sqrt(a2_x2)), where=np.abs(y_base) >= 1e-9) * np.sign(y_base) # Main calculation, ignores divide zero points
            return np.where((np.abs(y_base) < 1e-9) | (a2_x2 == 0),
                            1e50 * np.sign(x_base), 
                            slopes)

        def tangent_vector(self, theta_r):
            """
            Yields normalized tangent vectors pointing in the direction of positive angle (counter clockwise)
            """

            theta, r = theta_r.T
            x_base, y_base = self.transform(np.column_stack([theta, np.zeros(theta.size)])).T
            slopes = self.tangent(x_base, y_base)

            vectors = np.where(np.abs(y_base) <= 1e-9,
                                    np.stack([np.zeros(slopes.size), np.sign(slopes)]),
                                    np.sign(-y_base) * np.stack([np.ones(slopes.size), slopes])
                                    ).T
                    
            return np.where(np.abs(y_base) <= 1e-9, 
                                vectors.T,
                                vectors.T / np.hypot(*vectors.T)).T
            

        # def get_arc_length(self, start_angle, stop_angle):
        #     m = 1 - (self.b/self.a)**2
        #     len_1 = ellipeinc(stop_angle - 0.5*np.pi, m)
        #     len_0 = ellipeinc(start_angle - 0.5*np.pi, m)
        #     return self.a*(len_1 - len_0)
        
        def transform_non_affine(self, theta_r):
            """
            Does the actual transform from elliptical space to cartesian space. Please don't call this directly, use
            EllipticalTransform.transform instead.
            """
            theta, r = theta_r.T

            r_ellipse = (self.b * self.a) / np.sqrt(self.b**2 * np.cos(theta)**2 + self.a**2 * np.sin(theta)**2)
            x_base = r_ellipse * np.cos(theta)
            y_base = r_ellipse * np.sin(theta)
            
            normal_slopes = self.normal(x_base, y_base)

            x = x_base + np.copysign(r / np.sqrt(1 + normal_slopes**2), x_base) * np.sign(r)
            y = y_base + np.copysign(r*normal_slopes / np.sqrt(1 + normal_slopes**2), y_base) * np.sign(r)

            y = np.where((x_base == 0), y + np.copysign(r, y_base), y) # Check conditions where slope == inf (x==0)
            
            x[np.abs(x) < 1e-9] = 0 # Clamp x and y values that are very small to be zero
            y[np.abs(y) < 1e-9] = 0

            

            return np.column_stack([x, y])

        def transform_path_non_affine(self, path):
            """
            Does the actual transform from elliptical space to cartesian space, but for Path objects instead. Please don't call this directly, use
            EllipticalTransform.transform_path instead.
            """
            return Path(self.transform(path.vertices), path.codes)

        def inverted(self):
            """
            returns the inverse of the elliptical transform (convert cartesian space to elliptical space)
            """
            return EllipseAxes.InvertedEllipticalTransform(a=self.a, b=self.b)

    class InvertedEllipticalTransform(Transform):
        """
        Performs the transformation from cartesian space (x, y) to
        elliptical space (theta, r)
        """

        input_dims = output_dims = 2

        def __init__(self, a, b):
            self.a = a
            self.b = b
            super().__init__()

        def find_min_dist_point(self, xy):
            """
            Finds the nearest point on the ellipse from some point x,y.
            Unfortunately, there's no closed solution to this, so we do
            a bit of approximating.

            That being said I have no clue how this works, all I know is that it does.
            """
            px, py = np.abs(xy.T)

            x_0, y_0 = xy.T

            tx = ty = 0.7071067811865475 # cos(pi / 4) 

            for i in range(3):
                x = self.a * tx
                y = self.b * ty

                ex = (self.a**2 - self.b**2) * tx**3 / self.a
                ey = (self.b**2 - self.a**2) * ty**3 / self.b

                rx = x - ex
                ry = y - ey

                qx = px - ex
                qy = py - ey

                r = np.hypot(ry, rx)
                q = np.hypot(qy, qx)

                tx = np.minimum(1, np.maximum(0, (qx * r / q + ex) / self.a))
                ty = np.minimum(1, np.maximum(0, (qy * r / q + ey) / self.b))
                t = np.hypot(ty, tx)
                tx /= t 
                ty /= t 

            return np.column_stack([np.copysign(self.a * tx, x_0), np.copysign(self.b * ty, y_0)])

        def transform_non_affine(self, xy):
            """
            Does the actual transform from cartesian space to elliptical space. Please don't call this directly, use
            InvertedEllipticalTransform.transform instead.
            """
            x, y = xy.T

            x_base, y_base = self.find_min_dist_point(xy).T

            x_base[np.abs(x_base) < 1e-9] = 0 # Clamp x and y values that are very small to be zero
            y_base[np.abs(y_base) < 1e-9] = 0

            r_dir = 2 * (x**2/self.a**2 + y**2/self.b**2 >= 1) - 1 # check if point is inside or outside ellipse
            # -1 == inside, 1 == outside

            r = np.hypot(x - x_base, y - y_base) * r_dir
            theta = (np.arctan2(y_base, x_base) + 2*np.pi) % (2 *np.pi) # Move bounds from [-pi, pi] to [0, 2pi]

            return np.column_stack([theta, r])

        def transform_path_non_affine(self, path):
            """
            Does the actual transform from cartesian space to elliptical space, but for Path objects instead. Please don't call this directly, use
            InvertedEllipticalTransform.transform_path instead.
            """
            return Path(self.transform(path.vertices), path.codes)

        def inverted(self):
            """
            returns the inverse of the inverse elliptical transform (basically a normal ellipse transform conversion from elliptical space to cartesian space)
            """
            return EllipseAxes.EllipticalTransform(a=self.a, b=self.b)



    def __init__(self, *args, ab_ratio=1, min_angle=0, max_angle=360, **kwargs):
        """
        Creates the axes and sets up initial theta, r values and x,y limits 
        """

        super().__init__(*args, **kwargs)

        self.ab_ratio = ab_ratio
        self.min_angle = np.deg2rad(min_angle)
        self.max_angle = np.deg2rad(max_angle)

        # Make sure the ylabel stays in the correct position regardless of window size
        self.cid = self.get_figure().canvas.mpl_connect('resize_event', self._update_ylabel_pos)

        self._canvas_width = 0
        self._canvas_height = 0

        self.clear()

    def clear(self):

        self._legend_handles = [] # List for storing handles for the legend since PatchCollections aren't automatically added to legends

        self._xticklabel_kwargs = {} # dictionaries to hold x/y (theta/r) ticklabel info
        self._yticklabel_kwargs = {}

        self._ylabel_kwargs = {}

        if hasattr(self, "a"):
            super().clear()

        # Set default settings
        if self.ab_ratio >= 1:
            self._transform = self.EllipticalTransform(a=1, b=1/self.ab_ratio)
        else:
            self._transform = self.EllipticalTransform(a=self.ab_ratio, b=1)
        self.a = self._transform.a
        self.b = self._transform.b

        self.axis("off")

        default_angles_deg = np.arange(0, 360, 45)
        self.set_xticks(np.deg2rad(default_angles_deg))
        self.set_xticklabels([f"{angle}\N{DEGREE SIGN}" for angle in default_angles_deg])

        default_r = np.arange(0, 1, 0.2)
        self.set_yticks(default_r)
        self.set_yticklabels(default_r)

        self.set_aspect("equal") # Please don't squash my circles matplotlib :(

        default_lim = (-2, 2)

        self.set_xlim(default_lim)
        self.set_ylim(default_lim)

        # These locators prevent crashing because matplotlib is dumb and if we don't override this,
        # it will try to place >1000 tick marks and crash if the user clicks on the plot
        # We don't show the x/y axis anyway, so this is fine
        self.xaxis.set_major_locator(MaxNLocator(5))
        self.xaxis.set_minor_locator(MaxNLocator(5))
        self.yaxis.set_major_locator(MaxNLocator(5))
        self.yaxis.set_minor_locator(MaxNLocator(5))

    def _find_r_ticks(self, max_r):
        """
        Finds the best tick mark locations according to matplotlib
        """
        return AutoLocator()._raw_ticks(0, max_r)
    
    def set_rlim(self, max_r):
        """
        Sets the maximum radius limit for the plot*

        *radius limit is extended by 1.05 times to avoid edge lines being prematurely cut off.
        """

        # Set longer side of ellipse to take up ~1/2 the screen
        if self.ab_ratio >= 1:
            self._transform = self.EllipticalTransform(a=max_r, b=max_r/self.ab_ratio)
        else:
            self._transform = self.EllipticalTransform(a=max_r*self.ab_ratio, b=max_r)
        self.a = self._transform.a
        self.b = self._transform.b
        
        self.set_yticks([tick for tick in self._find_r_ticks(max_r) if tick <= max_r])
        self.set_yticklabels([f"{tick:,.2f}".rstrip("0").rstrip(".") for tick in self.get_yticks()], **self._yticklabel_kwargs) # Remove annoying decimal point
        
        self.set_xlim(-max_r*1.05*2, max_r*1.05*2)
        self.set_ylim(-max_r*1.05*2, max_r*1.05*2)
        
        # Redraw new grid with new transform
        if self._grid:
            self._grid_settings["max_r"] = max_r
            self.grid(**self._grid_settings) # restore grid settings
    
    def get_rlim(self):
        """
        Gets the maximum radius limit for the plot in all 4 cardinal directions*

        *radius limit is extended by 1.05 times to avoid edge lines being prematurely cut off.
        """
        xlim = self.get_xlim()
        ylim = self.get_ylim()

        return (abs(xlim[0]/1.05) - self.a, abs(xlim[1]/1.05) - self.a,
                abs(ylim[0]/1.05) - self.a, abs(xlim[1]/1.05) - self.a) # Max r in -/+ x direction, max r in -/+ y direction

    def set_xticklabels(self, *args, **kwargs):
        """
        Grab any kwargs info (like fonts, fontsize, rotation, etc) pass into set_xticklabels (theta labels) to use for later
        """
        kwargs.setdefault("horizontalalignment", "center")
        kwargs.setdefault("verticalalignment", "center")
        labels = kwargs.pop("labels", [])

        self._xticklabel_kwargs = kwargs

        if labels != []:
            super().set_xticklabels(labels, **kwargs)
        else:
            super().set_xticklabels(*args, **kwargs)        
    
    def set_yticklabels(self, *args, **kwargs):
        """
        Grab any kwargs info (like fonts, fontsize, rotation, etc) pass into set_yticklabels (radius labels) to use for later
        """
        labels = kwargs.pop("labels", [])

        self._yticklabel_kwargs = kwargs

        if labels != []:
            super().set_yticklabels(labels, **kwargs)
        else:
            super().set_yticklabels(*args, **kwargs)

    def set_xlabel(self, xlabel, loc=None, **kwargs):
        """
        Sets the xlabel (theta label) of the plot. If loc is not specified, the default position will either at the midpoint of the angle limits OR at 90 degrees.
        """
            
        kwargs.setdefault("horizontalalignment", "center")
        kwargs.setdefault("verticalalignment", "center")

        if loc is None:
            if self.min_angle != 0 or self.max_angle != 2*np.pi:
                text_angle = self.max_angle - ((self.max_angle - self.min_angle) / 2)
            else:
                text_angle = np.pi / 2
            loc = self._transform.transform(np.column_stack([[text_angle], [-self.b / 2]]))[0]
        
        if hasattr(self, "_xlabel"):
            self._xlabel.remove()
            del self._xlabel

        self._xlabel = self.text(*loc, xlabel, **kwargs)
    
    def get_xlabel(self):
        """
        returns the theta label string
        """
        return self._xlabel.get_text()
    
    def _update_ylabel_pos(self, event: ResizeEvent):
        """
        To ensure the ylabel doesn't intersect with the yticks, we reconfigure its location every time we update the plot
        """

        if event.width != self._canvas_width or event.height != self._canvas_height: # double check if canvas changed size
            if not hasattr(self, "_ylabel_loc") or self._ylabel_loc is None:
                self.set_ylabel(self.get_ylabel(), **self._ylabel_kwargs)
        
        self._canvas_width = event.width
        self._canvas_height = event.height

    def set_ylabel(self, ylabel, loc=None, **kwargs):
        """
        Sets the ylabel (radius label) of the plot. If loc is not specified, the default position will be either at both edges of the angle limits OR at 22.5 degrees.
        """

        kwargs.setdefault("horizontalalignment", "center")
        kwargs.setdefault("verticalalignment", "top")
        kwargs.setdefault("rotation_mode", "anchor")
        self._ylabel_kwargs = kwargs



        rlim = self.get_rlim()

        if loc is None:
            self._ylabel_loc = None
            if self.min_angle != 0 or self.max_angle != 2*np.pi:

                text_angle = [self.min_angle, self.max_angle]
                r_pos = np.min(rlim) / 2
                theta_r = np.column_stack([text_angle, [r_pos]*2])


                tangent_vectors_normalized = self._transform.tangent_vector(theta_r)
                normal_vectors_normalized = self._transform.normal_vector(theta_r)
                xy = self._transform.transform(theta_r)
                
                # Find the max distance the text extends from the grid and move that distance + padding to place the radius label
                yticklabels = self.get_yticklabels()
                renderer = self.get_figure().canvas.get_renderer()
                longest_text: plt.Text = yticklabels[np.argmax([len(text.get_text()) for text in yticklabels])]

                # Get width of text box in data coordinates
                text_bbox = longest_text.get_window_extent(renderer=renderer).transformed(self.transData.inverted())
                text_data_width = text_bbox.width

                dist = min(self.a, self.b) / 8 + text_data_width
                
                text_rotations = np.rad2deg((np.arctan2(normal_vectors_normalized.T[1] * np.sign(xy.T[0]), normal_vectors_normalized.T[0] * np.sign(xy.T[0])) + 2*np.pi) % (2 *np.pi))
                loc = xy[0] - tangent_vectors_normalized[0] * dist, xy[1] + tangent_vectors_normalized[1] * dist

            else:
                text_angle = np.deg2rad(22.5)
                loc = self._transform.transform(np.column_stack([[text_angle], [rlim[1] * 1.1]]))[0]
                self._ylabel_loc = loc
    
        if hasattr(self, "_ylabel"):
            [text.remove() for text in self._ylabel]
            del self._ylabel
        
        if len(loc) == 1:
            self._ylabel = [self.text(*loc, ylabel, **kwargs)]
        else:
            self._ylabel = []
            for i in range(len(loc)):
                self._ylabel.append(self.text(*loc[i], ylabel, rotation=text_rotations[i], **kwargs))

    def get_ylabel(self):
        """
        returns the radius label string
        """
        return self._ylabel[0].get_text() # self._ylabel is always a list, but only one text string is ever stored in it. Safe to grab [0] value


    def legend(self, *args, **kwargs):
        """
        If handles is not explicitly passed to self.legend, uses its internal list of legend handles for the Axes.legend function,
        otherwise works just like Axes.legend
        """
        handles = kwargs.pop("handles", self._legend_handles)
        return super().legend(*args, handles=handles, **kwargs)


    def plot(self, theta, r, *args, **kwargs):
        """
        Performs a transform from theta, r coordinates to x, y, then plots as the normal Axes.plot would.
        """
        x, y = self._transform.transform(np.column_stack([theta, r])).T
        super().plot(x, y, *args, **kwargs)

            
    def bar(self, angle, height, width, bottom=0, align="mid", **kwargs):
        """
        Creates a bar chart based off of the (base) angle and height of the bar.
        Width does NOT track with angle, so will need to be adjusted accordingly.
        Otherwise functions as a normal Axes.bar function
        """

        # Coercing everything to numpy arrays makes my life easier
        angle = np.asarray(angle)
        height = np.asarray(height)
        width = np.asarray(width)

        if angle.size != height.size:
            raise ValueError(f"angle and height must have the same dimensions, but have size ({angle.size}) and ({height.size})")

        if (bar_max := np.max(height)) != 0:
            self.set_rlim(bar_max*1.2)
        else:
            self.set_rlim(1)

        bars = self._get_bar_polygons(height, *self._get_bar_corners(angle, height, width, align), **kwargs)
        self._legend_handles.append(Patch(**kwargs))
        self.add_collection(bars)

    def _get_bar_corners(self, angle: np.ndarray, height, width: np.ndarray, align: str):
        """
        Find the points on the ellipse that are *width* units away from the align point

        Note: the align edges of left vs. right are relative to angle direction (counter clockwise). 
        So left align looks like right align for y > 0, and left align for y < 0. 
        Likewise right align looks like left align for y > 0 and right align for y < 0
        """

        # Get xy position of angle on ellipse
        xy_base = self._transform.transform(np.column_stack([angle, np.zeros(angle.size)]))
        x_base, y_base = xy_base.T

        # Find normal slopes of points -> use this to widen our bar by *width*
        normal_slopes = self._transform.normal(x_base, y_base)
        
        # Yields normalized tangent vectors pointing in the direction of positive angle (counter clockwise) and normals points outward        
        tangent_vectors_normalized = self._transform.tangent_vector(np.column_stack([angle, height]))
        
        normal_vectors_normalized = self._transform.normal_vector(np.column_stack([angle, height]))

        if align == "mid":
            edge_plus, edge_minus = xy_base + tangent_vectors_normalized*width/2, xy_base - tangent_vectors_normalized*width/2
        elif align == "left":
            edge_plus, edge_minus = xy_base + tangent_vectors_normalized*width, xy_base
        elif align == "right":
            edge_plus, edge_minus = xy_base, xy_base + tangent_vectors_normalized*width
        
        corners = []

        # Find the nearest intersection point between normal line and ellipse
        # Solve the quadratic equation: alpha*x**2 + beta*x + gamma == 0
        for edge in (edge_minus, edge_plus):
            x_0 = edge.T[0]
            y_0 = edge.T[1]
            alpha = normal_slopes**2 + (self.b**2/self.a**2)
            beta = (2*normal_slopes*y_0) - (2*(normal_slopes**2)*x_0)
            gamma = ((normal_slopes**2)*x_0**2) + (y_0**2) - (self.b**2) - (2*normal_slopes*y_0*x_0)

            b2_4ac = np.subtract(beta**2, 4*alpha*gamma, out=np.zeros_like(alpha), where=np.abs(normal_slopes) < 1e15) # b**2 - 4ac (value under sqrt in quadratic formula)
            if np.min(b2_4ac) >= 0:
                x_plus = np.where(normal_vectors_normalized.T[0] != 0, (-beta + np.sqrt(b2_4ac)) / (2*alpha), x_0)
                x_minus = np.where(normal_vectors_normalized.T[0] != 0, (-beta - np.sqrt(b2_4ac)) / (2*alpha), x_0)
            else:
                raise ValueError("Bar width too large!")
            
            
            intersect_line = lambda x : normal_slopes*(x - x_0) + y_0 # Point slope formula

            def ellipse_line(x):
                a2_x2 = self.a**2 -x**2
                a2_x2[a2_x2 < 0] = 0 # I hate floating point inprecision
                return np.sign(y_base) * (self.b/self.a) * np.sqrt(a2_x2)

            min_dist_point_xy = np.where(np.hypot(x_0 - x_plus, y_0 - intersect_line(x_plus)) < np.hypot(x_0 - x_minus, y_0 - intersect_line(x_minus)),
                                        np.asarray([x_plus, intersect_line(x_plus)]),
                                        np.asarray([x_minus, intersect_line(x_minus)])
                                        ).T
            min_dist_point_xy = np.where((np.abs(normal_slopes) < 1e15), min_dist_point_xy.T, np.column_stack([x_0, ellipse_line(x_0)]).T).T # fix 90 and 270 deg points
            
            max_dist_point_xy = min_dist_point_xy + (normal_vectors_normalized.T*height).T
            
            for i in range(1): # Iteritively get closer to actual radius point
                r_diff = height - self._transform.inverted().transform(max_dist_point_xy).T[1]
                distance_diff_vector = (normal_vectors_normalized.T*r_diff).T
                max_dist_point_xy = max_dist_point_xy + distance_diff_vector
            
            corners.append(min_dist_point_xy)
            corners.append(max_dist_point_xy)

        return corners[0], corners[1], corners[3], corners[2] # [0] is minus_min, [1] is minus_max, [2] is plus_max, [3] is plus_min

    def _get_bar_polygons(self, height, p1, p2, p3, p4, **kwargs):
        """
        Creates the physical polygons (bars) that make up the bar chart and places those on the Axes
        """
        bar_list = []
        
        bottom_edge_minus_theta, _ = self._transform.inverted().transform(p1).T
        bottom_edge_plus_theta, _ = self._transform.inverted().transform(p4).T

        top_edge_minus_theta, _ = self._transform.inverted().transform(p2).T
        top_edge_plus_theta, _ = self._transform.inverted().transform(p3).T

        # Since the bottom edge of the bar plot is, well, an ellipse, we need an arc to follow along the ellipse base
        bottom_arc_theta = (np.where(bottom_edge_plus_theta - bottom_edge_minus_theta >= 0, 
                                np.linspace(bottom_edge_plus_theta, bottom_edge_minus_theta, 100, endpoint=True),
                                np.linspace(bottom_edge_plus_theta+(2*np.pi), bottom_edge_minus_theta, 100, endpoint=True)
                                ) % (2*np.pi)).T
        
        # Same thing for the top edge, since it too needs to follow a (non-elliptical) curve of constant radius
        top_arc_theta = (np.where(top_edge_plus_theta - top_edge_minus_theta > 0, 
                                np.linspace(top_edge_minus_theta, top_edge_plus_theta, 100, endpoint=True),
                                np.linspace(top_edge_minus_theta, top_edge_plus_theta+(2*np.pi), 100, endpoint=True)
                                ) % (2*np.pi)).T
        
        for i, (bottom_arc, top_arc) in enumerate(zip(bottom_arc_theta, top_arc_theta)):

            bottom_arc_xy = self._transform.transform(np.column_stack([bottom_arc, np.zeros(bottom_arc.size)]))
            top_arc_xy = self._transform.transform(np.column_stack([top_arc, np.ones(top_arc.size)*height[i]]))

            bar_list.append(Polygon(np.concatenate([top_arc_xy, bottom_arc_xy]), closed=True, **kwargs))
        
        return PatchCollection(bar_list, match_original=True)


    def _clear_grid(self):
        """
        Clears the gridlines, since these are drawn manually.
        """
        if hasattr(self, "_theta_grid"):
            self._theta_grid.remove()
            del self._theta_grid

        if hasattr(self, "_theta_labels"):
            [text.remove() for text in self._theta_labels]
            del self._theta_labels

        if hasattr(self, "_radius_grid"):
            self._radius_grid.remove()
            del self._radius_grid
        
        if hasattr(self, "_radius_labels"):
            [text.remove() for text in self._radius_labels]
            del self._radius_labels

        self._grid = False

    def grid(self, visible=True, which='major', axis='both', max_r=1, **kwargs):
        """
        Sets (and draws) the grid lines for the plot. Works more or less like Axes.grid
        
        Note, the "which" kwarg is simply there for compatibility, it doesn't actually do anything at the moment
        """

        kwargs.setdefault("edgecolor", "#B0B0B0")
        kwargs.setdefault("facecolor", "#B0B0B0")
        kwargs.setdefault("linewidth", 1)
        kwargs.setdefault("alpha", 1)

        self._grid_settings = {"visible": visible, "axis" : axis}
        self._grid_settings.update(kwargs)

        self._clear_grid()

        # Make sure this doesn't break, since this gets called before __init__ (Axes subclass shenanigans)
        if hasattr(self, "min_angle"):
            if visible:

                if axis in ['theta', 'both']:
                    self._draw_theta_grid(max_r, **kwargs)
                if axis in ['r', 'both']:
                    self._draw_radius_grid(**kwargs)
                
                self._grid = True
        
        else:
            super().grid(False)
            
    def _draw_theta_grid(self, max_r, **kwargs):
        """
        Draws specifically the theta gridlines and its labels (please don't call this directly)
        """
        patches = []
        labels = []

        label_kwargs = self._xticklabel_kwargs

        for tick, tick_label in zip(self.get_xticks(), self.get_xticklabels()):
            if (tick - self.min_angle) % (2*np.pi) <= (self.max_angle - self.min_angle) % (2*np.pi)\
                or (self.max_angle - self.min_angle) % (2*np.pi) == 0: # Check if angle within angle range

                tick_len = min(self.a, self.b) / 50

                theta_r_main = np.column_stack([[tick, tick], [0, max_r]])
                theta_r_tick = np.column_stack([[tick, tick], [-tick_len, 0]])

                theta_r_label = np.column_stack([[tick], [-2*tick_len]])

                patches.append(
                    PathPatch(self._transform.transform_path(Path(theta_r_main)), fill=False, **kwargs)
                    )
                patches.append(
                    PathPatch(self._transform.transform_path(Path(theta_r_tick)), fill=False, facecolor="#000000", linewidth=1, edgecolor="#000000")
                    )
                text_x, text_y = self._transform.transform(theta_r_label).T


                rotation = label_kwargs.pop("rotation", # rotate text to face inwards relative to ellipse
                            np.rad2deg((np.arctan2(*np.flip(self._transform.normal_vector(theta_r_main)[0] * np.sign(text_x))) + 2*np.pi) % (2 *np.pi))
                            )
                
                default_horizontalalignment = "left" if text_x < 0 else "right"

                horizontalalignment = label_kwargs.pop("horizontalalignment", default_horizontalalignment)
                rotation_mode = label_kwargs.pop("rotation_mode", "anchor")

                labels.append(
                    self.text(text_x[0], text_y[0], 
                              s=tick_label.get_text(),
                              horizontalalignment=horizontalalignment,
                              rotation=rotation,
                              rotation_mode=rotation_mode, 
                              **label_kwargs)
                    )
                
        self._theta_grid = PatchCollection(patches, match_original=True, zorder=2.5)
        self._theta_labels = labels
        self.add_collection(self._theta_grid)

    def _draw_radius_grid(self, **kwargs):
        """
        Draws specifically the radius gridlines and its labels (please don't call this directly)
        """
        patches = []
        labels = []

        label_kwargs = self._yticklabel_kwargs

        theta_vals = np.linspace(self.min_angle, self.max_angle, 2000, endpoint=True)

        yticks = self.get_yticks()

        rotation = label_kwargs.pop("rotation", None)
            
        ha_dict = {
            True: "right",
            False: "left"
        }

        horizontalalignment = label_kwargs.pop("horizontalalignment", None)
        verticalalignment = label_kwargs.pop("verticalalignment", "center")
        rotation_mode = label_kwargs.pop("rotation_mode", "anchor")

        if horizontalalignment is not None:
            ha_dict[True] = horizontalalignment
            ha_dict[False] = horizontalalignment

        for tick, tick_label in zip(yticks, self.get_yticklabels()):

            theta_r_main = np.column_stack([theta_vals, np.ones(theta_vals.size)*tick])

            if (self.max_angle - self.min_angle) % (2*np.pi) == 0: # If we have a full circle, radius labels at 22.5 deg, else at the ends of angle range
                theta_r_label = np.column_stack([[np.deg2rad(22.5)], [tick]])
            else:
                theta_r_label = np.column_stack([[self.min_angle, self.max_angle], [tick, tick]])
            
            text_loc_rot = self._locate_radius_textlabels(theta_r_label, dist=np.min(yticks[1:] - yticks[0:-1])*0.4, 
                                                   double_sided=bool((self.min_angle + self.max_angle)%(2*np.pi)))

            if rotation is None:
                [labels.append(self.text(text_x, text_y, 
                                s=tick_label.get_text(),
                                rotation=rot,
                                rotation_mode=rotation_mode,
                                horizontalalignment=ha_dict[text_x > 0],
                                verticalalignment=verticalalignment, 
                                **label_kwargs))
                                for (text_x, text_y), rot in 
                                zip(*text_loc_rot)]
            else:
                [labels.append(self.text(text_x, text_y, 
                                s=tick_label.get_text(),
                                rotation=rotation,
                                rotation_mode=rotation_mode,
                                horizontalalignment=ha_dict[text_x > 0],
                                verticalalignment=verticalalignment, 
                                **label_kwargs))
                                for (text_x, text_y), _ in 
                                zip(*text_loc_rot)]

            if tick == 0:
                patches.append(
                    PathPatch(self._transform.transform_path(Path(theta_r_main)), fill=False, facecolor="#000000", linewidth=1, edgecolor="#000000")
                )
            else:
                patches.append(
                    PathPatch(self._transform.transform_path(Path(theta_r_main)), fill=False, **kwargs)
                )

        self._radius_grid = PatchCollection(patches, match_original=True, zorder=2.5)
        self._radius_labels = labels
        self.add_collection(self._radius_grid)
    
    def _locate_radius_textlabels(self, theta_r, dist, double_sided=False):
        """
        Helper function to shift the radius textlabels outward based on their tangents
        """
        
        xy = self._transform.transform(theta_r)

        if double_sided:
            dist = min(self.a, self.b) / 25
            tangent_vectors_normalized = self._transform.tangent_vector(theta_r)
            return (
                xy - (np.sign(xy.T[0]) * tangent_vectors_normalized.T * dist).T,
                np.rad2deg((np.arctan2(tangent_vectors_normalized.T[1] * -np.sign(xy.T[1]), tangent_vectors_normalized.T[0] * -np.sign(xy.T[1])) + 2*np.pi) % (2 *np.pi))
                )
        
        normal_vectors_normalized = self._transform.normal_vector(theta_r)
        return xy + normal_vectors_normalized * dist, np.zeros(xy.shape[0])
            
  
    def format_coord(self, x, y):
        """
        Format the coordinates that appear in the bottom right
        when hovering over stuff to display location in theta, r coordinates
        """
        if x is None or y is None:
            theta_str = r_str = '???'
        else:
            # theta and r come out as len 1 lists
            theta, r = self._transform.inverted().transform(np.column_stack([x, y])).T 
            theta_str, r_str = f"{np.rad2deg(theta[0]):.3f}\N{DEGREE SIGN}", f"{r[0]:.3f}"
        return f"theta={theta_str} r={r_str}"# | x={x:.3f}, y={y:.3f}"


    def can_zoom(self):
        """
        Disable zooming functionality, may add feature later upon request
        """
        return False

    def can_pan(self):
        """
        Disable panning functionality, may add feature later upon request
        """
        return False
    
def tex_escape(text):
    """
    Converts a string input to a correctly escaped LaTeX output.
    Mainly used for the legend names for custom regions in the rate plots.
    """
    conv = {
        '&' : r'\&',
        '%' : r'\%',
        '$' : r'\$',
        '#' : r'\#',
        '_' : r'\_',
        '{' : r'\{',
        '}' : r'\}',
        '~' : r'\textasciitilde{}',
        '^' : r'\^{}',
        '\\' : r'\textbackslash{}',
        '<' : r'\textless{}',
        '>' : r'\textgreater{}',
        '|' : r'\textbar{}'
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=lambda item: - len(item))))
    return regex.sub(lambda match : conv[match.group()], text)

# def inverse_tex_escape(latex_text):
#     """
#     Converts a LaTeX string input to a non-escaped utf-8 output.
#     Mainly used for labeling in counting statistics of the rate plots.
#     """
#     conv = {
#         r'\&' : '&',
#         r'\%' : '%',
#         r'\$' : '$',
#         r'\#' : '#',
#         r'\_' : '_',
#         r'\{' : '{',
#         r'\}' : '}',
#         r'\textasciitilde{}' : '~',
#         r'\^{}' : '^',
#         r'\textbackslash{}' : '\\',
#         r'\textless{}' : '<',
#         r'\textgreater{}' : '>',
#         r'\textbar{}' : '|'
#     }
#     regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key=lambda item: - len(item))))
#     return regex.sub(lambda match : conv[match.group()], latex_text)


def textbox(x,y,text,size=14,frameon=False, ax=None):
    if ax == None:
        text_obj = plt.gca().text(x, y, text, transform=plt.gca().transAxes, fontsize=size,
            verticalalignment='top'
    #          , bbox=dict(facecolor='white', alpha=0.5)
            )
    else:
        text_obj = ax.text(x, y, text, transform=ax.transAxes, fontsize=size,
                verticalalignment='top'
        #          , bbox=dict(facecolor='white', alpha=0.5)
                )
    return text_obj


from mpl_toolkits.mplot3d.axes3d import Axes3D

# (fig, rect=None, *args, azim=-60, elev=30, zscale=None, sharez=None, proj_type='persp', **kwargs)[source]¶

def lego(h, xbins, ybins, ax=None, **plt_kwargs):
    '''Function to make a lego plot out of a 2D histo matplotlib/numpy generated
    - Provide explicit axes to choose where to plot it, otherwise the current axes will be used'''
      
    if ax==None:
        fig = plt.gcf() # get current axes
#         ax = fig.add_subplot(111,projection='3d')
        ax = Axes3D(fig, rect=None, azim=-60, elev=30, proj_type='persp')
    # look for this key in the axes properies
    # -> not-so-elegant check
    
    if ax.properties().get('xlim3d',None) == None :
        print('Error, ax is not 3d')
        return None
    
    _xx, _yy = np.meshgrid(xbins[:-1], ybins[:-1],indexing='ij')
    bottom = np.zeros_like(_xx)
    top = h
    width = xbins[1]-xbins[0]
    depth = ybins[1]-ybins[0]
    mask = (h.flatten() == 0)
    ax.bar3d(_xx.flatten()[~mask], _yy.flatten()[~mask], bottom.flatten()[~mask], width, depth, h.flatten()[~mask], shade=True,color='red')
    return ax  

def rate_plots(uHTR4: bhm_analyser, uHTR11: bhm_analyser, plot_regions: list[str] = ["SR", "CP"], start_time=0, 
               lumi_bins=None, delivered_lumi=None, beam_status=None, theCuts=[None, None],
               save_fig=True, by_time=True, by_lumi=True):
    '''
    After analysis step has been completed, and the plots look reasonable, you can get the rate plot
    uHTR4  --> BHM Analyser object for uHTR4 
    uHTR11 --> BHM Analyser object for uHTR11 
    Run Level needs to be implemented

    This function is in shambles and needs serious cleaning up

    '''

        #Plotting the Run No:
    # def plot_runNo(uHTR):
    #     for run in np.unique(uHTR.run)[:]:
    #         orbit_value = (np.min(uHTR.orbit[uHTR.run == run])-uHTR.orbit[0])*3564*25*10**-6 + start_time # time in mille-seconds
    #         x=dt_conv.get_date_time(orbit_value)
    #         ax.axvline(x,color='k',linestyle='--')
    #         # ax.text(x, 1.2, run, transform=ax.transAxes, fontsize=10,
    #         #         verticalalignment='top',rotation=90)

    def get_bhm_rate(region4: pd.DataFrame, region11: pd.DataFrame, lumi_bins, start_time):

        max_rate = 0

        if not region4.empty:
            x1,y1,binx1 = uHTR4.get_rate(region4, bins=lumi_bins, start_time=start_time)
            if max(y1) > max_rate: max_rate = max(y1)
            if f"+Z {region_id}" not in commonVars.bhm_bins.keys(): # cache this data for later use
                commonVars.bhm_bins[f"+Z {region_id}"] = binx1[1:] - binx1[:-1]
        else:
            x1 = y1 = binx1 = None

        if not region11.empty:
            x2,y2,binx2 = uHTR11.get_rate(region11, bins=lumi_bins, start_time=start_time)
            if max(y2) > max_rate: max_rate = max(y2)
            if f"-Z {region_id}" not in commonVars.bhm_bins.keys(): # cache this data for later use
                commonVars.bhm_bins[f"-Z {region_id}"] = binx2[1:] - binx2[:-1]
        else:
            x2 = y2 = binx2 = None
        
        return x1, y1, binx1, x2, y2, binx2, max_rate


    def plot_lumi(ax: plt.Axes, lumi_time, scale_factor, max_rate):
        ax.plot(lumi_time, delivered_lumi*scale_factor, color="#a600ff", label="CMS Lumi")
        ax.fill_between(lumi_time, np.where(beam_status=="STABLE BEAMS", max_rate, 0), 0, color=beam_status_color_map["STABLE BEAMS"], alpha=0.1, step="post", label="Stable Beams")
        ax.fill_between(lumi_time, np.where(beam_status=="ADJUST", max_rate, 0), 0, color=beam_status_color_map["ADJUST"], alpha=0.1, step="post", label="Adjust")
        ax.fill_between(lumi_time, np.where(beam_status=="SQUEEZE", max_rate, 0), 0, color=beam_status_color_map["SQUEEZE"], alpha=0.1, step="post", label="Squeeze")
        ax.fill_between(lumi_time, np.where(beam_status=="FLAT TOP", max_rate, 0), 0, color=beam_status_color_map["FLAT TOP"], alpha=0.1, step="post", label="Flat Top")
        ax.fill_between(lumi_time, np.where(beam_status=="OTHER", max_rate, 0), 0, color=beam_status_color_map["OTHER"], alpha=0.1, step="post", label="Other")
        ax.set_ylabel(unit_labels[scale_factor])
        ax.set_yscale('linear')
        ax.set_ylim(0, np.max(delivered_lumi)*scale_factor*1.05)
        

    def plot_bhm(ax: plt.Axes, x1, x2, y1, y2, max_rate, region_id):

        if x1 is not None:
            l, = ax.plot(x1, y1, color='r',label=label_from_region_id(region_id, "+Z"))
            l.set_url(f"+Z {region_id}") # I'm hiding region metadata in the url property of these lines, this is just used for tagging them for counting stats
        if x2 is not None:
            l, = ax.plot(x2, y2, color='k',label=label_from_region_id(region_id, "-Z"))
            l.set_url(f"-Z {region_id}")
        ax.set_xlabel("Time Approximate")
        ax.set_ylabel("BHM Event Rate")
        ax.set_ylim(0, max_rate*1.05)
        ax.set_yscale('linear')
        if start_time != 0:
            textbox(0.0,1.11, f"Start Date: {dt_conv.utc_to_string(start_time)}" , 14, ax=ax)
    

    def plot_lumi_v_bhm(ax1: plt.Axes, ax2: plt.Axes, cax1, cax2, binx1, binx2, y1, y2, delivered_lumi, lumi_bins, scale_factor, region_id):
        if delivered_lumi is not None:

            lumi = delivered_lumi*scale_factor
            lumi_bins = np.asarray(lumi_bins)

            if y1 is not None:
                min_bin = max(np.min(lumi_bins), np.min(binx1))
                max_bin = min(np.max(lumi_bins), np.max(binx1))

                lumi_cut = ((lumi_bins >= min_bin) & (lumi_bins <= max_bin)) # [:-1] here since bins also include the right edge
                bhm_cut  = ((binx1 >= min_bin) & (binx1 <= max_bin))[:-1]    # which y1 doesn't

                # np.finfo(np.float64).tiny is equal to the smallest (positve) 64bit float ~= 2.225e-308
                binx = np.linspace(np.finfo(np.float64).tiny, np.max(lumi), num=25) # easiest way to kick out zero values, just don't bin them :)
                # Plus, these plots stop making sense if we include zero values, since bhm_analyser.get_rate will return extra zeros for where there
                # are no events (like if we request only to get data from 12:00 to 18:00 or something, all events outside that range have their rates set to zero)

                if (max_y1 := np.max(y1)) < 25: # Prevent striping patterns if there are too many bins since BHM event rate is an integer
                    biny = np.arange(1, max_y1+1) # BHM event rate is always an integer, we can just use 1 here to exclude zeros
                else:
                    biny = np.linspace(1, max_y1, num=25)

                if max_bin == lumi_bins[-1] and max_bin == binx1[-1]: # lumi has extra bin at the end AND a value associated with it, ignore this for our plots
                    h, _binx, _biny, img = ax1.hist2d(lumi[lumi_cut][:-1], y1[bhm_cut], bins=(binx, biny), cmap='GnBu')
                else:
                    h, _binx, _biny, img = ax1.hist2d(lumi[lumi_cut], y1[bhm_cut], bins=(binx, biny), cmap='GnBu')

                fig: plt.Figure = ax1.get_figure()
                fig.colorbar(img, cax=cax1, ax=ax1, label="Count")
                
            
            if y2 is not None:
                min_bin = max(np.min(lumi_bins), np.min(binx2))
                max_bin = min(np.max(lumi_bins), np.max(binx2))

                lumi_cut = ((lumi_bins >= min_bin) & (lumi_bins <= max_bin)) # [:-1] here since bins also include the right edge
                bhm_cut  = ((binx2 >= min_bin) & (binx2 <= max_bin))[:-1]    # which y2 doesn't

                # np.finfo(np.float64).tiny is equal to the smallest (positve) 64bit float ~= 2.225e-308
                binx = np.linspace(np.finfo(np.float64).tiny, np.max(lumi), num=25) # easiest way to kick out zero values, just don't bin them :)
                # Plus, these plots stop making sense if we include zero values, since bhm_analyser.get_rate will return extra zeros for where there
                # are no events (like if we request only to get data from 12:00 to 18:00 or something, all events outside that range have their rates set to zero)

                if (max_y2 := np.max(y2)) < 25: # Prevent striping patterns if there are too many bins since BHM event rate is an integer
                    biny = np.arange(1, max_y2+1) # BHM event rate is always an integer, we can just use 1 here to exclude zeros
                else:
                    biny = np.linspace(1, max_y2, num=25)

                if max_bin == lumi_bins[-1] and max_bin == binx2[-1]: # lumi has extra bin at the end AND a value associated with it, ignore this for our plots
                    h, _binx, _biny, img = ax2.hist2d(lumi[lumi_cut][:-1], y2[bhm_cut], bins=(binx, biny), cmap='GnBu')
                else:
                    h, _binx, _biny, img = ax2.hist2d(lumi[lumi_cut], y2[bhm_cut], bins=(binx, biny), cmap='GnBu')
                
                fig: plt.Figure = ax2.get_figure()
                fig.colorbar(img, cax=cax2, ax=ax2, label="Count")

        ax1.set_xlabel(unit_labels[scale_factor])
        ax1.set_ylabel("BHM Event Rate")
        ax2.set_xlabel(unit_labels[scale_factor])
        ax2.set_ylabel("BHM Event Rate")
        ax1.set_title(label_from_region_id(region_id, "+Z"))
        ax2.set_title(label_from_region_id(region_id, "-Z"))




    def label_from_region_id(region_id, side):

        def cut_if_long(string, max_len=15):
            if len(string) > max_len:
                return string[0:max_len-3] + "..."
            return string
        
        num_chan = 0

        substrings = region_id.split("|")
        if len(substrings) == 1:
            return tex_escape(f"{side} {cut_if_long(region_id)}")        

        for substring in substrings:
            try:
                ch_name = substring.split("\'")[1]
            except IndexError: # If we get an index error, we probably aren't parsing channels anymore
                continue
            if side == "+Z":
                if ch_name in uHTR4_CMAP:
                    num_chan += 1
            elif side == "-Z":
                if ch_name in uHTR11_CMAP:
                    num_chan += 1

        if num_chan == 20:
            label = region_id[region_id.find("\'))") + 3:]
            if label[0:3] == " & ":
                return tex_escape(f"{side} {cut_if_long(label[3:])}")
            
            elif label.strip() == "":
                return tex_escape(f"{side} All Events")
            
            return tex_escape(f"{side} {cut_if_long(label)}")
        
        else:
            return tex_escape(f"{side} {cut_if_long(region_id)}")


    def get_legend_handles_labels(bhm_ax, lumi_ax, bhm_empty=False, lumi_empty=False):

        bhm_lines, bhm_labels = bhm_ax.get_legend_handles_labels()

        if not lumi_empty:
            lumi_lines, lumi_labels = lumi_ax.get_legend_handles_labels()
        else:
            lumi_lines, lumi_labels = ([], [])
        
        # Default values
        handles1 = labels1 = handles2 = labels2 = ()
        
        if not bhm_empty:
            # Seperate out the color map from the rest of the legend
            handles1, labels1 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                if label.upper() not in beam_status_color_map.keys()])

        if not lumi_empty:
            # color map stuff
            handles2, labels2 = zip(*[(line, label) for line, label in zip(bhm_lines+lumi_lines, bhm_labels+lumi_labels) 
                                if label.upper() in beam_status_color_map.keys()])
        
        return handles1, labels1, handles2, labels2
    







    for uHTR in (uHTR4, uHTR11): # Make sure getattr() and query don't break if we don't have any data and thus never generated the uHTR dataframe
        if len(uHTR.run) == 0:
            # Fill attributes with (empty) placeholder dataframes
            uHTR.df = uHTR.SR = uHTR.AR = uHTR.BR = uHTR.CP = pd.DataFrame(columns=("bx", "tdc", "tdc_2", "ch", "ch_name", "orbit", "run", "peak_ampl"))

    if delivered_lumi is not None:
        delivered_lumi = np.asarray(delivered_lumi)

    beam_status = np.asarray(beam_status)

    if lumi_bins is not None:
        lumi_time = [dt_conv.get_date_time(utc_ms) for utc_ms in lumi_bins]
    else:
        lumi_time = None
    
    region_df_list: list[tuple[pd.DataFrame, pd.DataFrame]] = []

    for region in plot_regions:
        if " & " in region:
            regions = region.split(" & ")
            uHTR4_df = pd.concat((getattr(uHTR4, regions[0]), getattr(uHTR4, regions[1])))
            uHTR11_df = pd.concat((getattr(uHTR11, regions[0]), getattr(uHTR11, regions[1])))
            region_df_list.append((uHTR4_df, uHTR11_df))
        else:
            region_df_list.append((getattr(uHTR4, region), getattr(uHTR11, region)))

    for i, (region_name, region4, region11) in enumerate([(plot_regions[0], region_df_list[0][0], region_df_list[0][1]), 
                                                          (plot_regions[1], region_df_list[1][0], region_df_list[1][1])]):

        if theCuts[i] is not None: # theCut should be a pandas query string
            if "orbit" in theCuts[i]:
                # Pandas gets very mad if you query with uint64, so we need to use the python engine to not crash
                # This is a slower engine, so only use it if we have to by first checking if orbit is in our cuts (since orbit is a uint64)
                # This issue doesn't exist for uint8, 16, or 32, which is really weird...
                # I should probably just change it to int64 when it's loaded from the data files to begin with, but we'll do this for now
                region4 = region4.query(theCuts[i], engine="python")
                region11 = region11.query(theCuts[i], engine="python")
            else:
                region4 = region4.query(theCuts[i])
                region11 = region11.query(theCuts[i])
        
        if region_name == "df":
             # if we remove all non-letters and our cut is 'orbitorbit', then we still are plotting all events, just with a time cut
            if theCuts[i] is None or re.sub('[^a-zA-Z]+', '', theCuts[i]) == "orbitorbit":
                region_name = region_id = "All Events"
            else:
                region_id = theCuts[i].strip()
        else:
            region_id = region_name

        bhm_empty = region4.empty and region11.empty
        lumi_empty = lumi_bins is None
        no_data = region4.empty and region11.empty and lumi_bins is None

        if no_data:

            if commonVars.root:
                if by_time:
                    try:
                        bhm_ax = commonVars.rate_time_fig.axes[2*i]
                    except IndexError:
                        bhm_ax = commonVars.rate_time_fig.add_subplot(2, 1, i+1) 
                    xfmt = mdates.DateFormatter('%H:%M')
                    bhm_ax.xaxis.set_major_formatter(xfmt)
                    plot_bhm(bhm_ax, None, None, None, None, 10, region_id)
                if by_lumi:
                    try:
                        by_lumi_ax1: plt.Axes = commonVars.rate_lumi_fig.axes[2*i]
                        by_lumi_ax2: plt.Axes = commonVars.rate_lumi_fig.axes[2*i+1]
                    except IndexError:
                        by_lumi_ax1: plt.Axes = commonVars.rate_lumi_fig.add_subplot(2, 2, 2*i+1)
                        by_lumi_ax2: plt.Axes = commonVars.rate_lumi_fig.add_subplot(2, 2, 2*i+2)
                    # God that's a lot of None...
                    plot_lumi_v_bhm(by_lumi_ax1, by_lumi_ax2, None, None, None, None, None, None, None, None, None, None)
            continue

        # x1/x2 -> time values for uHTR4/uHTR11 respectively
        # y1/y2 -> event rate for uHTR4/uHTR11 respectively
        x1, y1, binx1, x2, y2, binx2, max_rate = get_bhm_rate(region4, region11, lumi_bins, start_time)

        if not lumi_empty:
            # Pick the scaling such that we minimize the (logarithmic) distance between max lumi and max bhm rate
            scales = np.logspace(-9, 6, num=6, endpoint=True)
            scale_factor = scales[np.argmin(np.abs(np.log10(np.max(delivered_lumi)*scales) - np.log10(max_rate)))]


        if save_fig:

            if by_time:
                by_time_fig, bhm_ax = plt.subplots()
                by_time_fig.autofmt_xdate()
                xfmt = mdates.DateFormatter('%H:%M')
                bhm_ax.xaxis.set_major_formatter(xfmt)

                plot_bhm(bhm_ax, x1, x2, y1, y2, max_rate, region_id)

                if not lumi_empty:
                    lumi_ax: plt.Axes = bhm_ax.twinx()
                    plot_lumi(lumi_ax, lumi_time, scale_factor, np.max(delivered_lumi)*scale_factor)
                
                bhm_handles, bhm_labels, lumi_handles, lumi_labels = get_legend_handles_labels(bhm_ax, lumi_ax, bhm_empty, lumi_empty)

                if bhm_handles:
                    bhm_ax.legend(handles=bhm_handles, labels=bhm_labels, loc=(1.2,0.8), frameon=1)
                if lumi_handles:
                    lumi_ax.legend(handles=lumi_handles, labels=lumi_labels, loc=(1.2, 0), title="LHC Beam Status", frameon=1)

                by_time_fig.savefig(f"{uHTR4.figure_folder}/rates_{region_name}.png",dpi=300)
                

            if not lumi_empty and by_lumi:
                by_lumi_fig, by_lumi_axes = plt.subplots(2, 1)
                plot_lumi_v_bhm(by_lumi_axes[0], by_lumi_axes[1], None, None, binx1, binx2, y1, y2, delivered_lumi, lumi_bins, scale_factor, region_id)

                by_lumi_fig.savefig(f"{uHTR4.figure_folder}/rates_by_lumi_{region_name}.png",dpi=300)


            



        if commonVars.root:
            if by_time:
                try:
                    bhm_ax: plt.Axes = commonVars.rate_time_fig.axes[2*i]
                except IndexError:
                    bhm_ax: plt.Axes = commonVars.rate_time_fig.add_subplot(2, 1, i+1)

                xfmt = mdates.DateFormatter('%H:%M')
                bhm_ax.xaxis.set_major_formatter(xfmt)

                plot_bhm(bhm_ax, x1, x2, y1, y2, max_rate, region_id)

                if not lumi_empty:
                    try:
                        lumi_ax: plt.Axes = commonVars.rate_time_fig.axes[2*i+1]
                    except:
                        lumi_ax: plt.Axes = bhm_ax.twinx()
                    plot_lumi(lumi_ax, lumi_time, scale_factor, np.max(delivered_lumi)*scale_factor)
                
                bhm_handles, bhm_labels, lumi_handles, lumi_labels = get_legend_handles_labels(bhm_ax, lumi_ax, bhm_empty, lumi_empty)

                bhm_ax_bbox = bhm_ax.get_position()
                
                if bhm_handles:
                    bhm_ax.legend(handles=bhm_handles, labels=bhm_labels, loc="upper left", 
                                bbox_to_anchor=(bhm_ax_bbox.x0+bhm_ax_bbox.width+0.05, bhm_ax_bbox.y0+bhm_ax_bbox.height), 
                                bbox_transform=commonVars.rate_time_fig.transFigure, 
                                frameon=1)
                if lumi_handles:
                    lumi_ax.legend(handles=lumi_handles, labels=lumi_labels, loc="lower left", 
                                bbox_to_anchor=(bhm_ax_bbox.x0+bhm_ax_bbox.width+0.05, bhm_ax_bbox.y0), 
                                bbox_transform=commonVars.rate_time_fig.transFigure, 
                                title="LHC\nBeam Status", frameon=1)

                    

            if not lumi_empty and by_lumi:
                try:
                    # 4*i because when we add the color bars, the axes list looks like this: 
                    # [hist2d, hist2d, colorbar, colorbar, hist2d, hist2d, colorbar, colorbar]
                    by_lumi_ax1: plt.Axes = commonVars.rate_lumi_fig.axes[4*i]
                    by_lumi_ax2: plt.Axes = commonVars.rate_lumi_fig.axes[4*i+1]

                    by_lumi_cax1: plt.Axes = commonVars.rate_lumi_fig.axes[4*i+2] # colorbar axes
                    by_lumi_cax2: plt.Axes = commonVars.rate_lumi_fig.axes[4*i+3]
                except IndexError:
                    # Without color bars, pretend we're making a 2x2 figure
                    by_lumi_ax1: plt.Axes = commonVars.rate_lumi_fig.add_subplot(2, 2, 2*i+1)
                    by_lumi_ax2: plt.Axes = commonVars.rate_lumi_fig.add_subplot(2, 2, 2*i+2)

                    by_lumi_cax1 = None
                    by_lumi_cax2 = None
                plot_lumi_v_bhm(by_lumi_ax1, by_lumi_ax2, by_lumi_cax1, by_lumi_cax2,
                                binx1, binx2, y1, y2, delivered_lumi, lumi_bins, scale_factor, region_id)

        
        plt.close()



def plot_lego_gui(uHTR, xbins, ybins, h):

    if uHTR == "4":
        try:
            ax3d = commonVars.lego_fig.axes[0]
        except IndexError:
            ax3d = commonVars.lego_fig.add_subplot(121, azim=50, elev=30, projection="3d", proj_type="persp")
    elif uHTR == "11":
        try:
            ax3d = commonVars.lego_fig.axes[1]
        except:
            ax3d = commonVars.lego_fig.add_subplot(122, azim=50, elev=30, projection="3d", proj_type="persp")
    
    if h is None: # Draw empty plot in gui if data empty
        ax3d.set_title(f"{beam_side[uHTR]}")
        ax3d.set_xlabel("TDC [a.u]")
        ax3d.set_ylabel("Ampl [a.u]")
        ax3d.set_zlabel("Events")
        ax3d.set_xlim3d(left=0, right=50)
        ax3d.set_ylim3d(bottom=0, top=180)
        return
    
    ax = lego(h, xbins, ybins, ax=ax3d)
    ax3d.set_title(f"{beam_side[uHTR]}")
    ax3d.set_xlabel("TDC [a.u]")
    ax3d.set_ylabel("Ampl [a.u]")
    ax3d.set_zlabel("Events")
    ax3d.set_xlim3d(left=0, right=50)
    ax3d.set_ylim3d(bottom=0, top=180)
    
    
def plot_adc_gui(ch, x, binx, binx_tick, adc_plt_tdc_width):

    try:
        # More complex ord mapping
        ax = commonVars.adc_fig.axes[int(20*(80 - ord(ch[0]))/3 + 10*(78-ord(ch[1]))/8 + int(ch[2:]) - 1)]
        #                                           +20 or +0   |      +10 or +0       |  + digits at end - 1   

        # Very complex way to map from channel name (ie PN01, MF05, PF03, etc. to an index position for subplot)
        # PN## occupies odd indices from 1 - 19, PF## occupies odd indices from 21 - 39
        # MN## occupies even indices from 2 - 20, MF## occupies even indices from 22 - 40
    except IndexError:
        ax = commonVars.adc_fig.add_subplot(20, 2, int((78-ord(ch[1]))*2.5 + 2*int(ch[2:]) - (ord(ch[0])-77)/3)) 
                                                    # +20 or +0    |   odd or even index  | -1 or -0

    textbox(0.6,0.8,f"CH:{ch} \n $|$TDC - {calib.TDC_PEAKS[ch]} $| <$ {adc_plt_tdc_width}", size=15, ax=ax)

    if x is None or len(x) == 0:
        ax.set_xlabel("ADC [a.u]")
        ax.set_xticks(binx_tick)
        ax.set_xticklabels(labels=binx_tick, rotation=45)
        x_val_range = (binx[-1] - binx[0])
        margin = ((x_val_range/10) - int(x_val_range/10))/2 + (x_val_range/10) // 2 # Cursed 5% margins
        # matplot lib uses """5%""" margins, but the right margin always seems to be +1 of the left margin
        # Both still add up to 10% regardless. Cursed but oh well
        ax.set_xlim(binx[0]-margin, binx[-1]+margin+1)
        return
    
    ax.hist(x,bins=binx+0.5, histtype="stepfilled")
    ax.axvline(calib.ADC_CUTS[ch],color='r',linestyle='--')
    ax.set_xticks(binx_tick)
    ax.set_xticklabels(labels=binx_tick, rotation=45)
    ax.set_xlabel("ADC [a.u]")
    

def plot_tdc_gui(ch, x, peak, delay=0):

    try:
        ax = commonVars.tdc_fig.axes[int(20*(80 - ord(ch[0]))/3 + 10*(78-ord(ch[1]))/8 + int(ch[2:]) - 1)]
    except IndexError:
        # Cursed index notation, see plot_adc_gui above for explanation
        ax = commonVars.tdc_fig.add_subplot(20, 2, int((78-ord(ch[1]))*2.5 + 2*int(ch[2:]) - (ord(ch[0])-77)/3))

    textbox(0.5,.8,f'All BX, \n {ch} \n Ampl $>$ {calib.ADC_CUTS[ch]}',15, ax=ax) 

    if x is None or len(x) == 0:
        margin = ((50/10) - int(50/10))/2 + (50/10) // 2 # Cursed 5% margins
        # Margins have a -1 on the left rather than a +1 on the right.
        ax.set_xlim(-margin-1, 50+margin)
        ax.set_xlabel("TDC [a.u]")
        return

    ax.hist(x, bins=np.arange(-0.5, 50, 1), histtype="step", color="r")
    ax.axvline(peak+delay,color='k',linestyle='--')
    ax.set_xlabel("TDC [a.u]")


def plot_occupancy_gui(uHTR, BR_bx, SR_bx):

    if uHTR == "4":
        try:
            ax = commonVars.occupancy_fig.axes[0]
        except IndexError:
            ax = commonVars.occupancy_fig.add_subplot(121)
    elif uHTR == "11":
        try:
            ax = commonVars.occupancy_fig.axes[1]
        except IndexError:
            ax = commonVars.occupancy_fig.add_subplot(122)

    if BR_bx is None:
        
        x_val_range = (3563.5 - -0.5)
        margin = x_val_range/20 # Sane 5% margins
        textbox(0.0,1.05,'Preliminary',15, ax=ax)
        textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=ax)
        ax.set_xlabel('BX ID')
        ax.set_ylabel('Events/1')
        ax.set_xlim(-0.5-margin, 3563.5+margin)
        return

    ax.set_yscale('log')
    textbox(0.0,1.05,'Preliminary',15, ax=ax)
    textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=ax)
    ax.set_xlabel('BX ID')
    ax.set_ylabel('Events/1')
    ax.hist(BR_bx, bins=np.arange(-0.5,3564,1), color='k', histtype="stepfilled", label="Collision $\&$ Activation")
    ax.hist(SR_bx, bins=np.arange(-0.5,3564,1), color='r', histtype="stepfilled", label="BIB")
    ax.legend(loc='upper right',frameon=1)
    
    return


def plot_tdc_stability_gui(uHTR, t_df, _mode, _mode_val, _std_dev, _sig):

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
        

        if uHTR == "4":
            try:
                violin_ax = commonVars.tdc_stability_fig.axes[0]
                vanilla_ax = commonVars.tdc_stability_fig.axes[1]
            except IndexError:
                violin_ax = commonVars.tdc_stability_fig.add_subplot(223)
                vanilla_ax = commonVars.tdc_stability_fig.add_subplot(221)
            CMAP = uHTR4_CMAP
        elif uHTR == "11":
            try:
                violin_ax = commonVars.tdc_stability_fig.axes[2]
                vanilla_ax = commonVars.tdc_stability_fig.axes[3]
            except IndexError:
                violin_ax = commonVars.tdc_stability_fig.add_subplot(224)
                vanilla_ax = commonVars.tdc_stability_fig.add_subplot(222)
            CMAP = uHTR11_CMAP
        
        channels = [ch for ch in CMAP.keys()]

        if t_df is None:
            # Violin filler
            textbox(0.0,1.11,'Preliminary',15, ax=violin_ax)
            textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=violin_ax)
            violin_ax.set_xticks(np.arange(20))
            violin_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            violin_ax.set_ylabel("TDC [a.u]",fontsize=15)
            violin_ax.set_xlabel("Channels",fontsize=15)
            margin = 0.5 # fixed margin
            violin_ax.set_ylim(0,15)
            violin_ax.set_xlim(-margin, 19+margin)
            
            # Vanilla filler
            textbox(0.0,1.11,'Preliminary',15, ax=vanilla_ax)
            textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=vanilla_ax)
            vanilla_ax.set_xticks(np.arange(20))
            vanilla_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
            vanilla_ax.set_ylabel("TDC [a.u]",fontsize=15)
            vanilla_ax.set_xlabel("Channels",fontsize=15)
            vanilla_ax.set_ylim(0,15)
            margin = 19/20 # Sane 5% margins
            vanilla_ax.set_xlim(-margin, 19+margin)
            return

        # Violin plot
        sns.violinplot(ax=violin_ax, data = t_df,x='ch_name',y='tdc',cut=0,bw=.15,scale='count')
        textbox(0.0,1.11,'Preliminary',15, ax=violin_ax)
        textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=violin_ax)
        violin_ax.set_xticks(np.arange(20))
        violin_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
        violin_ax.set_ylabel("TDC [a.u]",fontsize=15)
        violin_ax.set_xlabel("Channels",fontsize=15)
        violin_ax.set_ylim(0,15)

        # Vanilla plot
        if _mode_val is not None:
            vanilla_ax.errorbar(channels, _mode, yerr=_std_dev, fmt='r.', ecolor='k', capsize=2, label="MPV of TDC")
            vanilla_ax.axhline(_mode_val,color='black',linewidth=2,linestyle='-.',label=r"MVP All Channels")
            vanilla_ax.fill_between(channels, _mode_val+_sig, _mode_val-_sig,color='orange',alpha=.5,label=r"$\sigma$ All Channels")
            vanilla_ax.legend(loc='upper right',frameon=True)

        textbox(0.0,1.11,'Preliminary',15, ax=vanilla_ax)
        textbox(0.5,1.11,f'{beam_side[uHTR]} [uHTR-{uHTR}]',15, ax=vanilla_ax)
        vanilla_ax.set_xticks(np.arange(20))
        vanilla_ax.set_xticklabels(labels=channels, rotation=45, ha='center',fontsize=8)
        vanilla_ax.set_ylabel("TDC [a.u]",fontsize=15)
        vanilla_ax.set_xlabel("Channels",fontsize=15)
        vanilla_ax.set_ylim(0,15)
    
    return


def plot_channel_events_gui(uHTR, channels, SR_events):

    if uHTR == "4":
        try:
            ax: EllipseAxes = commonVars.ch_events_fig.axes[0]
        except IndexError:
            ax: EllipseAxes = commonVars.ch_events_fig.add_subplot(121, axes_class=EllipseAxes, ab_ratio=1/.95, min_angle=-45, max_angle=225)
        CMAP = uHTR4_CMAP
    elif uHTR == "11":
        try:
            ax: EllipseAxes = commonVars.ch_events_fig.axes[1]
        except IndexError:
            ax: EllipseAxes = commonVars.ch_events_fig.add_subplot(122, axes_class=EllipseAxes, ab_ratio=1/.95, min_angle=-45, max_angle=225)
        CMAP = uHTR11_CMAP

    angle_map = commonVars.angle_map

    if channels is None:
        
        textbox(0.0,1.05,'Preliminary', 15, ax=ax)
        textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax)
        ax.set_xticks(angle_map)
        ax.set_xticklabels(labels=[ch for ch in CMAP.keys()], fontsize=8)
        ax.grid("both")
        ax.bar(angle_map, [0]*20, width=1, facecolor="white")
        ax.set_xlabel("Channels", fontsize=15)
        ax.set_ylabel("Event Count", fontsize=15)
        return


    ax.set_xticks(angle_map)
    ax.set_xticklabels(labels=channels, fontsize=8)
    ax.grid(axis="both")
    
    ax.bar(angle_map, SR_events.to_numpy(), width=np.max(SR_events.to_numpy()) / 5, facecolor="red", label="BIB")
    ax.set_xlabel("Channels", fontsize=15)
    ax.set_ylabel("Event Count", fontsize=15)

    textbox(0.0,1.05,'Preliminary', 15, ax=ax)
    textbox(0.5,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax)
    #textbox(1,1.05,f'{beam_side[uHTR]} [uHTR-{uHTR}]', 15, ax=ax, horizontalalignment="right")

    ax.legend(loc='upper right', frameon=True)
    
    return