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
import os
from pathlib import Path
import sys
import time

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import nbformat
from nbclient import NotebookClient

GARDE_RESEAU = r'''
import ipaddress
import json
import os
from pathlib import Path
import socket

preuve = Path(os.environ['SMA_PREUVE_RESEAU'])
journal = Path(os.environ['SMA_JOURNAL_RESEAU'])

def local(hote):
    if hote in (None, '', 'localhost', b'localhost'):
        return True
    try:
        ip = ipaddress.ip_address(hote.decode() if isinstance(hote, bytes) else str(hote))
        return ip.is_loopback or ip.is_unspecified
    except ValueError:
        return False

def verifier(hote):
    if not local(hote):
        with journal.open('a', encoding='utf-8') as f:
            f.write(json.dumps({'hote': str(hote)}) + '\n')
        raise RuntimeError('Accès réseau externe bloqué pendant la vérification du notebook')

getaddrinfo_original = socket.getaddrinfo
connect_original = socket.socket.connect
connect_ex_original = socket.socket.connect_ex

def getaddrinfo(hote, *args, **kwargs):
    verifier(hote)
    return getaddrinfo_original(hote, *args, **kwargs)

def connect(self, adresse):
    if isinstance(adresse, tuple):
        verifier(adresse[0])
    return connect_original(self, adresse)

def connect_ex(self, adresse):
    if isinstance(adresse, tuple):
        verifier(adresse[0])
    return connect_ex_original(self, adresse)

socket.getaddrinfo = getaddrinfo
socket.socket.connect = connect
socket.socket.connect_ex = connect_ex
preuve.write_text(json.dumps({'protection_active': True}), encoding='utf-8')
'''


def main():
    ici = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dossier', type=Path, default=ici)
    parser.add_argument('--sans-reseau', action='store_true',
                        help='Bloque les connexions externes du noyau pendant la vérification.')
    args = parser.parse_args()
    dossier = args.dossier.resolve()
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = ici / 'rendu_final_groupe.ipynb'
    rapports = ici.parent / 'reports' / 'final_concis'
    rapports.mkdir(parents=True, exist_ok=True)
    nb = nbformat.read(chemin, as_version=4)
    nbformat.validate(nb)
    debut = time.perf_counter()
    options_noyau = {}
    if args.sans_reseau:
        garde = dossier / '.verification_reseau'
        garde.mkdir(exist_ok=True)
        (garde / 'sitecustomize.py').write_text(GARDE_RESEAU, encoding='utf-8')
        preuve_reseau, journal_reseau = garde / 'active.json', garde / 'tentatives.jsonl'
        if preuve_reseau.exists():
            preuve_reseau.unlink()
        journal_reseau.write_text('', encoding='utf-8')
        env = os.environ.copy()
        env['PYTHONPATH'] = str(garde) + os.pathsep + env.get('PYTHONPATH', '')
        env['SMA_PREUVE_RESEAU'] = str(preuve_reseau)
        env['SMA_JOURNAL_RESEAU'] = str(journal_reseau)
        options_noyau['env'] = env

    def progression(cell, cell_index, **_):
        if cell.cell_type == 'code':
            print(f'Cellule {cell_index + 1}/{len(nb.cells)} exécutée '
                  f'({time.perf_counter() - debut:.1f} s)', flush=True)

    client = NotebookClient(nb, timeout=1800, kernel_name='python3',
                            resources={'metadata': {'path': str(dossier)}},
                            on_cell_executed=progression)
    try:
        client.execute(**options_noyau)
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
               'code_cellules_sha256': hashlib.sha256('\n\n'.join(
                   c.source.replace('\r\n', '\n') for c in nb.cells if c.cell_type == 'code'
               ).encode('utf-8')).hexdigest(),
               'sorties_texte': textes}
    if args.sans_reseau:
        if not preuve_reseau.exists():
            raise RuntimeError('La protection réseau du noyau ne s’est pas chargée')
        tentatives = len(journal_reseau.read_text(encoding='utf-8').splitlines())
        rapport['verification_hors_ligne'] = {'protection_active': True,
                                              'tentatives_exterieures': tentatives}
        if tentatives:
            raise RuntimeError('Des appels réseau externes ont été tentés pendant l’exécution')
    (rapports / 'execution.json').write_text(json.dumps(rapport, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'Terminé en {rapport["secondes"]:.1f} s ; {len(erreurs)} erreur(s).', flush=True)
    if erreurs:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
