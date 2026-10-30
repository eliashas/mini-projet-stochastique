"""Exécute le rendu et garde les sorties, les figures et un compte rendu court.

    python rendu_final_concis/executer.py
    python rendu_final_concis/executer.py --dossier tmp/verification_concis_vide
"""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbclient import NotebookClient


def main():
    ici = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dossier', type=Path, default=ici)
    args = parser.parse_args()
    dossier = args.dossier.resolve()
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = ici / 'rendu_final_groupe.ipynb'
    rapports = ici.parent / 'reports' / 'final_concis'
    rapports.mkdir(parents=True, exist_ok=True)
    nb = nbformat.read(chemin, as_version=4)
    nbformat.validate(nb)
    debut = time.perf_counter()

    def progression(cell, cell_index, **_):
        if cell.cell_type == 'code':
            print(f'Cellule {cell_index + 1}/{len(nb.cells)} exécutée '
                  f'({time.perf_counter() - debut:.1f} s)', flush=True)

    client = NotebookClient(nb, timeout=1800, kernel_name='python3',
                            resources={'metadata': {'path': str(dossier)}},
                            on_cell_executed=progression)
    try:
        client.execute()
    finally:
        nbformat.write(nb, chemin)

    erreurs, textes, figures = [], [], []
    for i, cellule in enumerate(nb.cells):
        for j, sortie in enumerate(cellule.get('outputs', [])):
            if sortie.output_type == 'error':
                erreurs.append({'cellule': i, 'erreur': sortie.evalue})
            if sortie.output_type == 'stream':
                textes.append(sortie.text)
            if 'image/png' in sortie.get('data', {}):
                image = rapports / f'figure_{i:02d}_{j:02d}.png'
                image.write_bytes(base64.b64decode(sortie.data['image/png']))
                figures.append(image.name)
    rapport = {'date_utc': datetime.now(timezone.utc).isoformat(),
               'secondes': time.perf_counter() - debut,
               'notebook': str(chemin.relative_to(ici.parent)),
               'sha256': hashlib.sha256(chemin.read_bytes()).hexdigest(),
               'dossier_execution': str(dossier),
               'cellules_code': sum(c.cell_type == 'code' for c in nb.cells),
               'cellules_executees': sum(c.get('execution_count') is not None for c in nb.cells),
               'erreurs': erreurs, 'figures': figures,
               'sorties_texte': textes}
    (rapports / 'execution.json').write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Terminé en {rapport["secondes"]:.1f} s ; {len(erreurs)} erreur(s).', flush=True)
    if erreurs:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
