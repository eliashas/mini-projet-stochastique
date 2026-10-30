"""Prépare un ZIP contenant le notebook exécuté et les trois CSV du sujet."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def main():
    ici = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sortie', type=Path,
                        default=ici.parent / 'tmp' / 'livrable_sma' / 'rendu_final_groupe.zip')
    args = parser.parse_args()
    notebook = ici / 'rendu_final_groupe.ipynb'
    nb = json.loads(notebook.read_text(encoding='utf-8'))
    cellules = [c for c in nb['cells'] if c['cell_type'] == 'code']
    if any(c.get('execution_count') is None for c in cellules):
        raise ValueError('Exécuter le notebook avant de préparer le rendu')
    if any(o.get('output_type') == 'error' for c in cellules for o in c.get('outputs', [])):
        raise ValueError('Le notebook contient une sortie d’erreur')

    fichiers = [notebook] + [ici / nom for nom in nb['metadata']['donnees_locales']['fichiers']]
    for fichier in fichiers[1:]:
        attendu = nb['metadata']['donnees_locales']['sha256_lf'][fichier.name]
        if hashlib.sha256(fichier.read_bytes().replace(b'\r\n', b'\n')).hexdigest() != attendu:
            raise ValueError('CSV différent de celui du sujet : ' + fichier.name)
    sortie = args.sortie.resolve()
    sortie.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(sortie, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for fichier in fichiers:
            archive.write(fichier, arcname=fichier.name)
    with zipfile.ZipFile(sortie) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != {f.name for f in fichiers}:
            raise ValueError('Archive finale incorrecte')
        for fichier in fichiers:
            if archive.read(fichier.name) != fichier.read_bytes():
                raise ValueError('Fichier incorrect dans le rendu : ' + fichier.name)
    print('Rendu prêt :', sortie)
    print('Contenu :', ', '.join(f.name for f in fichiers))


if __name__ == '__main__':
    main()
