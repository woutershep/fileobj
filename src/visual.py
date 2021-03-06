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

import sys

from . import console
from . import edit
from . import extension
from . import kbd
from . import literal
from . import methods
from . import panel
from . import screen
from . import util

VISUAL = "VISUAL"
VISUAL_LINE = "VISUAL LINE"
VISUAL_BLOCK = "VISUAL BLOCK"

class _visual_addon (object):
    def init_method(self):
        if screen.use_alt_chgat():
            self.__chgat_single = self.__alt_chgat_single
            self.__chgat_head = self.__alt_chgat_head
            self.__chgat_tail = self.__alt_chgat_tail
            self.__chgat_body = self.__alt_chgat_body

    def update_visual(self, full):
        type = self.fileops.get_region_type()
        if type == VISUAL_BLOCK:
            self.__update_block_visual(full)
        else:
            self.__update_visual(type, full)

    def __update_visual(self, type, full):
        pos = self.fileops.get_pos()
        ppos = self.fileops.get_prev_pos()
        if self.in_same_page(pos, ppos):
            self.chgat_posstr(ppos, 0)
        else:
            full = True
        self.chgat_posstr(pos, screen.A_BOLD)

        beg = self.fileops.get_region_origin()
        end = pos
        if beg > end:
            beg, end = end, beg
        mapx = self.bufmap.x
        if type == VISUAL_LINE:
            beg -= beg % mapx
            end += (mapx - 1 - end % mapx)
        self.fileops.set_region_range(
            beg, end, self.bufmap)

        pgo = self.get_page_offset()
        npgo = self.get_next_page_offset()
        if beg < pgo:
            beg = pgo
        if end > npgo - 1:
            end = npgo - 1
        lcur = pgo

        l = []
        if not full:
            a = self.get_line_offset(pos)
            b = self.get_line_offset(ppos)
            if a == b:
                l = [a]
            else:
                if a < b:
                    a, b = b, a
                l = [b + i for i in range(0, a - b + mapx, mapx)]

        limit = self.fileops.get_max_pos()
        y = self.offset.y
        x = self.offset.x
        for _ in range(self.bufmap.y):
            if lcur > limit:
                break
            lnext = lcur + mapx
            if full or (lcur in l):
                head = lcur <= beg < lnext
                tail = lcur <= end < lnext
                if head and tail:
                    self.__chgat_single(y, x, beg, end, lcur)
                elif head:
                    self.__chgat_head(y, x, beg, lcur)
                elif tail:
                    self.__chgat_tail(y, x, end, lcur)
                elif beg < lcur < end:
                    self.__chgat_body(y, x, lcur, screen.A_STANDOUT)
                else:
                    self.__chgat_body(y, x, lcur, screen.A_DEFAULT)
            lcur = lnext
            y += 1

    def __update_block_visual(self, full):
        pos = self.fileops.get_pos()
        ppos = self.fileops.get_prev_pos()
        if self.in_same_page(pos, ppos):
            self.chgat_posstr(ppos, 0)
        else:
            full = True
        self.chgat_posstr(pos, screen.A_BOLD)

        beg = self.fileops.get_region_origin()
        end = pos
        if beg > end:
            beg, end = end, beg
        mapx = self.bufmap.x
        d1 = beg % mapx
        d2 = end % mapx
        lbeg = beg - d1
        lend = end - d2
        if d1 > d2:
            d2, d1 = d1, d2
        self.fileops.set_region_range(
            lbeg + d1, lend + d2, self.bufmap)

        lcur = self.get_page_offset()
        lpos = self.get_line_offset(pos)
        lppos = self.get_line_offset(ppos)
        lr = abs(pos - ppos) != mapx # move left/right

        l = []
        if not full:
            a, b = lpos, lppos
            if a == b:
                l = [a]
            else:
                if a < b:
                    a, b = b, a
                l = [b + i for i in range(0, a - b + mapx, mapx)]

        limit = self.fileops.get_max_pos()
        y = self.offset.y
        x = self.offset.x
        for _ in range(self.bufmap.y):
            if lcur > limit:
                break
            if full or lr or (lcur in l):
                if lbeg <= lcur <= lend:
                    self.__chgat_single(y, x, lcur + d1, lcur + d2, lcur)
                elif lppos <= lcur < lbeg and lpos == lbeg and lppos < lpos:
                    self.__chgat_body(y, x, lcur, screen.A_DEFAULT) # down
                elif lend < lcur <= lppos and lpos == lend and lpos < lppos:
                    self.__chgat_body(y, x, lcur, screen.A_DEFAULT) # up
            lcur += mapx
            y += 1

    def __chgat_head(self, y, x, beg, offset):
        pos = self.get_cell_width(beg - offset)
        siz = self.get_cell_edge(self.bufmap.x) - pos
        self.chgat(y, x, pos, screen.A_DEFAULT)
        self.chgat(y, x + pos, siz, screen.A_STANDOUT)

    def __alt_chgat_head(self, y, x, beg, offset):
        """Alternative for Python 2.5"""
        pos = self.get_cell_width(beg - offset)
        buf = self.fileops.read(offset, self.bufmap.x)
        s = self.get_form_line(buf)
        d = self.get_cell_edge(self.bufmap.x) - len(s)
        if d > 0:
            s += ' ' * d
        self.printl(y, x, s[:pos], screen.A_DEFAULT)
        self.printl(y, x + pos, s[pos:], screen.A_STANDOUT)

    def __chgat_tail(self, y, x, end, offset):
        pos = self.get_cell_edge(end - offset + 1)
        siz = self.get_cell_edge(self.bufmap.x) - pos
        self.chgat(y, x, pos, screen.A_STANDOUT)
        self.chgat(y, x + pos, siz, screen.A_DEFAULT)

    def __alt_chgat_tail(self, y, x, end, offset):
        """Alternative for Python 2.5"""
        pos = self.get_cell_edge(end - offset + 1)
        buf = self.fileops.read(offset, self.bufmap.x)
        s = self.get_form_line(buf)
        d = pos - len(s)
        if d > 0:
            s += ' ' * d
        self.printl(y, x, s[:pos], screen.A_STANDOUT)
        self.printl(y, x + pos, s[pos:], screen.A_DEFAULT)

    def __chgat_single(self, y, x, beg, end, offset):
        pos = self.get_cell_width(beg - offset)
        siz = self.get_cell_edge(end - beg + 1)
        wid = self.get_cell_edge(self.bufmap.x)
        self.chgat(y, x, wid, screen.A_DEFAULT)
        self.chgat(y, x + pos, siz, screen.A_STANDOUT)

    def __alt_chgat_single(self, y, x, beg, end, offset):
        """Alternative for Python 2.5"""
        pos = self.get_cell_width(beg - offset)
        siz = self.get_cell_edge(end - beg + 1)
        end = pos + siz
        buf = self.fileops.read(offset, self.bufmap.x)
        s = self.get_form_line(buf)
        d = end - len(s)
        if d > 0:
            s += ' ' * d
        self.printl(y, x, s[:pos], screen.A_DEFAULT)
        self.printl(y, x + pos, s[pos:end], screen.A_STANDOUT)
        self.printl(y, x + end, s[end:], screen.A_DEFAULT)

    def __chgat_body(self, y, x, offset, attr):
        siz = self.get_cell_edge(self.bufmap.x)
        self.chgat(y, x, siz, attr)

    def __alt_chgat_body(self, y, x, offset, attr):
        """Alternative for Python 2.5"""
        buf = self.fileops.read(offset, self.bufmap.x)
        s = self.get_form_line(buf)
        d = self.get_cell_edge(self.bufmap.x) - len(s)
        if d > 0:
            s += ' ' * d
        self.printl(y, x, s, attr)

