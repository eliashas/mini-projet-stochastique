import numpy as np


def sample(anchor,n,rng):
    return anchor['sigma']*rng.standard_normal(n)
