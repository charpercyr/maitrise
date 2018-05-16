
from argparse import ArgumentParser
import os
import tempfile


tests = [
    'perf'
]

PROJECT_SRC_DIR=os.path.abspath(os.path.dirname(__file__))
RESULTS_DIR='results'

def main():
    parser = ArgumentParser()

    args = parser.parse_args()