class BinaryCanvas (panel.BinaryCanvas, _visual_addon):
    def __init__(self, siz, pos):
        self.init_method()
        super(BinaryCanvas, self).__init__(siz, pos)

    def fill(self, low):
        super(BinaryCanvas, self).fill(low)
        self.update_visual(True)
        self.update_search(self.fileops.get_pos())

    def update_highlight(self):
        self.update_visual(False)
        self.update_search(self.fileops.get_pos())
        self.refresh()

class TextCanvas (panel.TextCanvas, _visual_addon):
    def __init__(self, siz, pos):
        self.init_method()
        super(TextCanvas, self).__init__(siz, pos)

    def fill(self, low):
        super(TextCanvas, self).fill(low)
        self.update_visual(True)
        self.update_search(self.fileops.get_pos())

    def update_highlight(self):
        self.update_visual(False)
        self.update_search(self.fileops.get_pos())
        self.refresh()

class ExtBinaryCanvas (extension.ExtBinaryCanvas, _visual_addon):
    def __init__(self, siz, pos):
        self.init_method()
        super(ExtBinaryCanvas, self).__init__(siz, pos)

    def fill(self, low):
        super(ExtBinaryCanvas, self).fill(low)
        self.update_visual(True)
        self.update_search(self.fileops.get_pos())

    def update_highlight(self):
        self.update_visual(False)
        self.update_search(self.fileops.get_pos())
        self.refresh()

