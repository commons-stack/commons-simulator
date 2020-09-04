import numpy as np


def probability(rate):
    """
    The higher the rate, the more likely this function will return True (up till 1.0)
    Mock this function out to make behaviour deterministic.
    """
    if rate > 1.0:
        raise Exception("Rate has a maximum value of 1.0")
    return np.random.rand() < rate
