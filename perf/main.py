
from argparse import ArgumentParser
import importlib
import os
import tempfile

from perf.runner import Runner


tests = [
    'perf'
]

PROJECT_SRC_DIR=os.path.abspath(os.path.dirname(__file__))
RESULTS_DIR=os.path.abspath('results')
ANALYSIS_DIR=os.path.abspath('analysis')

def main():
    parser = ArgumentParser()
    subs = parser.add_subparsers()

    parser.add_argument('-r', '--runs', type=int, default=100, help='Number of runs')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')

    runners = {}

    tmpdir = tempfile.TemporaryDirectory()

    for t in tests:
        p = subs.add_parser(t)
        p.set_defaults(test=t)
        runner = Runner(p, RESULTS_DIR, ANALYSIS_DIR, os.path.join(tmpdir.name, t), os.path.abspath(os.path.join(PROJECT_SRC_DIR, t)))
        mod = importlib.import_module(f'perf.{t}.{t}')
        register = getattr(mod, 'register')
        register(runner)
        runners[t] = runner

    args = parser.parse_args()

    if hasattr(args, 'test'):
        runners[args.test].run_all(args)
    else:
        for _, r in runners.items():
            r.run_all(args)