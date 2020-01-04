import math, operator
from functools import reduce
import numpy as np

def rms_same_shape(h1, h2):
    """
    This rms compares two vectors
    :param h1:
    :param h2:
    :return:
    """
    return math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, h1, h2))/len(h1))

def rms(v, m):
    """
    This RMS compares a vector with a matrix (a list of vectors). This should be much faster than iterating over the list of lists and computing the RMS for each one individually.
    :param v: A 1d numpy array
    :param m: A 2d numpy array (each row being the same shape as v)
    :return: a 1d numpy array of the same length as m which contains the RMSE between v and each row in m
    """
    return np.mean((m - v) ** 2, axis=1) ** .5

functions = {'rms': rms}