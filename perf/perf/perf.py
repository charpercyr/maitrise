
import math
import time
import os

from perf.execute import *
from perf.runner import Results

def devnull():
    return open(os.path.devnull, 'w+')

def create_dyntrace_before(ee):
    add_args = [
        'dyntrace',
        'add',
        *(('-e',) if ee else ()),
        '-r',
        'perf:^powmod$',
        'none'
    ]
    def dyntrace_before(args, exe):
        sudo_execute(['dyntraced', '--d'], silent=not args.verbose)
        execute(['dyntrace', 'attach', exe.path], silent=not args.verbose)
        execute(add_args, silent=not args.verbose, stdout=devnull())
        time.sleep(0.1)
    return dyntrace_before

def dyntrace_after(args, exe=None):
    sudo_execute(['pkill', 'dyntraced'], ignore_err=True, silent=not args.verbose)

UPROBE_TRACEPOINT_DIR = '/sys/kernel/debug/tracing'
UPROBE_TRACEPOINT_FILE=f'{UPROBE_TRACEPOINT_DIR}/uprobe_events'
UPROBE_TRACEPOINT_ENABLE=f'{UPROBE_TRACEPOINT_DIR}/events/uprobes/enable'

def powmod_offset(path):
    out = str(sp.run(['readelf', '-s', path], stdout=sp.PIPE).stdout, 'utf-8')
    base = str(sp.run(['readelf', '-l', path], stdout=sp.PIPE).stdout, 'utf-8')
    for line in base.split('\n'):
        line = list(filter(None, line.strip().split(' ')))
        if len(line) >= 4 and line[0] == 'LOAD':
            base = int(line[2], 16)
            break
    for line in out.split('\n'):
        line = list(filter(None, line.strip().split(' ')))
        if len(line) >= 8 and line[7] == 'powmod':
            return int(line[1], 16) - base
    raise ValueError('powmod not found in exe')

def create_uprobe_before(ee):
    tp = 'r' if ee else 'p'
    def uprobe_before(args, exe):
        sudo_execute(['echo', f'{tp}', f'{exe.path}:{powmod_offset(exe.path)}', '>', f'{UPROBE_TRACEPOINT_FILE}'], silent=not args.verbose)
        sudo_execute(['echo', '1', '>', f'{UPROBE_TRACEPOINT_ENABLE}'], silent=not args.verbose)
    return uprobe_before

def uprobe_after(args, exe=None):
        sudo_execute(['echo', '0', '>', f'{UPROBE_TRACEPOINT_ENABLE}'], ignore_err=True, silent=not args.verbose, stderr=devnull())
        sudo_execute(['echo', '>', f'{UPROBE_TRACEPOINT_FILE}'], ignore_err=True, silent=not args.verbose, stderr=devnull())

def analyze_data(results, output):
    res = {}
    headers = ['threads']
    keys = results.keys()
    for k in keys:
        headers += [str(k), 'stdev']
        for c in results[k]:
            t = c.comments['threads']
            i = c.comments['iters']
            if t not in res:
                res[t] = {}
            res[t][k] = {}
            cur = res[t][k]
            cur['mean'] = sum(float(r[1]) for r in c.results) / len(c.results)
            cur['stdev'] = math.sqrt(sum(float(r[1])*float(r[1]) for r in c.results) / len(c.results) - cur['mean'] * cur['mean'])
            cur['mean'] /= t*i
            cur['stdev'] /= t*i
    output.set_headers(headers)
    threads = sorted(res.keys())
    for t in threads:
        o = [t]
        for k in keys:
            o += [res[t][k]['mean'], res[t][k]['stdev']]
        output.add_result(o)

def calc_threads():
    ths=[]
    t = 1
    while t < os.cpu_count():
        ths += [t]
        t *= 2
    if ths[-1] != os.cpu_count():
        ths += [os.cpu_count()]
    return ths


def register(runner):
    exe = runner.add_executable(
        'perf',
        ['perf.cpp'],
        libs=['pthread'],
        flags=['-pie']
    )
    uftrace_exe = runner.add_executable(
        'perf-uftrace',
        ['perf.cpp'],
        libs=['pthread'],
        flags=['-pg', '-pie']
    )
    runner.add_arg('threads', int, calc_threads(), help='Number of threads')
    runner.add_arg('iters', int, 50000, help='Number of iterations')
    runner.add_arg('b', int, 5, help='Base')
    runner.add_arg('e', int, 123, help='Exponent')
    runner.add_arg('m', int, 1030, help='Modulo')
    runner.set_headers(['time (ns)'])

    none = runner.add_test('none', exe)
    dyntrace = runner.add_test('dyntrace', exe, before=create_dyntrace_before(False), after=dyntrace_after)
    dyntrace_ee = runner.add_test('dyntrace-ee', exe, before=create_dyntrace_before(True), after=dyntrace_after)
    uprobe = runner.add_test('uprobe', exe, before=create_uprobe_before(False), after=uprobe_after)
    uprobe_ee = runner.add_test('uprobe-ee', exe, before=create_uprobe_before(True), after=uprobe_after)
    uftrace = runner.add_test('uftrace', uftrace_exe, prefix=['uftrace', '--no-pager', '--nop'])

    runner.add_analysis('multithread', analyze_data, none, dyntrace, dyntrace_ee, uprobe, uprobe_ee, uftrace)

    runner.add_pre(dyntrace_after)
    runner.add_pre(uprobe_after)
    runner.add_post(dyntrace_after)
    runner.add_post(uprobe_after)