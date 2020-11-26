import numpy as np
from inspect import getmembers
from types import FunctionType
from scipy.stats import expon, gamma



def new_probability_func(seed):
    random_state = np.random.RandomState(seed)
    def probability(rate):
        if rate > 1.0:
            raise Exception("Rate has a maximum value of 1.0")
        return random_state.rand() < rate
    return probability


def new_exponential_func(seed):
    random_state = np.random.RandomState(seed)
    def exponential(loc, scale):
        return expon.rvs(loc=loc, scale=scale, random_state=random_state)
    return exponential


def new_gamma_func(seed):
    random_state = np.random.RandomState(seed)
    def gamma_func(alpha, loc, scale):
        return gamma.rvs(alpha, loc=loc, scale=scale, random_state=random_state)
    return gamma_func


def new_random_number_func(seed):
    random_state = np.random.RandomState(seed)
    def random_number_func():
        return random_state.rand()
    return random_number_func


def new_choice_func(seed):
    random_state = np.random.RandomState(seed)
    def choice_func(choice_list):
        return random_state.choice(choice_list)
    return choice_func


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
