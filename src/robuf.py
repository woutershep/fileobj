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

import os

from . import chunk
from . import fileobj
from . import log
from . import screen
from . import setting
from . import util

class Fileobj (fileobj.Fileobj):
    _insert  = False
    _replace = False
    _delete  = False
    _enabled = True

    def __init__(self, f):
        self.cbuf = []
        self.__thresh = 0
        self.set_size(0)
        super(Fileobj, self).__init__(f)

    def __str__(self):
        l = []
        l.append("size %s" % util.get_byte_string(self.get_size()))
        l.append("chunk size %d[B]" % setting.robuf_chunk_size)
        l.append("chunk total %d\n" % len(self.cbuf))
        for i, o in enumerate(self.cbuf):
            l.append("[%d] %s" % (i, o))
        return '\n'.join(l)

    def init(self):
        assert not self.cbuf
        f = self.get_path()
        if os.path.exists(f):
            self.init_chunk(open(f).read())
        else:
            self.init_chunk('')

    def is_dirty(self):
        return False

    def get_size(self):
        return self.__size

    def set_size(self, size):
        self.__size = size

    def set_search_thresh(self):
        r = setting.robuf_search_thresh_ratio
        if r is None: # heuristic
            if len(self.cbuf) > 10000:
                r = 0.01
            elif len(self.cbuf) > 1000:
                r = 0.02
            elif len(self.cbuf) > 20:
                r = 0.1
            else:
                r = 0.5
        self.__thresh = int(self.get_size() * r)
        if self.__thresh:
            log.debug("%s has search thresh at %d[B]/%d[B]" %
                (self.get_short_path(), self.__thresh, self.get_size()))

    def alloc_chunk(self, offset, buf):
        return chunk.Chunk(offset, buf)

    def init_chunk(self, b):
        self.cbuf = []
        for i in range(0, len(b), setting.robuf_chunk_size):
            s = b[i : i + setting.robuf_chunk_size]
            self.cbuf.append(self.alloc_chunk(i, s))
        self.set_size(len(b))
        self.mark_chunk()
        self.set_search_thresh()

    def mark_chunk(self):
        if not self.cbuf:
            self.cbuf.append(self.alloc_chunk(0, ''))
        self.cbuf[-1].last = True

    def search(self, x, s, end=-1):
        for o in self.cbuf:
            if end != -1 and x >= end:
                break
            if x in o:
                i = self.cbuf.index(o)
                if i < len(self.cbuf) - 1:
                    pos = self.cbuf[i + 1].offset
                    siz = len(s) - 1
                    b = self.read(pos, siz)
                else:
                    b = ''
                ret = o.search(x, s, b)
                if ret != -1:
                    return ret
                x = o.offset + len(o)
            if screen.test_signal():
                return -2
        return -1

    def rsearch(self, x, s, end=-1):
        for o in reversed(self.cbuf):
            if end != -1 and x <= end:
                break
            if x in o:
                i = self.cbuf.index(o)
                if i > 0:
                    siz = len(s) - 1
                    pos = o.offset - siz
                    if pos < 0:
                        siz = o.offset
                        pos = 0
                    b = self.read(pos, siz)
                else:
                    b = ''
                ret = o.rsearch(x, s, b)
                if ret != -1:
                    return ret
                x = o.offset - 1
            if screen.test_signal():
                return -2
        return -1

    def get_chunk_index(self, pos):
        if pos <= self.__thresh:
            for o in self.cbuf:
                if pos in o:
                    return self.cbuf.index(o)
        else:
            beg = 0
            end = len(self.cbuf) - 1
            while True:
                i = (beg + end) / 2
                o = self.cbuf[i]
                if pos in o:
                    return self.cbuf.index(o)
                if pos < o.offset:
                    end = i - 1
                elif pos > o.offset + len(o) - 1:
                    beg = i + 1
                if beg > end:
                    break
        assert 0, pos

    def read(self, x, n):
        buf = []
        for i in range(self.get_chunk_index(x), len(self.cbuf)):
            s = self.cbuf[i].read(x, n)
            if s:
                buf.append(s)
                x += len(s)
                n -= len(s)
                if n <= 0:
                    break # doesn't always come here
        return ''.join(buf)