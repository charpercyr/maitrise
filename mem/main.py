
import itertools
import os
import tempfile
import time
import subprocess as sp

FUNC_TEMPLATE="""
asm(
".type {name}, @function\\n"
"{name}:\\n"
"{nops}\\n"
"ret\\n"
".skip 16 - (. - {name})"
);
"""

MAIN_TEMPLATE="""
#include <stdio.h>
int main()
{{
    while(getchar() != EOF);
    return 0;
}}
"""

MAX_ITER = 1000

ops = [
    'nop',
    'xchg %ax, %ax',
    'nopl (%rax)',
    'nopl (%eax)',
    'nopl (%eax, %eax, 1)'
]

def calc_nops(n):
    res = []
    for i in range(1, n):
        a = calc_nops(n - i)
        for j in range(len(a)):
            a[j] = (i, *a[j])
        res += a
    res += [(n,)]
    return res

def generate_file(n, nops):
    res = ''
    nops = [ops[i - 1] for i in nops]
    for i in range(n):
        res += FUNC_TEMPLATE.format(name=f'func{i}', nops='\\n"\n"'.join(nops)) + '\n'
    return res + MAIN_TEMPLATE

def compile(output, sources, flags=(), libs=()):
    args = [
        'gcc',
        *sources,
        *flags,
        '-o',
        output,
        *('-l{l}' for l in libs)
    ]
    #print(' '.join(args))
    sp.run(args)

def do_run(file):
    proc = sp.Popen(['dyntrace-run', file], stdin=sp.PIPE)
    time.sleep(0.5)
    worked = True
    for i in range(MAX_ITER):
        args = ['dyntrace', 'add', f'{file}:func{i}', 'none']
        #print(*args)
        res = sp.run(args, stdout=sp.PIPE, stderr=sp.PIPE)
        if res.returncode != 0:
            worked = False
            break
    if not worked:
        print(f'Failed after {i+1} insert{"s" if i != 0 else ""}')
    else:
        print(f'Made it to {MAX_ITER} inserts')
    proc.communicate()


def main():

    cwd = tempfile.TemporaryDirectory(prefix='mem-')

    nops = calc_nops(5)
    for n in nops:
        print('-'.join(map(str, n)))
        name = '-'.join(str(i) for i in n)
        open(os.path.join(cwd.name, f'{name}.c'), 'w').write(generate_file(MAX_ITER, n))
        compile(
            os.path.join(cwd.name, name),
            [os.path.join(cwd.name, f'{name}.c')],
            flags=['-pie']
        )
        do_run(os.path.join(cwd.name, name))