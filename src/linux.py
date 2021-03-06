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
import re

from . import libc
from . import log
from . import unix
from . import util

PTRACE_PEEKTEXT = 1
PTRACE_PEEKDATA = 2
PTRACE_POKETEXT = 4
PTRACE_POKEDATA = 5
PTRACE_CONT     = 7
PTRACE_KILL     = 8
PTRACE_ATTACH   = 16
PTRACE_DETACH   = 17

def get_term_info():
    return unix.get_term_info()

def get_lang_info():
    return unix.get_lang_info()

def get_blkdev_info(fd):
    try:
        d = {   "BLKSSZGET"  : 0x1268,
                "BLKGETSIZE" : 0x1260, }
        s = "BLKSSZGET"
        sector_size = unix.ioctl_get_int(fd, d[s], 4)
        s = "BLKGETSIZE"
        size = unix.ioctl_get_int(fd, d[s], 8)
        size <<= 9
        return size, sector_size, ''
    except Exception as e:
        log.error("ioctl({0}, {1}) failed, {2}".format(fd.name, s, e))
        raise

def stat_size(f):
    return unix.stat_size(f)

def read_size(f):
    return unix.read_size(f)

def get_inode(f):
    return unix.get_inode(f)

def fopen(f, mode='r'):
    return unix.fopen(f, mode)

def fopen_text(f, mode='r'):
    return unix.fopen_text(f, mode)

def fcreat(f):
    return unix.fcreat(f)

def fcreat_text(f):
    return unix.fcreat_text(f)

def symlink(source, link_name):
    return unix.symlink(source, link_name)

def fsync(fd):
    return unix.fsync(fd)

def truncate(f, offset):
    return unix.truncate(f, offset)

def utime(f, st):
    return unix.utime(f, st)

def touch(f):
    return unix.touch(f)

def stat_type(f):
    return unix.stat_type(f)

def get_page_size():
    return unix.get_page_size()

def set_non_blocking(fd):
    return unix.set_non_blocking(fd)

def get_terminal_size():
    return unix.get_terminal_size()

def get_tc(fd):
    return unix.get_tc(fd)

def set_tc(fd):
    return unix.set_tc(fd)

def set_cbreak(fd):
    return unix.set_cbreak(fd)

def get_total_ram():
    return get_meminfo("MemTotal")

def get_free_ram():
    return get_meminfo("MemFree")

def get_meminfo(s):
    f = unix.get_procfs_entry("meminfo")
    if not f:
        return -1
    try:
        s = util.escape_regex_pattern(s)
        for l in fopen_text(f):
            m = re.match(r"^{0}.*\s+(\d+)".format(s), l)
            if m:
                return int(m.group(1)) * util.KiB
    except Exception as e:
        log.error(e)
    return -1

def is_blkdev(f):
    l = stat_type(f)
    if l != -1:
        return l[2] # blk
    else:
        return False

def is_blkdev_supported():
    return True

def has_mmap():
    return True

def has_mremap():
    return True

def has_pid_access(pid):
    return unix.kill_sig_zero(pid)

def has_pid(pid):
    return unix.fs_has_pid(pid) or unix.ps_has_pid(pid)

def get_pid_name(pid):
    # comm does not exist on older kernels
    ret = unix.get_pid_name_from_fs(pid, "comm", "cmdline")
    if not ret:
        return unix.get_pid_name_from_ps(pid, __parse_ps_name)
    else:
        return ret

def __parse_ps_name(name):
    cmd = name.split(" ")[0]
    if re.match(r"^\[.+\]$", cmd): # kernel thread
        return cmd[1:-1]
    else:
        return os.path.basename(cmd)

def is_pid_path_supported():
    return libc.has_ptrace()

def ptrace_peektext(pid, addr):
    return libc.ptrace(PTRACE_PEEKTEXT, pid, addr, None)

def ptrace_peekdata(pid, addr):
    return libc.ptrace(PTRACE_PEEKDATA, pid, addr, None)

def ptrace_poketext(pid, addr, data):
    return libc.ptrace(PTRACE_POKETEXT, pid, addr, data)

def ptrace_pokedata(pid, addr, data):
    return libc.ptrace(PTRACE_POKEDATA, pid, addr, data)

def ptrace_cont(pid):
    return libc.ptrace(PTRACE_CONT, pid, None, None)

def ptrace_kill(pid):
    return libc.ptrace(PTRACE_KILL, pid, None, None)

def ptrace_attach(pid):
    return libc.ptrace(PTRACE_ATTACH, pid, None, None)

def ptrace_detach(pid):
    return libc.ptrace(PTRACE_DETACH, pid, None, None)

ptrace_peek = ptrace_peektext
ptrace_poke = ptrace_poketext

def get_ptrace_word_size():
    return libc.get_ptrace_data_size()

def parse_waitpid_result(status):
    return unix.parse_waitpid_result(status)

def init():
    libc.init_ptrace("long")
