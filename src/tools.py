"""
Random tools that don't fit anywhere else
"""

def flatten(vals):
    """
    Takes a list of list and converts it into a list
    """
    return [x for y in vals for x in y]
