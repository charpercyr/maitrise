
import math
import time

from exp.execute import *
from exp.runner import Results

def create_dyntrace_before(ee):
    args = [
        'dyntrace',
        'add',
        *(('-e',) if ee else ()),
        'powmod',
        'none'
    ]
    def dyntrace_before(args, exe):
        sudo_execute(['dyntraced', '--d'], silent=not args.verbose)
        execute(['dyntrace', 'attach', exe.name], silent=not args.verbose)
        time.sleep(0.1)
    return dyntrace_before

def dyntrace_after(args, exe=None):
    sudo_execute(['pkill', 'dyntraced'], ignore_err=True, silent=not args.verbose)

def analyze_data(results, output):
    res = {}
    headers = ['threads']
    keys = sorted(results.keys())
    for k in keys:
        headers += [str(k), 'stdev']
        for c in results[k]:
            t = c.comments['threads']
            if t not in res:
                res[t] = {}
            res[t][k] = {}
            cur = res[t][k]
            cur['mean'] = sum(float(r[1]) for r in c.results) / len(c.results)
            cur['stdev'] = math.sqrt(sum(float(r[1])*float(r[1]) for r in c.results) / len(c.results) - cur['mean'] * cur['mean'])
            cur['mean'] /= t
            cur['stdev'] /= t
    output.set_headers(headers)
    threads = sorted(res.keys())
    for t in threads:
        o = [t]
        for k in keys:
            o += [res[t][k]['mean'], res[t][k]['stdev']]
        output.add_result(o)

def register(runner):
    exe = runner.add_executable(
        'perf',
        ['perf.cpp'],
        libs=['pthread']
    )
    exe.add_arg('threads', int, [1, 2, 4, 8], help='Number of threads')
    exe.add_arg('iters', int, 50000, help='Number of iterations')
    exe.add_arg('b', int, 5, help='Base')
    exe.add_arg('e', int, 123, help='Exponent')
    exe.add_arg('m', int, 1030, help='Modulo')
    exe.set_headers(['time (ns)'])

    none = runner.add_test('none', exe)
    dyntrace = runner.add_test('dyntrace', exe, before=create_dyntrace_before(False), after=dyntrace_after)
    dyntrace_ee = runner.add_test('dyntrace-ee', exe, before=create_dyntrace_before(True), after=dyntrace_after)

    runner.add_analysis('multithread', analyze_data, none, dyntrace, dyntrace_ee)

    runner.add_pre(dyntrace_after)
    runner.add_post(dyntrace_after)