class _console (console.Console):
    def init_method(self):
        this = sys.modules[__name__]
        self.add_method(literal.up           , methods, "go_up")
        self.add_method(literal.down         , methods, "go_down")
        self.add_method(literal.left         , methods, "go_left")
        self.add_method(literal.right        , methods, "go_right")
        self.add_method(literal.gg           , methods, "go_head")
        self.add_method(literal.G            , methods, "go_tail")
        self.add_method(literal.zero         , methods, "go_lhead")
        self.add_method(literal.doller       , methods, "go_ltail")
        self.add_method(literal.minus        , methods, "go_up_lhead")
        self.add_method(literal.plus         , methods, "go_down_lhead")
        self.add_method(literal.H            , methods, "go_phead")
        self.add_method(literal.M            , methods, "go_pcenter")
        self.add_method(literal.L            , methods, "go_ptail")
        self.add_method(literal.w            , methods, "go_next_char")
        self.add_method(literal.b            , methods, "go_prev_char")
        self.add_method(literal.parens_end   , methods, "go_next_zero")
        self.add_method(literal.parens_beg   , methods, "go_prev_zero")
        self.add_method(literal.bracket1_end , methods, "go_next_nonzero")
        self.add_method(literal.bracket1_beg , methods, "go_prev_nonzero")
        self.add_method(literal.bracket2_end , methods, "end_read_delayed_input")
        self.add_method(literal.bracket2_beg , methods, "start_read_delayed_input")
        self.add_method(literal.go           , methods, "go_to")
        self.add_method(literal.ctrlb        , methods, "go_pprev")
        self.add_method(literal.ctrlu        , methods, "go_hpprev")
        self.add_method(literal.ctrlf        , methods, "go_pnext")
        self.add_method(literal.ctrld        , methods, "go_hpnext")
        self.add_method(literal.resize       , methods, "resize_container")
        self.add_method(literal.ctrll        , methods, "refresh_container")
        self.add_method(literal.ctrlw_w      , this,    "_buffer_input")
        self.add_method(literal.ctrlw_W      , this,    "_buffer_input")
        self.add_method(literal.ctrlw_t      , this,    "_buffer_input")
        self.add_method(literal.ctrlw_b      , this,    "_buffer_input")
        self.add_method(literal.ctrlw_s      , this,    "_buffer_input")
        self.add_method(literal.s_split      , this,    "_buffer_input")
        self.add_method(literal.ctrlw_plus   , methods, "inc_workspace_height")
        self.add_method(literal.ctrlw_minus  , methods, "dec_workspace_height")
        self.add_method(literal.s_close      , this,    "_buffer_input")
        self.add_method(literal.s_only       , this,    "_buffer_input")
        #self.add_method(literal.s_e         , methods, "open_buffer")
        #self.add_method(literal.s_bdelete   , methods, "close_buffer")
        #self.add_method(literal.s_bfirst    , methods, "goto_first_buffer")
        #self.add_method(literal.s_blast     , methods, "goto_last_buffer")
        #self.add_method(literal.s_bnext     , methods, "goto_next_buffer")
        #self.add_method(literal.s_bprev     , methods, "goto_prev_buffer")
        self.add_method(literal.s_set        , methods, "set_option")
        self.add_method(literal.ctrlg        , this,    "_buffer_input")
        self.add_method(literal.g_ctrlg      , this,    "_buffer_input")
        self.add_method(literal.s_self       , this,    "_buffer_input")
        self.add_method(literal.s_pwd        , this,    "_buffer_input")
        self.add_method(literal.s_date       , this,    "_buffer_input")
        self.add_method(literal.s_platform   , this,    "_buffer_input")
        self.add_method(literal.s_hostname   , this,    "_buffer_input")
        self.add_method(literal.s_term       , this,    "_buffer_input")
        self.add_method(literal.s_lang       , this,    "_buffer_input")
        self.add_method(literal.s_version    , this,    "_buffer_input")
        self.add_method(literal.s_sector     , this,    "_buffer_input")
        self.add_method(literal.s_args       , this,    "_buffer_input")
        self.add_method(literal.ctrla        , this,    "_inc_number")
        self.add_method(literal.ctrlx        , this,    "_dec_number")
        #self.add_method(literal.period      , methods, "repeat")
        self.add_method(literal.toggle       , this,    "_toggle")
        self.add_method(literal.ror          , this,    "_rotate_right")
        self.add_method(literal.rol          , this,    "_rotate_left")
        self.add_method(literal.delete       , this,    "_delete")
        self.add_method(literal.X            , this,    "_delete")
        self.add_method(literal.D            , this,    "_delete")
        #self.add_method(literal.u           , methods, "undo")
        #self.add_method(literal.U           , methods, "undo_all")
        #self.add_method(literal.ctrlr       , methods, "redo")
        self.add_method(literal.m_reg        , this,    "_buffer_input")
        self.add_method(literal.backtick_reg , this,    "_buffer_input")
        self.add_method(literal.s_delmarks   , this,    "_buffer_input")
        self.add_method(literal.s_delmarksneg, this,    "_buffer_input")
        self.add_method(literal.q_reg        , methods, "start_record")
        self.add_method(literal.atsign_reg   , methods, "replay_record")
        self.add_method(literal.atsign_at    , methods, "replay_record")
        self.add_method(literal.bit_and      , this,    "_logical_bit_operation")
        self.add_method(literal.bit_or       , this,    "_logical_bit_operation")
        self.add_method(literal.bit_xor      , this,    "_logical_bit_operation")
        self.add_method(literal.y            , this,    "_yank")
        self.add_method(literal.Y            , this,    "_yank")
        self.add_method(literal.P            , this,    "_put")
        self.add_method(literal.p            , this,    "_put")
        self.add_method(literal.O            , this,    "_put")
        self.add_method(literal.o            , this,    "_put")
        self.add_method(literal.s_w          , this,    "_save_buffer")
        self.add_method(literal.s_wneg       , this,    "_force_save_buffer")
        #self.add_method(literal.s_wq        , methods, "save_buffer_quit")
        #self.add_method(literal.s_x         , methods, "xsave_buffer_quit")
        #self.add_method(literal.s_q         , methods, "quit")
        #self.add_method(literal.s_qneg      , methods, "force_quit")
        self.add_method(literal.s_fsearch    , methods, "search_forward")
        self.add_method(literal.s_rsearch    , methods, "search_backward")
        self.add_method(literal.n            , methods, "search_next_forward")
        self.add_method(literal.N            , methods, "search_next_backward")
        self.add_method(literal.escape       , this,    "_exit_visual")
        #self.add_method(literal.i           , this,    "_enter_edit_insert")
        #self.add_method(literal.I           , this,    "_enter_edit_insert_head")
        #self.add_method(literal.a           , this,    "_enter_edit_append")
        #self.add_method(literal.A           , this,    "_enter_edit_append_tail")
        self.add_method(literal.R            , this,    "_enter_edit_replace")
        self.add_method(literal.r            , this,    "_do_edit_replace")
        self.add_method(literal.v            , this,    "_enter_visual")
        self.add_method(literal.V            , this,    "_enter_line_visual")
        self.add_method(literal.ctrlv        , this,    "_enter_block_visual")

    def handle_signal(self):
        _exit_visual(self)
        return kbd.INTERRUPT

    def handle_invalid_literal(self, li):
        self.co.flash("Not a visual command " + li.str)
        return _exit_visual(self)

    def set_banner(self):
        console.set_banner(self.co.get_region_type())

