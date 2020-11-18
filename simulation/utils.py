import numpy as np
from inspect import getmembers
from types import FunctionType


def probability(rate, random_state):
    """
    The higher the rate, the more likely this function will return True (up till 1.0)
    Mock this function out to make behaviour deterministic.
    """
    if rate > 1.0:
        raise Exception("Rate has a maximum value of 1.0")
    return random_state.rand() < rate


"""
Helper functions from
https://stackoverflow.com/questions/192109/is-there-a-built-in-function-to-print-all-the-current-properties-and-values-of-a
to print all attributes of a class without me explicitly coding it out.
"""


def api(obj):
    return [name for name in dir(obj) if name[0] != '_']


def attrs(obj):
    disallowed_properties = {
        name for name, value in getmembers(type(obj))
        if isinstance(value, (property, FunctionType))}
    return {
        name: getattr(obj, name) for name in api(obj)
        if name not in disallowed_properties and hasattr(obj, name)}
