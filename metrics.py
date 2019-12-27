import math, operator
from functools import reduce

def rms(h1, h2):
    return math.sqrt(reduce(operator.add,map(lambda a,b: (a-b)**2, h1, h2))/len(h1))

functions = {'rms': rms}