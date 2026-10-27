"""Contrôles du paquet réellement livré, utilisables dans un clone neuf."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import nbformat
import numpy as np
import pandas as pd
from sma.final_models import predictive_sample, SCENARIOS
from sma.benchmark_adapter import check_predictions


def main():
    data=ROOT/'rendu_final/data';out=ROOT/'rendu_final/resultats'
    selection=json.loads((out/'selection.json').read_text())
    run=json.loads((out/'execution.json').read_text())
    nb=nbformat.read(ROOT/'notebooks/rendu_final_equipe.ipynb',as_version=4)
    nbformat.validate(nb)
    assert all(c.execution_count is not None for c in nb.cells if c.cell_type=='code')
    assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
    assert run['status']=='completed' and selection['test_used_for_selection'] is False
    assert run['test_previously_consulted'] is True
    manifest=json.loads((ROOT/'rendu_final/provenance_donnees.json').read_text())
    for row in manifest['files']:
        assert hashlib.sha256((data/row['file']).read_bytes()).hexdigest()==row['sha256']
    with zipfile.ZipFile(ROOT/'rendu_final/ressources_notebook.zip') as z:
        files=json.loads(z.read('MANIFEST_EMBARQUE.json'))
        for path,digest in files.items():
            assert hashlib.sha256(z.read(path)).hexdigest()==digest
            assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    assert hashlib.sha256((ROOT/'rendu_final/ressources_notebook.zip').read_bytes()).hexdigest()==nb.metadata.sma.bundle_sha256
    matrix=pd.read_csv(ROOT/'reports/matrice_conformite.csv');ids={c.id for c in nb.cells}
    assert all(set(row.split(','))<=ids for row in matrix.cellules)
    inputs=pd.read_csv(data/'test_inputs.csv')
    future=pd.read_csv(data/'yearly_future_co2.csv',parse_dates=['valid_time'])
    c2100=future.loc[future.valid_time.dt.year==2100,list(SCENARIOS)].to_numpy().ravel()
    arrays={};projection_controls=[]
    for v in ['max','min']:
        suite=json.loads((ROOT/f'rendu_final/modeles/historique/{v}/suite.json').read_text())
        arrays['test_'+v]=predictive_sample(suite,selection['selected'][v],inputs.co2,root=ROOT,seed=8200+1000*(v=='min'))
        arrays['proj_'+v]=predictive_sample(suite,selection['selected'][v],c2100,root=ROOT,seed=8200+1000*(v=='min'))
        component=selection['h0_components'][v]
        assert np.array_equal(predictive_sample(suite,f'H0_{component}_1',c2100,root=ROOT),predictive_sample(suite,'Bayes',c2100,root=ROOT))
        assert np.array_equal(predictive_sample(suite,f'H0_{component}_0',c2100,root=ROOT),predictive_sample(suite,component,c2100,root=ROOT))
        full=json.loads((ROOT/f'rendu_final/modeles/complet/{v}/suite.json').read_text())
        expected=pd.read_csv(out/'projections.csv')
        for j,sc in enumerate(SCENARIOS):
            draws=predictive_sample(full,selection['selected'][v],future[sc],root=ROOT,seed=42000+j+100*(v=='min'),independent_years=True)
            assert draws.shape==(75,10000) and np.isfinite(draws).all()
            q=np.quantile(draws,[.05,.5,.95],axis=1)
            recorded=expected[(expected.variable==v)&(expected.scenario==sc)]
            np.testing.assert_allclose(q.T,recorded[['q05_C','q50_C','q95_C']],atol=2e-5,rtol=0)
            lo,hi=(0,50) if v=='max' else (-30,20)
            projection_controls.append(dict(variable=v,scenario=sc,minimum_C=draws.min(),maximum_C=draws.max(),
                outside_kit_bounds=int(((draws<lo)|(draws>hi)).sum())))
    assert check_predictions(arrays)['admissible']
    from sma.scores import crps_rows
    truth=pd.read_csv(data/'verite_2001_2025.csv')
    for v in ['max','min']:
        assert abs(crps_rows(arrays['test_'+v],truth[v]).mean()-run['score_'+v])<2e-5
    pd.DataFrame(projection_controls).to_csv(ROOT/'reports/final/controle_projections_recalculees.csv',index=False)
    proof=dict(status='passed',resources=len(files),requirements=len(matrix),code_cells=sum(c.cell_type=='code' for c in nb.cells),
               historical_prechecks=True,mixture_endpoints_exact=True,projections_recomputed=True,
               notebook_sha256=hashlib.sha256((ROOT/'notebooks/rendu_final_equipe.ipynb').read_bytes()).hexdigest())
    (ROOT/'reports/final/verification_paquet.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(proof,ensure_ascii=False))


if __name__=='__main__':main()
