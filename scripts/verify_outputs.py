"""Vérifie les critères de fin et les empreintes, sans réajustement ni accès vérité."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
import nbformat

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from sma.utils import read_json,sha256,write_json
from sma.benchmark_adapter import check_predictions,KEYS


def verify():
    comp=ROOT/'artifacts'/'competition'; full=ROOT/'artifacts'/'full_project'
    required=[ROOT/p for p in ['README.md','requirements.txt','configs/base.yaml','configs/experiments.yaml','reports/rapport_competition.md','reports/rapport_projections.md','reports/synthese_equipe.md','reports/audit_sources.md','notebooks/experiences_execute.ipynb','notebooks/rendu_projet.ipynb']]
    required += [comp/p for p in ['data_audit.json','environment.json','validation_individual.csv','validation_mixture.csv','validation_summary.csv','validation_per_year.csv','validation_runs.json','selection_validation.json','selection.json','fit_final.json','prechecks.json','evaluation_manifest.json','benchmark_results.json','benchmark_scores.csv','test_per_year.csv','test_diagnostics.csv','locked_source.zip','prediction_timing.json','test_truth_opened.json']]
    required += [full/p for p in ['fit_full.json','projections.npz','projection_summary.csv','probability_40.csv','trajectory_probability_40.csv','projection_manifest.json','co2_transition.json','heatwaves/heatwave_events_min3.csv','heatwaves/heatwave_events_min2.csv','heatwaves/heatwave_climatology.csv','heatwaves/heatwave_summary.json','annual_analysis/correlations.csv']]
    absent=[str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if absent: raise AssertionError(f'Livrables absents: {absent}')
    manifest=read_json(comp/'evaluation_manifest.json')
    assert sha256(comp/'selection.json')==manifest['selection_sha256']
    assert sha256(comp/'selection_validation.json')==manifest['selection_validation_sha256']
    assert sha256(comp/'locked_source.zip')==manifest['locked_source_sha256']
    assert manifest['test_years']==list(range(2001,2026))
    assert manifest['scenarios']==['ssp1-2.6','ssp2-4.5','ssp5-8.5']
    for cp,h in manifest['checkpoint_hashes'].items(): assert sha256(ROOT/cp)==h
    benchmark=read_json(comp/'benchmark_results.json'); result={r['id']:r for r in benchmark['results']}
    for row in manifest['predictions']:
        assert sha256(ROOT/row['path'])==row['sha256']
        with np.load(ROOT/row['path']) as f:
            assert set(f.files)==set(KEYS)
            arrays={k:f[k] for k in KEYS}
        checks=check_predictions(arrays)
        assert checks['admissible']==result[row['id']]['admissible']
    runs=read_json(comp/'validation_runs.json')
    assert len(runs)==108 or len(read_json(comp/'failures.json'))>0
    assert len(pd.read_csv(comp/'validation_mixture.csv'))==78 or len(read_json(comp/'failures.json'))>0
    assert len(pd.read_csv(comp/'validation_per_year.csv'))==780 or len(read_json(comp/'failures.json'))>0
    fit=read_json(comp/'fit_final.json')
    reuse={}
    for var in ('max','min'):
        for child,parent in [('D3_ddm_anchor','D1_ddm_crps'),('D4_ddm_tail_anchor','D2_ddm_tail')]:
            if child in fit['models'][var] and parent in fit['models'][var]:
                ok=fit['models'][var][child]['checkpoints']==fit['models'][var][parent]['checkpoints']
                assert ok; reuse[f'{var}_{child}']=ok
    with np.load(full/'projections.npz') as f:
        assert f['years'].tolist()==list(range(2026,2101))
        for var in ('max','min'): assert f[var].shape==(3,75,10000) and np.isfinite(f[var]).all()
    assert sha256(full/'projections.npz')==read_json(full/'projection_manifest.json')['ensembles_sha256']
    projection_table=pd.read_csv(full/'projection_summary.csv')
    assert len(projection_table)==450
    assert np.isfinite(projection_table[['event_threshold_C','event_probability']]).all().all()
    assert projection_table.event_probability.between(0,1).all()
    for filename in ('probability_40.csv','trajectory_probability_40.csv'):
        probabilities=pd.read_csv(full/filename)
        assert len(probabilities)==3
        assert np.allclose(probabilities.probability,probabilities.k/probabilities.n)
        assert ((probabilities.ci_lower<=probabilities.probability)&(probabilities.probability<=probabilities.ci_upper)).all()
    notebooks=[]
    for path in (ROOT/'notebooks').glob('*.ipynb'):
        nb=nbformat.read(path,as_version=4); code=[c for c in nb.cells if c.cell_type=='code']
        assert all(c.execution_count is not None for c in code),f'Cellules non exécutées: {path}'
        assert not any(o.output_type=='error' for c in code for o in c.outputs),f'Erreur notebook: {path}'
        notebooks.append({'path':str(path.relative_to(ROOT)),'code_cells':len(code),'executed':True,'error_outputs':0})
    pngs=list((ROOT/'reports'/'figures').rglob('*.png'))+list((ROOT/'artifacts').glob('*/heatwaves/*.png'))+list((ROOT/'artifacts').glob('*/annual_analysis/*.png'))
    for path in pngs: assert path.with_suffix('.svg').exists()
    report={'status':'complete','required_files':len(required),'validation_network_runs':len(runs),'benchmark_exports':len(manifest['predictions']),'admissible_exports':sum(r['admissible'] for r in result.values()),'eliminated_exports':sum(not r['admissible'] for r in result.values()),'candidate':manifest['candidate'],'candidate_models':manifest['selected_models'],'bootstrap_checkpoint_reuse':reuse,'notebooks':notebooks,'figure_png_svg_pairs':len(pngs),'test_results':read_json(ROOT/'artifacts'/'test_results.json'),'validation_failures':read_json(comp/'failures.json'),'final_fit_failures':fit['failures'],'full_fit_failures':read_json(full/'fit_full.json')['failures'],'notes':'Statuts des échecs conservés; les contrôles kit portent sur compétition; aucune vérité ouverte par cette vérification.'}
    write_json(ROOT/'artifacts'/'completion_audit.json',report)
    return report


if __name__=='__main__': print(json.dumps(verify(),ensure_ascii=False,indent=2))
