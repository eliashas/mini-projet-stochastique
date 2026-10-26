import warnings
import numpy as np
from scipy.stats import genextreme


def fit(residuals,variable):
    r=np.asarray(residuals)*(-1 if variable=='min' else 1)
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter('always')
        c,loc,scale=genextreme.fit(r)
    if not np.isfinite([c,loc,scale]).all() or scale<=0: raise ValueError('Paramètres GEV invalides')
    logpdf=genextreme.logpdf(r,c,loc=loc,scale=scale)
    if not np.isfinite(logpdf).all(): raise ValueError('Données hors support GEV ajustée')
    low,high=genextreme.support(c,loc=loc,scale=scale)
    return {'c':float(c),'xi':float(-c),'loc':float(loc),'scale':float(scale),'support':[float(low) if np.isfinite(low) else '-inf',float(high) if np.isfinite(high) else '+inf'],'variable':variable,'log_likelihood':float(logpdf.sum()),'support_valid':True,'convergence':'SciPy fit retourne des paramètres finis; aucun statut optimiseur fourni','warnings':[str(w.message) for w in ww],'tail_warning':bool(abs(c)>.5),'convention':'genextreme.c = -xi'}


def sample(params,n,rng):
    x=genextreme.rvs(params['c'],loc=params['loc'],scale=params['scale'],size=n,random_state=rng)
    return x*(-1 if params['variable']=='min' else 1)
