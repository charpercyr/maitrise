
from exp.execute import execute

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
        self.results += [res]

    def set_headers(self, hdrs):
        self.headers = hdrs

    def commit(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as file:
            for k, v in self.comments.items():
                file.write(f'{k},{v}\n')
            file.write('\n')
            file.write(','.join(self.headers) + '\n')
            for r in self.results:
                file.write(','.join(str(i) for i in r) + '\n')

class Executable:
    def __init__(self, name, path, resdir, cwd, parser, sources, flags, libs):
        self.name = name
        self.path = path
        self.resdir = resdir
        self.cwd = cwd
        self.parser = parser
        self.sources = sources
        self.flags = flags if flags is not None else []
        self.libs = libs if libs is not None else []
        self.args = []
        self.headers = []

    def add_arg(self, name, t, default, help=None):
        if not isinstance(default, list) and not isinstance(default, tuple):
            default = [default]
        self.args += [(name, default)]
        self.parser.add_argument(f'--{name}', type=t, nargs='*', help=help)

    def set_headers(self, hdrs):
        self.headers = hdrs

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

    def execute(self, args, before, after):
        runs = args.runs
        a = []
        format_string = self.name
        for name, default in self.args:
            try:
                a += [getattr(args, name)]
                if a[-1] is None:
                    a[-1] = default
            except:
                a += [default]
            if len(a[-1]) != 1:
                format_string += f'-{{{name}}}'
        format_string += '.csv'
        for args in itertools.product(*a):
            keyargs = {}
            for i, a in enumerate(self.args):
                keyargs[a[0]] = args[i]
            res = Results(os.path.join(self.resdir, format_string.format(**keyargs)))
            res.set_headers(['run', *self.headers])
            for k, v in keyargs.items():
                res.add_comment(k, v)
            exec_args = [self.path, *(str(a) for a in args)]
            print(f'> {runs}x', ' '.join(exec_args))
            for i in range(runs):
                out = str(execute(exec_args, stdout=sp.PIPE, silent=True)[0], 'utf-8')
                res.add_result([i, *out.strip().split('\n')])
            res.commit()


class Test:
    def __init__(self, name, exe, before, after):
        pass

    def __call__(self, args):
        pass

class Runner:
    def __init__(self, parser, resdir, tmpdir, cwd):
        self.parser = parser
        self.resdir = resdir
        self.tmpdir = tmpdir
        self.cwd = cwd
        self.exes = []
        self.tests = []
        self.pre = []
        self.post = []

    def run_all(self, args):
        for exe in self.exes:
            exe.compile()
        for pre in self.pre:
            pre()
        for t in self.tests:
            t(args)
        for post in self.post:
            post()

    def add_executable(self, name, sources, flags=None, libs=None):
        self.exes += [Executable(name, os.path.join(self.tmpdir, name), self.resdir, self.cwd, self.parser, sources, flags, libs)]
        return self.exes[-1]

    def add_test(self, name, exe, before=None, after=None):
        pass

    def set_headers(self, hdrs):
        pass

    def add_pre(self, func):
        self.pre += [func]

    def add_post(self, func):
        self.post += [func]