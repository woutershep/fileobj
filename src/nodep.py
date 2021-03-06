# Copyright (c) 2010-2016, TOMOHIRO KUSUMI
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
import platform
import sys

def __test(version, name):
    if not version:
        version = sys.version_info
    version = tuple(version[:3])
    if not name:
        name = platform.system()
    name = name.lower()

    s = "Using Python %s" % '.'.join([str(x) for x in version])
    if version < (2, 6, 0):
        raise Exception("%s\nPython 2.6 or above is required" % s)
    elif "windows" in name:
        raise Exception("Windows is not supported")
    import curses
    del curses

def test():
    if __ignore_test():
        return -1
    try:
        __test(None, None)
    except Exception:
        e = sys.exc_info()[1]
        sys.stderr.write("%s\n" % e)
        sys.exit(1)

def __ignore_test():
    e = os.getenv("FILEOBJ_USE_TEST")
    if isinstance(e, str) and e.lower() == "false":
        return True
    else:
        return False

if __name__ == '__main__':
    test()
