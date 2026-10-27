"""Exécuter le seul notebook copié dans un dossier vide, avec un noyau neuf.

Lancer avec le Python de l'environnement à vérifier. Le kernelspec éphémère
utilise exactement cet interpréteur ; aucun kernel utilisateur n'est modifié.
"""
from pathlib import Path
import argparse
import json
import os
import shutil
import sys
import tempfile
import time

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--notebook',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--proof',required=True)
    parser.add_argument('--mode',default='rapide',choices=['rapide','reentrainement'])
    args=parser.parse_args()
    work=Path(tempfile.mkdtemp(prefix='sma_clean_execution_'))
    copied=work/'rendu_final_equipe.ipynb'
    shutil.copy2(args.notebook,copied)
    kernels=Path(tempfile.mkdtemp(prefix='sma_clean_kernel_'))
    spec=kernels/'sma-clean';spec.mkdir()
    (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
        'display_name':'SMA environnement neuf','language':'python'}),encoding='utf-8')
    manager=KernelManager(kernel_name='sma-clean',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
    notebook=nbformat.read(copied,as_version=4)
    for cell in notebook.cells:
        if cell.cell_type=='code':cell.outputs=[];cell.execution_count=None
    env=dict(os.environ,SMA_MODE=args.mode,PYTHONIOENCODING='utf-8',MPLBACKEND='module://matplotlib_inline.backend_inline')
    env.pop('PYTHONPATH',None)
    env.pop('PYTHONHOME',None)
    started=time.perf_counter()
    def progress(cell,cell_index,**kwargs):
        if cell.cell_type=='code':print(f"CELLULE {cell_index+1}/{len(notebook.cells)} {cell.id}",flush=True)
    client=NotebookClient(notebook,km=manager,resources={'metadata':{'path':str(work)}},timeout=7200,
                          allow_errors=False,on_cell_start=progress)
    try:
        client.execute(env=env)
    except BaseException:
        nbformat.write(notebook,work/'echec_notebook.ipynb')
        print('Échec conservé dans',work,flush=True)
        raise
    nbformat.validate(notebook)
    codes=[c for c in notebook.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in codes)
    assert not any(o.output_type=='error' for c in codes for o in c.outputs)
    proof=json.loads((work/'verification_notebook.json').read_text(encoding='utf-8'))
    nbformat.write(notebook,args.output)
    proof.update(execution_seconds=time.perf_counter()-started,code_cells=len(codes),markdown_cells=len(notebook.cells)-len(codes),
                 executable=sys.executable,empty_initial_directory=True,cleared_initial_outputs=True,
                 executed_notebook_sha256=__import__('hashlib').sha256(Path(args.output).read_bytes()).hexdigest())
    Path(args.proof).parent.mkdir(parents=True,exist_ok=True)
    Path(args.proof).write_text(json.dumps(proof,indent=2,ensure_ascii=False),encoding='utf-8')
    print('EXÉCUTION TERMINÉE',json.dumps(proof,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
