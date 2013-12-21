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

from . import rofd
from . import util

class Fileobj (rofd.Fileobj):
    _insert  = False
    _replace = True
    _delete  = False
    _enabled = True

    def __init__(self, f):
        super(Fileobj, self).__init__(f)
        self.__dirty = False
        self.__diff = {}

    def __str__(self):
        return "%s\n\ndiff size %s" % (super(Fileobj, self).__str__(),
            util.get_byte_string(len(self.__diff)))

    def clear_dirty(self):
        self.__dirty = False

    def is_dirty(self):
        return self.__dirty

    def sync(self):
        for x in sorted(self.__diff.keys()):
            self.fd.seek(x)
            self.fd.write(self.__diff[x])
        util.fsync(self.fd)

    def read(self, x, n):
        s = super(Fileobj, self).read(x, n)
        if not s or not self.__diff:
            return s
        l = list(s)
        for i in util.get_xrange(x, x + n):
            if i in self.__diff:
                l[i - x] = self.__diff[i]
        return ''.join(l)

    def replace(self, x, s, rec=True):
        # don't use buf for both ufn/rfn because ufn lose original buf
        if x + len(s) > self.get_size():
            s = s[:self.get_size() - x]
        if rec:
            ubuf = self.read(x, len(s))
            def ufn(ref):
                ref.replace(x, ubuf, False)
                return x

        for i, c in enumerate(s):
            self.__diff[x + i] = c
        self.__dirty = not not self.__diff

        if rec:
            rbuf = s[:]
            def rfn(ref):
                ref.replace(x, rbuf, False)
                return x
            self.add_undo(ufn, rfn)