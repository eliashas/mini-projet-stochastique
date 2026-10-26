"""Accès aux données par phase. La vérité n'est ouverte que dans l'adaptateur benchmark."""
from pathlib import Path
import shutil
import zipfile
import numpy as np
import pandas as pd
from .utils import ROOT,sha256,write_json,event

INPUTS=('yearly_temp_brest_train.csv','daily_temp_brest_train.csv','test_inputs.csv','yearly_future_co2.csv')
FULL_NAMES={'daily_temp_brest.csv','yearly_temp_brest.csv','yearly_future_co2.csv'}
SCENARIOS=('ssp1-2.6','ssp2-4.5','ssp5-8.5')


def prepare_kit(config,kit_dir=None):
    dest=ROOT/config['kit_dir']; source=Path(kit_dir or config['original_kit_dir'])
    (dest/'data').mkdir(parents=True,exist_ok=True)
    for name in INPUTS:
        target=dest/'data'/name
        original=source/'data'/name
        if not target.exists(): shutil.copy2(original,target)
        elif original.exists() and sha256(original)!=sha256(target): raise ValueError(f'Copie modifiée: {name}')
    for name in ('kit.py','exemple.py','LISEZMOI.md','CONTEXTE_POUR_LLM.md'):
        if source.resolve()!=dest.resolve(): shutil.copy2(source/name,dest/name)
    manifest={name:{'source':str(source/'data'/name),'copy':str((dest/'data'/name).relative_to(ROOT)),'sha256':sha256(dest/'data'/name)} for name in INPUTS}
    manifest['kit.py']={'source':str(source/'kit.py'),'sha256':sha256(dest/'kit.py')}
    write_json(ROOT/'data'/'provenance_competition.json',manifest)
    return dest


def load_competition(config):
    base=ROOT/config['kit_dir']/'data'
    return {name.removesuffix('.csv'):pd.read_csv(base/name,parse_dates=['valid_time']) for name in INPUTS}


def input_hashes(config):
    base=ROOT/config['kit_dir']/'data'
    return {name:sha256(base/name) for name in INPUTS}


def audit_data(config):
    data=load_competition(config); report={}
    expected={'yearly_temp_brest_train':(['valid_time','max','min','co2'],1940,2000,61),'daily_temp_brest_train':(['valid_time','mean'],1940,2000,22281),'test_inputs':(['valid_time','co2'],2001,2025,25),'yearly_future_co2':(['valid_time',*SCENARIOS],2026,2100,75)}
    for name,df in data.items():
        cols,lo,hi,n=expected[name]
        if list(df.columns)!=cols or len(df)!=n: raise ValueError(f'Colonnes/taille inattendues {name}')
        if df.isna().any().any() or df.valid_time.duplicated().any(): raise ValueError(f'Valeur manquante/doublon {name}')
        if not df.valid_time.is_monotonic_increasing: raise ValueError('Ordre temporel invalide')
        if df.valid_time.dt.year.min()!=lo or df.valid_time.dt.year.max()!=hi: raise ValueError('Période invalide')
        numeric=df.drop(columns='valid_time').to_numpy(dtype=float)
        if not np.isfinite(numeric).all(): raise ValueError('Valeurs non finies')
        co2cols=[c for c in df if c=='co2' or c in SCENARIOS]
        if co2cols and not (df[co2cols]>0).all().all(): raise ValueError('CO₂ non positif')
        if name.startswith('daily'):
            if not np.all(np.diff(df.valid_time.to_numpy())==np.timedelta64(1,'D')): raise ValueError('Calendrier journalier discontinu')
        else:
            if df.valid_time.dt.year.tolist()!=list(range(lo,hi+1)): raise ValueError('Années invalides')
        report[name]={'rows':len(df),'first':str(df.valid_time.min()),'last':str(df.valid_time.max()),'columns':cols,'missing':0,'duplicate_dates':0,'ranges':{c:[float(df[c].min()),float(df[c].max())] for c in df if c!='valid_time'},'units':{'temperature':'°C fournis par le kit','co2':'ppm fournis par le kit'},'sha256':sha256(ROOT/config['kit_dir']/'data'/(name+'.csv'))}
    report['data_limits']='Températures moyennes journalières distinctes des extrêmes annuels; provenance ERA5 et résolution non certifiées par ces CSV.'
    return report


def safe_extract(archive,dest):
    """Liste blanche stricte; ignore entrée '/' et toutes entrées non autorisées."""
    dest=Path(dest).resolve(); dest.mkdir(parents=True,exist_ok=True)
    found=[]
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if info.filename not in FULL_NAMES: continue
            target=(dest/info.filename).resolve()
            if target.parent!=dest: raise ValueError('Destination hors dossier')
            with z.open(info) as src, target.open('wb') as dst: shutil.copyfileobj(src,dst)
            found.append(info.filename)
    if set(found)!=FULL_NAMES: raise ValueError(f'Archive incomplète: {found}')
    return {n:sha256(dest/n) for n in sorted(found)}


def load_full(config):
    dest=ROOT/'data'/'full_project'
    if not (ROOT/'artifacts'/'competition'/'benchmark_results.json').exists(): raise RuntimeError('Phase complète interdite avant benchmark verrouillé')
    if not all((dest/n).exists() for n in FULL_NAMES):
        hashes=safe_extract(ROOT/config['full_archive'],dest)
        write_json(dest/'provenance.json',{'archive_sha256':sha256(ROOT/config['full_archive']),'files':hashes})
        event('full_project','archive_extracted',files=hashes)
    frames={n.removesuffix('.csv'):pd.read_csv(dest/n,parse_dates=['valid_time']) for n in FULL_NAMES}
    yearly=frames['yearly_temp_brest']; daily=frames['daily_temp_brest']
    if len(yearly)!=86 or yearly.valid_time.dt.year.tolist()!=list(range(1940,2026)): raise ValueError('Période annuelle complète invalide')
    if len(daily)!=31412 or daily.valid_time.dt.year.min()!=1940 or daily.valid_time.dt.year.max()!=2025: raise ValueError('Période journalière complète invalide')
    for df in frames.values():
        if df.isna().any().any() or df.valid_time.duplicated().any(): raise ValueError('Audit complet: manquants/doublons')
        if not np.isfinite(df.drop(columns='valid_time').to_numpy(float)).all(): raise ValueError('Audit complet: non fini')
    comp=load_competition(config)
    future=frames['yearly_future_co2']
    if list(future.columns)!=['valid_time',*SCENARIOS] or future.valid_time.dt.year.tolist()!=list(range(2026,2101)):
        raise ValueError('Scénarios complets: colonnes ou années invalides')
    if not (future[list(SCENARIOS)]>0).all().all(): raise ValueError('Scénarios complets: CO₂ non positif')
    pd.testing.assert_frame_equal(comp['yearly_future_co2'],future)
    late=yearly.loc[yearly.valid_time.dt.year>=2001,['valid_time','co2']].reset_index(drop=True)
    pd.testing.assert_frame_equal(comp['test_inputs'],late)
    for short,long in [('yearly_temp_brest_train','yearly_temp_brest'),('daily_temp_brest_train','daily_temp_brest')]:
        old=comp[short]; head=frames[long].iloc[:len(old)]
        pd.testing.assert_frame_equal(old.reset_index(drop=True),head.reset_index(drop=True))
    return frames
