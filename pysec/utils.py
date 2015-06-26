"""
utils.py

Utility functions for pysec
"""

def quarter_split(quarter):
    """
    Split a quarter (YYYYQ) into a tuple (YYYY, Q)

    Args:
        quarter: Str, YYYYQ
    
    Returns:
        ( Str, Str ): the year and quarter as separate strings
    """

    year = quarter[:4]
    q = quarter[-1:]
    return ( year, q )
