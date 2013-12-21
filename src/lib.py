# Copyright (c) 2010-2013, TOMOHIRO KUSUMI
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys

from . import allocator
from . import fileobj
from . import fileops
from . import path
from . import setting
from . import util

class Fileops (fileops.Fileops):
    def __del__(self):
        self.cleanup()

    def flush(self, f=None):
        try:
            l = super(Fileops, self).flush(f)
            if l[0]: # msg
                print(l[0])
        except fileobj.FileobjError:
            _print_exc_info()

    def read(self, x, n):
        if n is None:
            n = self.get_size() - x
        return super(Fileops, self).read(x, n)

    def delete(self, x, n, rec=True):
        if n is None:
            n = self.get_size() - x
        return super(Fileops, self).delete(x, n, rec)

    def append(self, s, rec=True):
        return self.insert(self.get_max_pos() + 1, s, rec)

    def iter_search(self, x, word, end=-1):
        while True:
            ret = self.search(x, word, end)
            if ret < 0:
                break
            yield ret
            x = ret + 1

    def iter_rsearch(self, x, word, end=-1):
        while True:
            ret = self.rsearch(x, word, end)
            if ret < 0:
                break
            yield ret
            x = ret - 1

    def iter_read(self, x, n):
        while True:
            ret = self.read(x, n)
            if not ret:
                break
            yield ret
            x += len(ret)

def _print_exc_info():
    info = sys.exc_info()
    if not setting.use_debug:
        util.print_stderr(str(info[1]))
    else:
        util.print_stderr(info[1])
        for s in util.get_traceback(info[2]):
            util.print_stderr(s)

def alloc(f, name=''):
    f = path.get_path(f)
    cls = fileobj.get_class(name)
    if cls:
        o = cls(f)
        o.set_magic()
    else:
        o = allocator.alloc(f)
        if not o:
            o = allocator.alloc('')
    return Fileops(o)