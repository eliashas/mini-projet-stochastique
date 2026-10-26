def sample(anchor,n,rng):
    return rng.choice(anchor['residuals'],size=n,replace=True)
