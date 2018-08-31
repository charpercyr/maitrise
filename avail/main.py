
import argparse
import os
import os.path as osp
import signal
import subprocess as sp
import tempfile
import time

import numpy.random as rnd

NOPS = [
    '0x90',
    '0x66, 0x90',
    '0x0f, 0x1f, 0x00',
    '0x0f, 0x1f, 0x40, 0x00',
    '0x0f, 0x1f, 0x44, 0x00, 0x00',
    '0x66, 0x0f, 0x1f, 0x44, 0x00, 0x00',
    '0x0f, 0x1f, 0x80, 0x00, 0x00, 0x00, 0x00',
    '0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x66, 0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x66, 0x66, 0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x66, 0x66, 0x66, 0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
    '0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x66, 0x0f, 0x1f, 0x84, 0x00, 0x00, 0x00, 0x00, 0x00',
]

MAIN_CPP = osp.join(osp.dirname(__file__), 'main.cpp')
NANO = '/usr/local/bin/nano'

VERBOSE=False

def generate(size):
    while size:
        n = min((int(rnd.poisson(3.3)), size, 15))
        if n < 1: n = 1
        size -= n
        yield n

def execute(args, popen = False, **kwargs):
    if VERBOSE:
        print(' '.join(args))
    if popen:
        return sp.Popen(args, **kwargs)
    else:
        return sp.run(args, **kwargs)

def gen_file(n):
    code = tempfile.NamedTemporaryFile('w+', suffix='.S')
    addr = ''
    gdb = 0
    for i, v in enumerate(generate(n)):
        code.write(
            f'.global .{i}\n'
            f'.type .{i}, @function\n'
            f'.{i}: .byte {NOPS[v - 1]}\n'
            f'.size .{i}, . - .{i}\n'
        )
        if i < n:
            addr += f'.{i}, '
        if v >= 5:
            gdb += 1
    code.write(
        '.section .rodata\n'
        '.global addresses\n'
        '.type addresses, @object\n'
        f'addresses: .quad {addr}0x00\n'
    )
    code.flush()
    exe = tempfile.NamedTemporaryFile('wb', delete=False)
    execute(['g++', '-std=c++17', '-o', exe.name, code.name, MAIN_CPP, '-ldyntrace-fasttp'])
    exe.close()
    return exe.name

def get_funcs(exe):
    return sorted(str(sp.run(f"readelf -Ws {exe} | grep FUNC | grep -v UND | grep GLOBAL | awk '{{print $8}}'", shell=True, stdout=sp.PIPE).stdout, 'utf-8').strip().split('\n'))

def run_dyntrace(exe, funcs):
    success = 0
    execute(['sudo', 'dyntraced', '--d'])
    proc = execute(['dyntrace-run', exe], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    time.sleep(0.5)
    for f in funcs:
        if proc.poll() is not None:
            proc = execute(['dyntrace-run', exe], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        ret = execute(['dyntrace', 'add', f'{exe}:{f}', 'none'], stdout=sp.PIPE, stderr=sp.PIPE)
        if ret.returncode == 0:
            success += 1
            tp = str(ret.stdout, 'utf-8').strip()
            execute(['dyntrace', 'rm', f'{exe}:{tp}'])
        else:
            if VERBOSE and ret.stdout: print(str(ret.stdout, 'utf-8').strip())
            if VERBOSE and ret.stderr: print(str(ret.stderr, 'utf-8').strip())
    proc.kill()
    execute(['sudo', 'pkill', 'dyntraced'])
    return success

def run_gdb(exe, funcs):
    commands = ''
    for f in funcs:
        commands += f'ftrace {f}\n'
    commands += 'q\n'
    res = execute(['gdb', exe], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    out = str(res.communicate(bytes(commands, 'utf-8'))[0], 'utf-8')
    return out.count('Fast tracepoint')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('n', nargs='?', default=1000, type=int)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()
    
    global VERBOSE
    VERBOSE = args.verbose
    
    rnd.seed(args.seed)
    exe = gen_file(args.n)
    small_funcs = get_funcs(exe)
    small_gdb = run_gdb(exe, small_funcs)
    small = run_dyntrace(exe, small_funcs)

    nano_funcs = get_funcs(NANO)
    nano_gdb = run_gdb(NANO, nano_funcs)
    nano = run_dyntrace(NANO, nano_funcs)
    
    print(f'small-dyntrace: {small}/{len(small_funcs)}')
    print(f'small-gdb: {small_gdb}/{len(small_funcs)}')
    print(f'nano-dyntrace: {nano}/{len(nano_funcs)}')
    print(f'nano-gdb: {nano_gdb}/{len(nano_funcs)}')