
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

def get_base(exe):
    bases = str(sp.run(f"cat /proc/$(ps ax | grep {exe} | grep -v dyntrace-run | awk '{{print $1}}' | head -1)/maps | grep {exe} | grep r-xp | sed 's/-/ /g' | awk '{{print $1}}'", shell=True, stdout=sp.PIPE).stdout, 'utf-8').strip().split()
    return min(int(b, 16) for b in bases)

def run_dyntrace(exe, funcs, name=None, args=[]):
    if not name:
        name = exe
    success = 0
    execute(['sudo', 'dyntraced', '--d'])
    proc = execute(['dyntrace-run', '--', exe, *args], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
    time.sleep(0.5)
    base = get_base(exe)
    for f in funcs:
        if proc.poll() is not None:
            proc = execute(['dyntrace-run', '--', exe, *args], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
            time.sleep(0.5)
        try:
            if type(f) is int:
                ret = execute(['dyntrace', 'add' ,'-x', f'{name}:{hex(base + f)}', 'none'], stdout=sp.PIPE, stderr=sp.PIPE, timeout=5)
            else:
                ret = execute(['dyntrace', 'add', f'{name}:{f}', 'none'], stdout=sp.PIPE, stderr=sp.PIPE, timeout=5)
            if ret.returncode == 0:
                success += 1
                tp = str(ret.stdout, 'utf-8').strip()
                execute(['dyntrace', 'rm', f'{name}:{tp}'], timeout=5)
            else:
                if VERBOSE and ret.stdout: print(str(ret.stdout, 'utf-8').strip())
                if VERBOSE and ret.stderr: print(str(ret.stderr, 'utf-8').strip())
        except sp.TimeoutExpired:
            pass
        if proc.poll() is not None:
            proc = execute(['dyntrace-run', '--', exe, *args], True, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
            time.sleep(0.5)
            base = get_base(exe)
    proc.kill()
    #execute(['sudo', 'pkill', 'dyntraced'])
    return success
