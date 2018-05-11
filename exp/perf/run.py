#!/usr/bin/python3

import argparse
import os
import time
import subprocess as sp

PERF_PATH='./build/perf'
PERF_ABS_PATH = os.path.abspath(PERF_PATH)
UPROBE_BASE='/sys/kernel/debug/tracing'
UPROBE_FILE=f'{UPROBE_BASE}/uprobe_events'
UPROBE_ENABLE=f'{UPROBE_BASE}/events/uprobes/enable'

def powmod_off():
    out = str(sp.run(['readelf', '-s', PERF_PATH], stdout=sp.PIPE).stdout, 'utf-8')
    for line in out.split('\n'):
        if 'powmod' in line:
            return int(line.strip().split(' ')[1], 16)
    raise ValueError('Not offset')

def exec_command(args, before=None, after=None, check_return=True):
    print('>', ' '.join(args))
    proc = sp.Popen(args, stdin=sp.PIPE)
    if before: before()
    proc.communicate()
    if after: after()
    if check_return and proc.returncode != 0:
        raise RuntimeError(f'Process returned {proc.returncode}')

def run_perf(name, runs=None, iter=None, before=None, after=None, prepend=None, append=None):
    args = ['./build/perf', f'./results/{name}.csv']
    if runs:
        args += [str(runs)]
    if iter:
        args += [str(iter)]
    if prepend: args = prepend + args
    if append: args = args + append
    print(f'===== {name.upper()} =====')
    exec_command(args, before, after)

def start_dyntrace():
    exec_command(['sudo', 'dyntraced', '--d'])

def stop_dyntrace():
    exec_command(['sudo', 'pkill', 'dyntraced'], check_return=False)

def start_uprobe(tp, off):
    exec_command(['sudo', 'bash', '-c', f'echo {tp} {PERF_ABS_PATH}:{hex(off)} > {UPROBE_FILE}'])
    exec_command(['sudo', 'bash', '-c', f'echo 1 > {UPROBE_ENABLE}'])

def stop_uprobe():
    exec_command(['sudo', 'bash', '-c', f'echo 0 > {UPROBE_ENABLE}'])
    exec_command(['sudo', 'bash', '-c', f'echo > {UPROBE_FILE}'])

def trace_powmod(entry_exit):
    time.sleep(0.1)
    args = ['dyntrace', 'add', f'perf:powmod']
    if entry_exit:
        args += ['-e']
    args += ['none']
    exec_command(args)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runs', type=int, nargs='?')
    parser.add_argument('iter', type=int, nargs='?')
    args = parser.parse_args()

    os.makedirs('./results', exist_ok=True)
    run_perf('none', args.runs, args.iter)

    stop_dyntrace()
    start_dyntrace()
    run_perf(
        'dyntrace', args.runs, args.iter, before=lambda: trace_powmod(False),
        prepend=['dyntrace-run']
    )
    run_perf(
        'dyntrace-ee', args.runs, args.iter, before=lambda: trace_powmod(True),
        prepend=['dyntrace-run']
    )
    stop_dyntrace()
    off = powmod_off()
    run_perf(
        'uprobe', args.runs, args.iter,
        before=lambda: start_uprobe('p', off),
        after=stop_uprobe
    )
    run_perf(
        'uprobe-ee', args.runs, args.iter,
        before=lambda: start_uprobe('r', off),
        after=stop_uprobe
    )


if __name__ == '__main__':
    main()