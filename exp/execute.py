
import subprocess as sp

def execute(args, stdin=None, stdout=None, stderr=None, before=None, after=None, ignore_err=False):
    print('>', ' '.join(args))
    proc = sp.Popen(args, stdin=stdin, stdout=stdout, stderr=stderr)
    if before: before()
    out, err = proc.communicate()
    if after: after()
    if not ignore_err and proc.returncode != 0:
        raise RuntimeError('Process failed')
    return out, err

def sudo_execute(args, stdin=None, stdout=None, stderr=None, before=None, after=None, ignore_err=False):
    cargs = []
    for a in args:
        if a.contains(' '):
            a = f'"{a}"'
        cargs += [a]
    cargs = ' '.join(cargs)
    return execute(
        ['sudo', 'bash', '-c', cargs],
        stdin, stdout, stderr, before, after, ignore_err
    )
