#!/usr/bin/env python
import os
import sys
import time
from nose import run


def test_modules():
    topdir = os.path.dirname(__file__)
    for dirpath, _, filenames in os.walk(topdir):
        for fname in filenames:
            if _is_test_module(fname):
                yield os.path.join(dirpath, fname)

def _is_test_module(fname):
    return fname.startswith('test') and fname.endswith('.py')


def collect_execution_times(test_modules):
    sys.argv.append('--match=^test')
    sys.argv.append('-q')
    for tmodule in test_modules:
        yield(tmodule, _test_module_execution_time(tmodule))

def _test_module_execution_time(tmodule):
    starttime = time.time()
    run(defaultTest=tmodule)
    return time.time() - starttime


def write_results(exectimes):
    total = 0.0
    with open('testtimes.txt', 'w') as output:
        for record in reversed(sorted(exectimes, key=lambda record: record[1])):
            output.write('%s%.02f s\n' % (record[0].ljust(70), record[1]))
            total += record[1]
        output.write('\nTotal test execution time: %.02f seconds\n' % total)


if __name__ == '__main__':
    exectimes = collect_execution_times(test_modules())
    write_results(exectimes)

