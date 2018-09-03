
import subprocess as sp
import time

VERBOSE=False

def set_verbose(val):
    global VERBOSE
    VERBOSE = val

def execute(args, popen = False, **kwargs):
    if VERBOSE:
        print(' '.join(args))
    if popen:
        return sp.Popen(args, **kwargs)
    else:
        return sp.run(args, **kwargs)

def run_dyntrace(exe, funcs, args=[]):
    success = 0
    execute(['sudo', 'dyntraced', '--d'])
    proc = execute(['dyntrace-run', exe, *args], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    time.sleep(0.5)
    for f in funcs:
        if proc.poll() is not None:
            proc = execute(['dyntrace-run', exe], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        try:
            ret = execute(['dyntrace', 'add', f'{exe}:{f}', 'none'], stdout=sp.PIPE, stderr=sp.PIPE, timeout=5)
            if ret.returncode == 0:
                success += 1
                tp = str(ret.stdout, 'utf-8').strip()
                execute(['dyntrace', 'rm', f'{exe}:{tp}'], timeout=5)
            else:
                if VERBOSE and ret.stdout: print(str(ret.stdout, 'utf-8').strip())
                if VERBOSE and ret.stderr: print(str(ret.stderr, 'utf-8').strip())
        except sp.TimeoutExpired:
            if VERBOSE and ret.stdout: print(str(ret.stdout, 'utf-8').strip())
            if VERBOSE and ret.stderr: print(str(ret.stderr, 'utf-8').strip())
    proc.kill()
    #execute(['sudo', 'pkill', 'dyntraced'])
    return success
