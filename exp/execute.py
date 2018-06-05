
import subprocess as sp

def execute(args, stdout=None, stderr=None, before=None, after=None, ignore_err=False, cwd=None, silent=False, prefix=None, suffix=None):
    proc = sp.Popen(args, stdin=sp.PIPE, stdout=stdout, stderr=stderr, cwd=cwd)
    if before: before()
    if prefix:
        args = prefix + args
    if suffix:
        args += suffix
    if not silent:
        print('>', ' '.join(a if ' ' not in a else f'"{a}"' for a in args))
    out, err = proc.communicate()
    if after: after()
    if not ignore_err and proc.returncode != 0:
        raise RuntimeError('Process failed')
    return out, err

def sudo_execute(args, **kwargs):
    cargs = []
    for a in args:
        if ' ' in a:
            a = f'"{a}"'
        cargs += [a]
    cargs = ' '.join(cargs)
    return execute(
        ['sudo', 'bash', '-c', cargs],
        **kwargs
    )
