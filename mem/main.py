
import argparse
import os
import subprocess as sp
import tempfile

from dyntrace import run_dyntrace, execute, set_verbose

NOPS = [
    'nop',
    'xchg %ax, %ax',
    'nopl (%rax)',
    'nopl 0(%rax)',
    'nopl 0(%rax, %rax, 1)'
]

def gen_sizes(n):
    for i in range(1, n):
        for r in gen_sizes(n - i):
            yield (i, *r)
    yield (n,)

def gen_nops(n):
    for i in gen_sizes(n):
        yield tuple(NOPS[n - 1]for n in i)

def gen_code(n, nops):
    res = ''
    for i in range(n):
        res += f'.global .{i}\n'
        res += f'.type .{i}, @function\n'
        res += f'.{i}:\n'
        res += '  '
        res += '\n  '.join(nops)
        res += '\n  ret\n'
        res += f'.size .{i}, . - .{i}\n'
    res += '.global main\n'
    res += '.type main, @function\n'
    res += 'main:\n'
    res += '  pause\n'
    res += '  jmp main\n'
    res += '.size main, . - main\n'
    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', default=1000, type=int)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    set_verbose(args.verbose)

    success = {}

    for nops in gen_nops(5):
        code = tempfile.NamedTemporaryFile('w+', suffix='.S', prefix='mem-')
        exe = tempfile.NamedTemporaryFile('wb', prefix='mem-', delete=False)
        exe.close()
        code.write(gen_code(args.n, nops))
        code.flush()
        execute(['gcc', '-o', exe.name, code.name])
        success[nops] = run_dyntrace(exe.name, [f'.{i}' for i in range(args.n)])
        os.remove(exe.name)

    for n, s in success.items():
        print(n, s)