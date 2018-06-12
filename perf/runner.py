
from perf.execute import execute

import itertools
import os
import subprocess as sp

class Results:
    def __init__(self, path):
        self.path = path
        self.comments = {}
        self.headers = []
        self.results = []

    def add_comment(self, key, value):
        self.comments[key] = value

    def add_result(self, res):
        self.results += [tuple(res)]

    def set_headers(self, hdrs):
        self.headers = hdrs

    def commit(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as file:
            if self.comments:
                for k, v in self.comments.items():
                    file.write(f'{k},{v}\n')
                file.write('\n')
            file.write(','.join(self.headers) + '\n')
            for r in self.results:
                file.write(','.join(str(i) for i in r) + '\n')

class Args:
    def __init__(self, parser):
        self.parser = parser
        self.args = []

    def add_arg(self, name, t, default, help=None):
        allow_multiple=True
        if not isinstance(default, list) and not isinstance(default, tuple):
            default = [default]
            allow_multiple = False
        self.args += [(name, default)]
        self.parser.add_argument(f'--{name}', type=t, nargs='*' if allow_multiple else 1, help=help)

class Executable:
    def __init__(self, name, path, resdir, cwd, args, sources, flags, libs):
        self.name = name
        self.path = path
        self.resdir = resdir
        self.cwd = cwd
        self.args = args
        self.sources = sources
        self.flags = flags if flags is not None else []
        self.libs = libs if libs is not None else []

    def compile(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        execute([
            'g++',
            '-O3',
            *self.flags,
            '-o',
            self.path,
            *self.sources,
            *(f'-l{l}' for l in self.libs)
        ], cwd=self.cwd)

    def execute(self, test_name, cmdargs, before, after, prefix, suffix, headers):
        runs = cmdargs.runs
        a = []
        format_string = f'{self.name}-{test_name}'
        for name, default in self.args.args:
            try:
                a += [getattr(cmdargs, name)]
                if a[-1] is None:
                    a[-1] = default
            except:
                a += [default]
            if len(a[-1]) != 1:
                format_string += f'-{{{name}}}'
        format_string += '.csv'
        results = []
        for args in itertools.product(*a):
            keyargs = {}
            for i, a in enumerate(self.args.args):
                keyargs[a[0]] = args[i]
            res = Results(os.path.join(self.resdir, format_string.format(**keyargs)))
            res.set_headers(['run', *headers])
            for k, v in keyargs.items():
                res.add_comment(k, v)
            exec_args = [self.path, *(str(a) for a in args)]
            print(f'> {runs}x', ' '.join(exec_args))
            for i in range(runs):
                out = str(execute(
                    exec_args, stdout=sp.PIPE, silent=not cmdargs.verbose,
                    before=((lambda: before(cmdargs, self)) if before else None),
                    after=((lambda: after(cmdargs, self)) if after else None),
                    prefix=prefix, suffix=suffix, cwd=os.path.dirname(self.path)
                )[0], 'utf-8')
                res.add_result([i, *out.strip().split('\n')])
            res.commit()
            results += [res]
        return results


class Test:
    def __init__(self, name, exe, before, after, prefix, suffix):
        self.name = name
        self.exe = exe
        self.before = before
        self.after = after
        self.prefix = prefix
        self.suffix = suffix
        self.results = None

    def __call__(self, args, headers):
        print(f'>>> {self.name.upper()}')
        self.results = self.exe.execute(self.name, args, self.before, self.after, self.prefix, self.suffix, headers)

class Analysis:
    def __init__(self, name, func):
        self.name = name
        self.func = func

    def __call__(self, results, output):
        self.func(results, output)

class Runner:
    def __init__(self, parser, resdir, anadir, tmpdir, cwd):
        self.parser = parser
        self.resdir = resdir
        self.anadir = anadir
        self.tmpdir = tmpdir
        self.cwd = cwd
        self.exes = []
        self.tests = []
        self.analyses = []
        self.pre = []
        self.post = []
        self.args = Args(self.parser)

    def run_all(self, args):
        for exe in self.exes:
            exe.compile()
        for pre in self.pre:
            pre(args)
        for t in self.tests:
            t(args, self.headers)
        for post in self.post:
            post(args)
        for ana, tests in self.analyses:
            r = Results(os.path.join(self.anadir, f'{ana.name}.csv'))
            ana({t.name: t.results for t in tests}, r)
            r.commit()

    def add_arg(self, name, t, default, help=None):
        self.args.add_arg(name, t, default, help)

    def add_executable(self, name, sources, flags=None, libs=None):
        self.exes += [Executable(name, os.path.join(self.tmpdir, name), self.resdir, self.cwd, self.args, sources, flags, libs)]
        return self.exes[-1]

    def add_test(self, name, exe, before=None, after=None, prefix=None, suffix=None):
        self.tests += [Test(name, exe, before, after, prefix, suffix)]
        return self.tests[-1]

    def add_analysis(self, name, func, *tests):
        self.analyses += [(Analysis(name, func), tests)]
        return self.analyses[-1]

    def add_pre(self, func):
        self.pre += [func]

    def add_post(self, func):
        self.post += [func]

    def set_headers(self, hdrs):
        self.headers = hdrs