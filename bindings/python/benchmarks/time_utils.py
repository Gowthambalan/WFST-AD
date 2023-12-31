"""
Copyright (c) Facebook, Inc. and its affiliates.

This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
"""

import time
import gtn


def time_func(func, iterations=100, name=None, iscuda=False):
    # warmup:
    for i in range(5):
        func()
    if iscuda:
        gtn.cuda.synchronize()
    start = time.perf_counter()
    for i in range(iterations):
        func()
    if iscuda:
        gtn.cuda.synchronize()
    time_taken = (time.perf_counter() - start) * 1e3 / iterations
    name = "function" if name is None else name
    print('"{}" took {:.3f} (ms)'.format(name, time_taken))
