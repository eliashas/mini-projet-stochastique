"""CLI portable; toute sortie et tout accès vérité sont explicites par phase."""
from pathlib import Path
import argparse
import os
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
os.chdir(ROOT)

from sma.utils import load_config,write_json,read_json,event,environment


def run(command,config,args):
    from sma.data import prepare_kit,audit_data,load_competition
    from sma.experiments import validation,select,final_fit,predict_competition
    from sma.reporting import analyze_annual,generate_reports
    from sma.heatwaves import analyze_heatwaves
    out=ROOT/'artifacts'/'competition'
    selection_path=ROOT/(args.selection or 'artifacts/competition/selection.json')
    if command=='audit-data':
        prepare_kit(config,args.kit_dir)
        write_json(out/'data_audit.json',audit_data(config)); write_json(out/'environment.json',environment())
    elif command=='smoke':
        import importlib.util
        spec=importlib.util.spec_from_file_location('sma_neural_smoke',ROOT/'scripts'/'neural_smoke.py')
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        module.run_smoke({k:v for k,v in config.items() if k not in ('models','folds')})
    elif command=='validate': validation(config)
    elif command=='select': select(config)
    elif command=='fit-final': final_fit(config,read_json(selection_path))
    elif command=='predict': predict_competition(config,read_json(selection_path))
    elif command=='benchmark':
        from sma.benchmark_adapter import run_benchmarks
        run_benchmarks(config,ROOT/(args.manifest or 'artifacts/competition/evaluation_manifest.json'))
    elif command=='refit-full': final_fit(config,read_json(selection_path),full=True)
    elif command=='project-full':
        from sma.projections import project_full
        project_full(config)
    elif command=='report':
        phase=args.phase; phaseout=ROOT/'artifacts'/phase
        if phase=='competition':
            d=load_competition(config); yearly=d['yearly_temp_brest_train']; daily=d['daily_temp_brest_train']
        else:
            from sma.data import load_full
            d=load_full(config); yearly=d['yearly_temp_brest']; daily=d['daily_temp_brest']
        analyze_annual(yearly,phaseout/'annual_analysis',phase)
        analyze_heatwaves(daily,phaseout/'heatwaves',phase)
        generate_reports(ROOT,phase)
    elif command=='notebooks':
        import subprocess
        subprocess.run([sys.executable,str(ROOT/'scripts'/'build_notebooks.py'),'--execute'],check=True)
    elif command=='all':
        run('audit-data',config,args)
        if not (out/'benchmark_results.json').exists():
            if (out/'test_truth_opened.json').exists(): run('benchmark',config,args)
            else:
                for c in ('smoke','validate','select','fit-final','predict','benchmark'): run(c,config,args)
        run('report',config,argparse.Namespace(**{**vars(args),'phase':'competition'}))
        run('refit-full',config,args); run('project-full',config,args)
        run('report',config,argparse.Namespace(**{**vars(args),'phase':'full_project'}))
        run('notebooks',config,args)
    else: raise ValueError(command)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['audit-data','smoke','validate','select','fit-final','predict','benchmark','report','refit-full','project-full','notebooks','all'])
    parser.add_argument('--config',default='configs/experiments.yaml'); parser.add_argument('--kit-dir')
    parser.add_argument('--selection'); parser.add_argument('--manifest'); parser.add_argument('--phase',default='competition',choices=['competition','full_project'])
    args=parser.parse_args(); config=load_config(ROOT/args.config)
    if args.kit_dir: config['original_kit_dir']=args.kit_dir
    tick=time.perf_counter(); event(args.phase,'command_started',command=args.command)
    try: run(args.command,config,args)
    except BaseException as exc:
        event(args.phase,'command_failed',command=args.command,error=repr(exc),traceback=traceback.format_exc()); raise
    finally:
        elapsed=time.perf_counter()-tick
        print(f'{args.command}: {elapsed:.3f} s',flush=True)
        event(args.phase,'command_finished',command=args.command,wall_seconds=elapsed)


if __name__=='__main__': main()
