
import argparse
import os
import os.path as osp
import signal
import subprocess as sp
import tempfile
import time

import numpy.random as rnd

from dyntrace import *

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
NANO =    '/usr/local/bin/nano'
FIREFOX = '/home/charpercyr/mozilla-central/obj-x86_64-pc-linux-gnu/dist/bin/firefox'

def generate(size):
    while size:
        n = min((int(rnd.poisson(3.3)), size, 15))
        if n < 1: n = 1
        size -= n
        yield n

def gen_file(n):
    code = tempfile.NamedTemporaryFile('w+', suffix='.S')
    addr = ''
    gdb = 0
    code.write('.section .text\n')
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
    res = []
    for f in str(sp.run(f"readelf -Ws {exe} | grep FUNC | grep -v UND | grep GLOBAL", shell=True, stdout=sp.PIPE).stdout, 'utf-8').strip().split('\n'):
        f = list(filter(None, f.strip().split(' ')))
        start, size, name = int(f[1], 16), int(f[2]), f[-1]
        if not size:
            continue
        for a in str(sp.run(f"objdump -d {exe} --start-address={hex(start)} --stop-address={hex(start + size)} | grep -E '[a-fA-F0-9]+:' | awk '{{print $1}}' | sed 's/://g'", shell=True, stdout=sp.PIPE).stdout, 'utf-8').strip().split('\n'):
            try:
                res += [int(a, 16)]
            except ValueError:
                pass
    return res


def run_gdb(exe, funcs, args=[]):
    commands = ''
    for f in funcs:
        commands += f'ftrace *0x{f}\n'
        commands += 'd\ny\n'
    commands += 'q\n'
    res = execute(['gdb', '--args', exe, *args], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    out = str(res.communicate(bytes(commands, 'utf-8'))[0], 'utf-8')
    return out.count('Fast tracepoint')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('n', nargs='?', default=1000, type=int)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--verbose', action='store_true')
    args = parser.parse_args()

    set_verbose(args.verbose)

    firefox_funcs = get_funcs(FIREFOX)
    firefox_gdb = run_gdb(FIREFOX, firefox_funcs, args=['--headless'])
    #firefox = run_dyntrace(FIREFOX, firefox_funcs, name='firefox', args=['--headless'])

    # nano_funcs = get_funcs(NANO)
    # nano_gdb = run_gdb(NANO, nano_funcs)
    # # nano = run_dyntrace(NANO, nano_funcs)
    
    # rnd.seed(args.seed)
    # exe = gen_file(args.n)
    # small_funcs = get_funcs(exe)
    # small_gdb = run_gdb(exe, small_funcs)
    # small = run_dyntrace(exe, small_funcs)

    #print(f'small-dyntrace: {small}/{len(small_funcs)}')
    #print(f'small-gdb: {small_gdb}/{len(small_funcs)}')
    #print(f'nano-dyntrace: {nano}/{len(nano_funcs)}')
    #print(f'nano-gdb: {nano_gdb}/{len(nano_funcs)}')
    print(f'firefox-dyntrace: {firefox}/{len(firefox_funcs)}')
    print(f'firefox-gdb: {firefox_gdb}/{len(firefox_funcs)}')
    
