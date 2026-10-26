from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def json_default(x):
    if isinstance(x, Path): return str(x)
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, np.generic): return x.item()
    raise TypeError(type(x).__name__)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=json_default, allow_nan=False), encoding='utf-8')
    os.replace(temp, path)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=json_default).encode()).hexdigest()


def code_hash():
    return fingerprint({str(p.relative_to(ROOT)): sha256(p) for folder in ('src','scripts','configs') for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and p.suffix in ('.py','.yaml','.ps1')})


def load_config(path):
    import yaml
    path = Path(path)
    config = yaml.safe_load(path.read_text(encoding='utf-8'))
    if 'extends' in config:
        base = load_config(path.parent / config.pop('extends'))
        base.update(config); config = base
    return config


def environment():
    import importlib.metadata
    import torch
    names = ['torch','numpy','pandas','scipy','matplotlib','nbformat','nbclient','ipykernel','PyYAML','pytest']
    versions = {}
    for n in names:
        try: versions[n] = importlib.metadata.version(n)
        except importlib.metadata.PackageNotFoundError: versions[n] = 'absent'
    try: commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError): commit = None
    return {'python':sys.version,'executable':sys.executable,'platform':platform.platform(), 'packages':versions,'cuda':torch.version.cuda,'cuda_available':torch.cuda.is_available(),'gpu':torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,'dtype':'float32','amp':False,'commit':commit,'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}


def event(phase, action, **fields):
    path = ROOT/'artifacts'/'execution_journal.jsonl'
    path.parent.mkdir(parents=True, exist_ok=True)
    value = dict(timestamp_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),phase=phase,action=action,**fields)
    with path.open('a',encoding='utf-8') as f: f.write(json.dumps(value,ensure_ascii=False,default=json_default)+'\n')
