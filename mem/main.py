
import argparse
import tempfile
import time
import os
import shutil
import subprocess as sp

DEFAULT_TPS = [1, 10, 100, 500, 1000, 2500, 5000, 7500, 10000, 25000, 50000, 75000, 100000]

FUNC_TEMPLATE=os.path.join(os.path.dirname(__file__), 'func.c.in')
MAIN_TEMPLATE=os.path.join(os.path.dirname(__file__), 'main.c.in')

def run_test(filename):
    print(filename)
    if sp.run(['gcc', f'{filename}.c', '-o', filename]).returncode != 0:
        raise RuntimeError(f'Could not compile {filename}.c')
    proc = sp.Popen([
        'dyntrace-run', '--', 'valgrind', '--tool=massif', '--pages-as-heap=yes', f'--massif-out-file={filename}.massif', filename],
        stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE
    )
    time.sleep(1)
    sp.run(['dyntrace', 'add', 'valgrind:func*', 'none'], stdout=sp.PIPE)
    proc.communicate()
    peak = -1
    for line in open(f'{filename}.massif'):
        if line.startswith('mem_heap_B='):
            used = int(line.replace('mem_heap_B=', ''))
            if used > peak:
                peak = used
    shutil.copy(f'{filename}.massif', 'results/')
    return peak

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

    os.makedirs('results', exist_ok=True)
    os.makedirs('analysis', exist_ok=True)

    tmpdir = tempfile.TemporaryDirectory(prefix='mem-')
    data = []
    for tps in args.tps:
        filename = os.path.join(tmpdir.name, f'mem-{tps}')
        open(f'{filename}.c', 'w').write(make_exe(tps))
        data += [(tps, run_test(filename))]
    out = open('analysis/mem.csv', 'w')
    out.write('n,memory(KB)\n')
    out.write('\n'.join(f'{d[0]},{d[1]//1024}'for d in data))