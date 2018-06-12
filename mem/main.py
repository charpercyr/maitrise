
import argparse
import tempfile
import time
import os
import shutil
import subprocess as sp

DEFAULT_TPS = [0, 1, 5, 10, 50, 100, 500, 1000]

FUNC_TEMPLATE=os.path.join(os.path.dirname(__file__), 'func.c.in')
MAIN_TEMPLATE=os.path.join(os.path.dirname(__file__), 'main.c.in')

def run_test(filename):
    print(filename)
    if sp.run(['gcc', f'{filename}.c', '-o', filename]).returncode != 0:
        raise RuntimeError(f'Could not compile {filename}.c')
    proc = sp.Popen([
        'dyntrace-run', '--', 'valgrind', '--tool=massif', '--pages-as-heap=yes', f'--massif-out-file={filename}.massif', filename],
        stdin=sp.PIPE, #stdout=sp.PIPE, stderr=sp.PIPE
    )
    time.sleep(1)
    sp.run(['dyntrace', 'add', 'valgrind:func*', 'none'])
    proc.communicate()
    os.makedirs('results', exist_ok=True)
    shutil.copy(f'{filename}.massif', 'results')

def make_exe(tps):
    func_content = open(FUNC_TEMPLATE).read()
    main_content = open(MAIN_TEMPLATE).read()
    return \
        '\n'.join(
            func_content.format(name=f'func{i}') for i in range(tps)
        ) + \
        '\n' + \
        main_content.format(calls='\n    '.join(f'func{i}();' for i in range(tps)))

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--tps', help='Number of tracepoints', nargs='+', type=int, default=DEFAULT_TPS)

    args = parser.parse_args()

    tmpdir = tempfile.TemporaryDirectory(prefix='mem-')

    for tps in args.tps:
        filename = os.path.join(tmpdir.name, f'mem-{tps}')
        open(f'{filename}.c', 'w').write(make_exe(tps))
        run_test(filename)
    #print('\n'.join(os.listdir(tmpdir.name)))