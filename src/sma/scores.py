import numpy as np


def crps_rows(samples, observations):
    """Estimateur empirique M², identique au kit, float64 et O(M log M)."""
    x = np.sort(np.asarray(samples, dtype=np.float64), axis=-1)
    y = np.asarray(observations, dtype=np.float64)
    n = x.shape[-1]
    w = (2*np.arange(1,n+1)-n-1)/n**2
    return np.abs(x-y[...,None]).mean(axis=-1)-np.sum(x*w,axis=-1)


def twcrps_rows(samples, observations, threshold, variable):
    h = np.maximum if variable == 'max' else np.minimum
    return crps_rows(h(samples,threshold),h(observations,threshold))


def torch_crps(samples, observations, alpha=0.95):
    """alpha fair + (1-alpha) empirical, moyenne sur le batch."""
    import torch
    m = samples.shape[-1]
    if m < 2: raise ValueError('Au moins deux membres pour le score fair')
    x = samples.sort(dim=-1).values
    w = 2*torch.arange(1,m+1,device=x.device,dtype=x.dtype)-m-1
    first = (x-observations[...,None]).abs().mean(dim=-1)
    spread = (x*w).sum(dim=-1)
    return (first - spread * (alpha/(m*(m-1))+(1-alpha)/(m*m))).mean()
