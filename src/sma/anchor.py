import numpy as np


def fit_anchor(co2, y):
    co2,y = np.asarray(co2,dtype=float),np.asarray(y,dtype=float)
    if len(y)<3 or not np.isfinite(y).all() or np.any(co2<=0): raise ValueError('Ancre: données invalides')
    b_raw,_ = np.polyfit(np.log(co2),y,1)
    b = max(float(b_raw),0.)
    a = float(np.mean(y-b*np.log(co2)))
    residuals = y-(a+b*np.log(co2))
    sigma_raw = float(np.std(residuals,ddof=2))
    sigma = max(sigma_raw,1e-6)
    return {'a':a,'b':b,'b_raw':float(b_raw),'sigma':sigma,'sigma_raw':sigma_raw,'scale_floor_active':sigma_raw<1e-6,'residuals':residuals,'z':residuals/sigma,'n':len(y),'log_co2_center':float(np.log(co2).mean()),'constraint_active':b_raw<0}


def predict_anchor(anchor, co2):
    return anchor['a']+anchor['b']*np.log(np.asarray(co2,dtype=float))


def bootstrap_anchor(co2,y,B=500,block_length=3,seed=7100):
    co2,y=np.asarray(co2,dtype=float),np.asarray(y,dtype=float)
    fit=fit_anchor(co2,y); residuals=fit['residuals']-np.mean(fit['residuals'])
    rng=np.random.default_rng(seed); n=len(y); a=[]; b=[]; raw=[]
    for _ in range(B):
        starts=rng.integers(0,n,size=int(np.ceil(n/block_length)))
        ix=((starts[:,None]+np.arange(block_length))%n).ravel()[:n]
        star=fit_anchor(co2,predict_anchor(fit,co2)+residuals[ix])
        a.append(star['a']); b.append(star['b']); raw.append(star['b_raw'])
    return {'a':np.asarray(a),'b':np.asarray(b),'b_raw':np.asarray(raw),'constraint_fraction':float(np.mean(np.asarray(raw)<0)),'co2_sha256':__import__('hashlib').sha256(co2.tobytes()).hexdigest(),'block_length':block_length,'replicates':B,'seed':seed,'fixed_co2':True}
