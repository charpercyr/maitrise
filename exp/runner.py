
from exp.execute import execute

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
        with open(self.path, 'w') as file:
            for k, v in self.comments.items():
                file.write(f'{k},{v}\n')
            file.write(','.join(self.headers) + '\n')
            for r in self.results:
                file.write(','.join(str(i) for i in r) + '\n')
    
class Executable:
    def __init__(self, name, path, parser, sources, flags, libs):
        self.name = name
        self.path = path
        self.parser = parser
        self.sources = sources
        self.flags = flags
        self.libs = libs
        self.args = []

    def add_arg(self, name, t, default):
        if not isinstance(default, list) and not isinstance(default, tuple):
            default = [default]
        self.args += [(name, t, default)]
        self.parser.add_argument(f'--{name}', type=t, nargs='*')

    def compile(self):
        execute([
            'g++',
            '-O3',
            *self.flags,
            *self.sources,
            *(f'-l{l}' for l in self.libs)
        ])

    def prepare(self, results):
        pass

    def execute(self, args):
        pass


class Test:
    def __init__(self, name, exe):
        pass

class Runner:
    def __init__(self, parser, resdir, tmpdir):
        self.parser = parser
        self.resdir = resdir
        self.tmpdir = tmpdir
        self.exes = []
        self.tests = []
        self.pre = []
        self.post = []

    def run_all(self):
        for exe in self.exes:
            exe.compile()
        for pre in self.pre:
            pre()

    def add_executable(self, name, sources, flags=None, libs=None):
        self.exes += [Executable(name, os.path.join(self.tmpdir, name), self.parser, sources, flags, libs)]
        return self.exes[-1]

    def add_test(self, name, exe, before=None, after=None):
        pass

    def set_headers(self, hdrs):
        pass