class Console (_console):
    pass

class ExtConsole (_console):
    pass

def _buffer_input(self, amp, ope, args, raw):
    if raw[0] in literal.get_slow_ords():
        raw.append(kbd.ENTER)
    self.co.buffer_input(raw)
    return _exit_visual(self)

def _enter_visual(self, amp, ope, args, raw):
    return __enter_visual(self, VISUAL)

def _enter_line_visual(self, amp, ope, args, raw):
    return __enter_visual(self, VISUAL_LINE)

def _enter_block_visual(self, amp, ope, args, raw):
    return __enter_visual(self, VISUAL_BLOCK)

def __enter_visual(self, visual_type):
    if self.co.get_region_type() == visual_type:
        return _exit_visual(self)
    else:
        self.co.set_region_type(visual_type)
        return self.set_console(util.get_class(self))

def _exit_visual(self, amp=None, ope=None, args=None, raw=None):
    self.co.cleanup_region()
    return self.set_console(None)

def _(a, b):
    def _exit(fn):
        def _method(self, amp, ope, args, raw):
            _fn = b if _in_block_visual(self) else a
            _fn(self, amp, ope, args, raw)
            return fn(self, amp, ope, args, raw)
        return _method
    return _exit

def _in_block_visual(self):
    return self.co.get_region_type() == VISUAL_BLOCK

