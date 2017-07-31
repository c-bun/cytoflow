#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from traits.api import HasStrictTraits, Str, provides

import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class ViolinPlotView(Base1DView):
    """Plots a violin plot -- a set of kernel density estimates
    
    Attributes
    ----------

    channel : Str
        the name of the channel we're plotting
        
    variable : Str
        the main variable by which we're faceting
    
    xfacet : Str 
        the conditioning variable for multiple plots (horizontal)
    
    yfacet : Str
        the conditioning variable for multiple plots (vertical)
    
    huefacet : Str
        the conditioning variable for multiple plots (color)
        
    huescale = Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the color bar, if there is one plotted
        
    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
        
        .. note: Should this be a param instead?
        
    Examples
    --------
    >>> viol = flow.ViolinPlotView()
    >>> viol.channel = 'Y2-A'
    >>> viol.variable = 'Dox'
    >>> viol.plot(ex)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.violin"
    friendly_id = "Violin Plot" 

    variable = Str
    
    def plot(self, experiment, **kwargs):
        """
        Plot a violin plot of a variable
        
        Parameters
        ----------
        
        orient : "v" | "h", optional
            Orientation of the plot (vertical or horizontal). 
        
        bw : {{'scott', 'silverman', float}}, optional
            Either the name of a reference rule or the scale factor to use when
            computing the kernel bandwidth. The actual kernel size will be
            determined by multiplying the scale factor by the standard deviation of
            the data within each bin.

        scale : {{"area", "count", "width"}}, optional
            The method used to scale the width of each violin. If ``area``, each
            violin will have the same area. If ``count``, the width of the violins
            will be scaled by the number of observations in that bin. If ``width``,
            each violin will have the same width.
            
        scale_hue : bool, optional
            When nesting violins using a ``hue`` variable, this parameter
            determines whether the scaling is computed within each level of the
            major grouping variable (``scale_hue=True``) or across all the violins
            on the plot (``scale_hue=False``).
            
        gridsize : int, optional
            Number of points in the discrete grid used to compute the kernel
            density estimate.

        inner : {{"box", "quartile", "point", "stick", None}}, optional
            Representation of the datapoints in the violin interior. If ``box``,
            draw a miniature boxplot. If ``quartiles``, draw the quartiles of the
            distribution.  If ``point`` or ``stick``, show each underlying
            datapoint. Using ``None`` will draw unadorned violins.
            
        split : bool, optional
            When using hue nesting with a variable that takes two levels, setting
            ``split`` to True will draw half of a violin for each level. This can
            make it easier to directly compare the distributions.
            
        See Also
        --------
        BaseView.plot : common parameters for data views
        """
        
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.variable:
            raise util.CytoflowViewError("Variable not specified")
        
        facets = [x for x in [self.xfacet, self.yfacet, self.huefacet, self.variable] if x]
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):

        kwargs.setdefault('orient', 'v')

        # since the 'scale' kwarg is already used
        kwargs['data_scale'] = xscale
                
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in grid.axes.flatten():
            if kwargs['orient'] == 'h':
                ax.set_xscale(xscale.name, **xscale.mpl_params)  
            else:
                ax.set_yscale(xscale.name, **xscale.mpl_params)  
            
        # this order-dependent thing weirds me out.      
        if kwargs['orient'] == 'h':
            violin_args = [self.channel, self.variable]
        else:
            violin_args = [self.variable, self.channel]
            
        if self.huefacet:
            violin_args.append(self.huefacet)
            
        grid.map(_violinplot,   
                 *violin_args,      
                 order = np.sort(experiment[self.variable].unique()),
                 hue_order = (np.sort(experiment[self.huefacet].unique()) if self.huefacet else None),
                 **kwargs)
        
        return {}
        
# this uses an internal interface to seaborn's violin plot.

from seaborn.categorical import _ViolinPlotter

def _violinplot(x=None, y=None, hue=None, data=None, order=None, hue_order=None,
                bw="scott", cut=2, scale="area", scale_hue=True, gridsize=100,
                width=.8, inner="box", split=False, orient=None, linewidth=None,
                color=None, palette=None, saturation=.75, ax=None, data_scale = None,
                **kwargs):
    
    if orient and orient == 'h':
        x = data_scale(x)
    else:
        y = data_scale(y)
            
    plotter = _ViolinPlotter(x, y, hue, data, order, hue_order,
                             bw, cut, scale, scale_hue, gridsize,
                             width, inner, split, orient, linewidth,
                             color, palette, saturation)

    for i in range(len(plotter.support)):
        if plotter.hue_names is None:       
            if plotter.support[i].shape[0] > 0:
                plotter.support[i] = data_scale.inverse(plotter.support[i])
        else:
            for j in range(len(plotter.support[i])):
                if plotter.support[i][j].shape[0] > 0:
                    plotter.support[i][j] = data_scale.inverse(plotter.support[i][j])

    for i in range(len(plotter.plot_data)):
        plotter.plot_data[i] = data_scale.inverse(plotter.plot_data[i])

    if ax is None:
        ax = plt.gca()

    plotter.plot(ax)
    return ax