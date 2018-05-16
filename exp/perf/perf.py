
import time

from exp.execute import *

def create_dyntrace_before(ee):
    args = [
        'dyntrace',
        'add',
        *(('-e',) if ee else ()),
        'powmod',
        'none'
    ]
    def dyntrace_before(exe):
        sudo_execute(['dyntraced', '--d'])
        execute(['dyntrace', 'attach', exe.name])
        time.sleep(0.1)
        execute(args)
    return dyntrace_before

def dyntrace_after():
    sudo_execute(['pkill', 'dyntraced'], ignore_err=True)

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

    runner.add_test('none', exe)
    runner.add_test('dyntrace', exe, before=create_dyntrace_before(False), after=dyntrace_after)
    runner.add_test('dyntrace-ee', exe, before=create_dyntrace_before(True), after=dyntrace_after)

    runner.add_pre(dyntrace_after)
    runner.add_post(dyntrace_after)