@_(methods.range_inc_number, methods.block_inc_number)
def _inc_number(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_dec_number, methods.block_dec_number)
def _dec_number(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_toggle, methods.block_toggle)
def _toggle(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_rotate_right, methods.block_rotate_right)
def _rotate_right(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_rotate_left, methods.block_rotate_left)
def _rotate_left(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_delete, methods.block_delete)
def _delete(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_logical_bit_operation, methods.block_logical_bit_operation)
def _logical_bit_operation(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_yank, methods.block_yank)
def _yank(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_put, methods.block_put)
def _put(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_save_buffer, methods.block_save_buffer)
def _save_buffer(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_force_save_buffer, methods.block_force_save_buffer)
def _force_save_buffer(self, amp, ope, args, raw):
    return _exit_visual(self)

@_(methods.range_delete, methods.block_delete)
def _enter_edit_replace(self, amp, ope, args, raw):
    self.co.cleanup_region()
    arg = edit.Arg(amp=methods.get_int(amp))
    return self.set_console(edit.get_replace_class(), arg)

def _do_edit_replace(self, amp, ope, args, raw):
    if _in_block_visual(self):
        cls = edit.get_block_replace_class()
    else:
        cls = edit.get_range_replace_class()
    arg = edit.Arg(limit=edit.get_input_limit(),
        start=self.co.get_region_range()[0])
    return self.set_console(cls, arg)
