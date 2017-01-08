"""
Random tools that don't fit anywhere else
"""

import matplotlib as mp
import matplotlib.pyplot as plt

def flatten(vals):
    """
    Takes a list of list and converts it into a list
    """
    return [x for y in vals for x in y]

class TempParams: # pylint: disable=R0903
    """
    Allows for setting parameters temporarily (only font right now).
    """
    def __init__(self, new_font):
        self.new_font = new_font
        self.font = -1
    def __enter__(self):
        self.font = mp.rcParams['font.size']
        mp.rcParams.update({'font.size': self.new_font})
    def __exit__(self, typ, value, traceback):
        del typ, value, traceback
        mp.rcParams.update({'font.size': self.font})

def show_or_save(path, lgd):
    """
    Either shows or saves
    """
    if path is None:
        plt.show()
    else:
        plt.savefig(path, bbox_extra_artists=(lgd,), bbox_inches='tight', dpi=300)

def cached_property(prop):
    """
    Similar to `property`, but caches the result.
    """
    value = None
    have_value = False
    def cached(sel):
        nonlocal value, have_value
        if not have_value:
            value = prop(sel)
            have_value = True
        return value
    return property(cached)
