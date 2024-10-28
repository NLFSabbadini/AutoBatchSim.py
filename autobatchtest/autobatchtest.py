import time
import json
import sys
import os
import subprocess
import sys
from os import path
import argparse


def parse(command, defaults, deltas):
    parser = argparse.ArgumentParser(description='Automated batch deplyment, tracking and result management of tests.')
    parser.add_argument('testdir', help='existing test directory')
    parser.add_argument('-s', action='store_true' ,help='run for single delta')
    parser.add_argument('-d', nargs=2, default=[], action='append', help='run with additional delta: par val')

    args = parser.parse_args(command)
    if not path.exists(args.testdir):
        raise Exception(f'Test directory {args.testdir:!r} not found')
    sys.path.append(args.testdir)
    if path.exists(f'{args.testdir}/defaults.py'):
        from defaults import defaults
    if path.exists(f'{args.testdir}/deltas.py'):
        from deltas import deltas

    gamma = {key:val for key, val in args.d}
    deltas = [gamma] if args.s else [{**delta, **gamma} for delta in deltas]

    for delta in deltas:
        for key, val in delta.items():
            if key not in defaults:
                raise Exception(f'Invalid key found in delta {delta}')
            delta[key] = type(defaults[key])(val)

    argsl = [{**defaults, **delta} for delta in deltas]
    subdirl = [f'{args.testdir}/{testname}' for testname in map(lambda args: hash(f'{args}{time.time_ns()}'), argsl)]
    return args.testdir, subdirl, argsl


def run(command=sys.argv[1:], defaults={}, deltas=[{}], deploy='sh', preamble='', python=sys.executable):
    testdir, subdirl, argsl = parse(command, defaults, deltas)
    for subdir, args in zip(subdirl, argsl):
        request = "\n".join((
            f'{deploy} << SH',
            f'{preamble}',
            f'{python} << PY',
            'import sys',
            f'sys.path.append({testdir!r})',
            'from job import job',
            f'job({subdir!r}, {args})',
            'PY',
            'SH'
        ))
        os.makedirs(subdir, exist_ok=True)
        with open(path.join(subdir,'args.json'),'w') as file:
            json.dump(args, file, indent=4)
        subprocess.run(request, shell=True)
