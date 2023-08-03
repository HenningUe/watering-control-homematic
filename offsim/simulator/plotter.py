
# -*- coding: iso-8859-15 -*-

import os
import itertools

from .. import actionstorage

# required imports
try:
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as font_manager
except ImportError, ex:
    msg = \
        (u'During import of "matplotlib" an error occured. '
         u'To plot signals the libraries "matplotlib" and "numpy" must be '
         u'installed on your system. Both libraries are open-source and can be '
         u'downloaded from the internet. Browse to the links below and select the '
         u'appropriate version (python 2.5/2.7). \n'
         u'matplotlib: http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-1.1.1/ \n'
         u'numpy: http://sourceforge.net/projects/numpy/files/NumPy/1.7.1/ \n'
         u'Original exception message is: {}').format(ex.message)
    raise ImportError(msg)


def plot_variables(title=None):
    print(u"Plotting curves. Plot is being opened ... ")

    fig = plt.figure(figsize=(12, 10), facecolor=u'w')
    if title is not None:
        fig.suptitle(_get_calling_mod_name(title), fontsize=20)

    ax_main = _create_axis(fig, actionstorage.actions.StorageType.main)
    ax_byhand = _create_axis(fig, actionstorage.actions.StorageType.byhand)
    ax_values = _create_axis(fig, actionstorage.actions.StorageType.value)

    axref = ax_main
    if ax_main is None:
        axref = ax_byhand

    # Now add the legend with some customizations.
    font_p = font_manager.FontProperties()
    font_p.set_size(u'small')

    # legend for curves
    leg_lines = axref.lines
    labels = [line.get_label() for line in leg_lines]
    legend1 = \
        fig.legend(leg_lines, labels, loc=u'lower right', prop=font_p,
                   bbox_to_anchor=(0.55, 0.05))
    legend1.draggable()
    for label in legend1.get_lines():
        label.set_linewidth(1)  # the legend line width
    # The frame is matplotlib.patches.Rectangle instance surrounding the legend.
    frame = legend1.get_frame()
    frame.set_facecolor(u'0.90')

    # legend for curves
    if ax_values is not None:
        leg_lines = ax_values.lines
        labels = [line.get_label() for line in leg_lines]
        legend1 = \
            fig.legend(leg_lines, labels, loc=u'lower left', prop=font_p,
                       bbox_to_anchor=(0.55, 0.05))
        legend1.draggable()
        for label in legend1.get_lines():
            label.set_linewidth(1)  # the legend line width
        # The frame is matplotlib.patches.Rectangle instance surrounding the legend.
        frame = legend1.get_frame()
        frame.set_facecolor(u'0.90')

    print(u"Plotting finished")
    plt.show()


def _create_axis(fig, storage_type, safe=dict()):
    actionstorage.set_storage_type(storage_type)
    channel_vals = \
        actionstorage.get_action_plot_values_grouped_by_channel()
    if not channel_vals:
        return None
    subpl_numb = 510 + (safe.get(u"ax_count", 0) + 1)
    kwargs = dict()
    if u"ax_first" in safe:
        # kwargs[u'sharex'], kwargs[u'sharey'] = [safe[u"ax_first"]] * 2
        kwargs[u'sharex'] = safe[u"ax_first"]
    ax1 = fig.add_subplot(subpl_numb, **kwargs)  # 212
    safe[u"ax_first"] = ax1
    safe[u"ax_count"] = safe.get(u"ax_count", 0) + 1

    # add vertical and horizontal grid lines
    ax1.xaxis.grid(color=u'gray', linestyle=u'dashed')
    ax1.yaxis.grid(color=u'gray', linestyle=u'dashed')
    # Adapt position and size of axis
    #     box = ax1.get_position()
    #     ax1.set_position([box.x0 * 0.53, box.y0 * 1.2 + box.height * 0.5, \
    #                      box.width * 1.15, box.height * 0.5])
    colors = _get_color_iterator()
    linestyle = u'solid'
    linewidth = 1.5
    if storage_type == actionstorage.actions.ActionType.value:
        # linestyle=u'dotted'
        linewidth = 3
    for channel in channel_vals:
        vals = channel_vals[channel]
        label = channel
        if u"alias" in vals:
            label = vals[u"alias"]
        ax1.plot(vals[u'time'], vals[u'values'],
                 colors.next(), linewidth=linewidth, label=label,
                 linestyle=linestyle)
    return ax1


def _get_color_iterator():
    # #        Chocolate(LightBrown)      #D2691E
    # #        SaddleBrown      #8B4513
    # #        Purple      #800080
    # #        OrangeRed      #FF4500
    # #        Orange(DarkYellow)      #FFA500
    # #        Lime(LightGreen)      #00FF00
    # #        GoldenRod(Okker)      #DAA520
    colors = itertools.cycle(
        [u'b', u'#D2691E', u'g', u'#800080', u'r', u'c', u'#FF4500', u'm',
         u'#8B4513', u'y', u'#00FF00', u'k', u'#DAA520', u'#FFA500'])
    return colors


def _get_calling_mod_name(filename):
    if not os.path.isabs(filename):
        return filename
    filename = os.path.split(filename)[1]
    filenamepure = os.path.splitext(filename)[0]
    return unicode(filenamepure)
