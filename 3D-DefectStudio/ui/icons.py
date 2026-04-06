# -*- coding: utf-8 -*-
"""
Icon Factory - Icon generation and management
Provides modern self-drawn icons for the UI — no QStyle system icons.
"""

import os
import math
import numpy as np
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (QIcon, QPixmap, QPainter, QPen, QBrush, QColor,
                            QPainterPath, QRadialGradient, QLinearGradient)
from PySide6.QtWidgets import QApplication, QStyle

from .design_tokens import DesignTokens


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _canvas(size: int):
    px = QPixmap(size, size)
    px.fill(Qt.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    return px, p


# ─────────────────────────────────────────────────────────────────────────────
#  UIIcons — self-drawn icon set
# ─────────────────────────────────────────────────────────────────────────────

class UIIcons:
    _CACHE: dict = {}

    # palette
    BLUE    = QColor("#4f8ef7")
    BLUE2   = QColor("#7eb3ff")
    GRAY    = QColor("#8899bb")
    LGRAY   = QColor("#b0bcd4")
    RED     = QColor("#e05555")
    ORANGE  = QColor("#f0903a")
    GREEN   = QColor("#4caf7d")
    YELLOW  = QColor("#f0c040")
    WHITE   = QColor("#e8eaf6")
    BG      = QColor("#181b2a")

    @classmethod
    def get(cls, name: str, size: int = 32) -> QIcon:
        key = f"{name}@{size}"
        if key not in cls._CACHE:
            fn = getattr(cls, f"_i_{name}", None)
            if fn is None:
                return QIcon()
            px, p = _canvas(size)
            fn(p, size)
            p.end()
            cls._CACHE[key] = QIcon(px)
        return cls._CACHE[key]

    # ── open folder ───────────────────────────────────────────────────────────
    @classmethod
    def _i_open(cls, p, s):
        c = cls.BLUE
        p.setPen(Qt.NoPen)
        p.setBrush(c.darker(150))
        p.drawRoundedRect(QRectF(s*.10, s*.34, s*.80, s*.50), s*.06, s*.06)
        tab = QPainterPath()
        tab.moveTo(s*.10, s*.34); tab.lineTo(s*.10, s*.26)
        tab.lineTo(s*.40, s*.26); tab.lineTo(s*.48, s*.34)
        tab.closeSubpath()
        p.setBrush(c.darker(130)); p.drawPath(tab)
        front = QPainterPath()
        front.moveTo(s*.06, s*.78); front.lineTo(s*.14, s*.44)
        front.lineTo(s*.94, s*.44); front.lineTo(s*.86, s*.78)
        front.closeSubpath()
        p.setBrush(c); p.drawPath(front)

    # ── export  (arrow up out of tray) ────────────────────────────────────────
    @classmethod
    def _i_export(cls, p, s):
        c = cls.BLUE2
        pen = QPen(c, s*.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(s*.18,s*.78), QPointF(s*.82,s*.78))
        p.drawLine(QPointF(s*.18,s*.78), QPointF(s*.18,s*.58))
        p.drawLine(QPointF(s*.82,s*.78), QPointF(s*.82,s*.58))
        p.drawLine(QPointF(s*.50,s*.58), QPointF(s*.50,s*.22))
        arr = QPainterPath()
        arr.moveTo(s*.50,s*.14); arr.lineTo(s*.30,s*.36); arr.lineTo(s*.70,s*.36)
        arr.closeSubpath()
        p.setBrush(c); p.setPen(Qt.NoPen); p.drawPath(arr)

    # ── save_data  (floppy + green down-arrow) ────────────────────────────────
    @classmethod
    def _i_save_data(cls, p, s):
        c = cls.GREEN
        p.setPen(Qt.NoPen)
        p.setBrush(c.darker(150))
        p.drawRoundedRect(QRectF(s*.14,s*.12,s*.72,s*.76), s*.07, s*.07)
        p.setBrush(cls.WHITE)
        p.drawRect(QRectF(s*.24,s*.12,s*.40,s*.28))
        p.setBrush(c.darker(130))
        p.drawRect(QRectF(s*.54,s*.12,s*.12,s*.18))
        p.setBrush(c.darker(120))
        p.drawRoundedRect(QRectF(s*.24,s*.56,s*.52,s*.24), s*.04, s*.04)
        pen = QPen(c, s*.08, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(s*.50,s*.28), QPointF(s*.50,s*.46))
        arr = QPainterPath()
        arr.moveTo(s*.50,s*.54); arr.lineTo(s*.36,s*.40); arr.lineTo(s*.64,s*.40)
        arr.closeSubpath()
        p.setBrush(c); p.setPen(Qt.NoPen); p.drawPath(arr)

    # ── home / reset view ─────────────────────────────────────────────────────
    @classmethod
    def _i_home(cls, p, s):
        c = cls.BLUE
        p.setPen(Qt.NoPen)
        roof = QPainterPath()
        roof.moveTo(s*.50,s*.12); roof.lineTo(s*.88,s*.46); roof.lineTo(s*.12,s*.46)
        roof.closeSubpath()
        p.setBrush(c); p.drawPath(roof)
        p.setBrush(c.darker(150))
        p.drawRect(QRectF(s*.22,s*.44,s*.56,s*.42))
        p.setBrush(c.darker(110))
        p.drawRect(QRectF(s*.40,s*.60,s*.20,s*.26))

    # ── clear / broom ─────────────────────────────────────────────────────────
    @classmethod
    def _i_clear(cls, p, s):
        c = cls.ORANGE
        pen = QPen(c, s*.09, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawLine(QPointF(s*.70,s*.16), QPointF(s*.28,s*.72))
        pen2 = QPen(c.lighter(130), s*.065, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen2)
        p.drawLine(QPointF(s*.22,s*.68), QPointF(s*.12,s*.86))
        p.drawLine(QPointF(s*.30,s*.74), QPointF(s*.22,s*.88))
        p.drawLine(QPointF(s*.38,s*.76), QPointF(s*.34,s*.88))
        p.setPen(Qt.NoPen); p.setBrush(c.lighter(160))
        for rx,ry in [(.54,.72),(.62,.78),(.50,.82)]:
            p.drawEllipse(QRectF(s*rx,s*ry,s*.06,s*.06))

    # ── delete / trash can ────────────────────────────────────────────────────
    @classmethod
    def _i_delete(cls, p, s):
        c = cls.RED
        p.setPen(Qt.NoPen)
        p.setBrush(c)
        p.drawRoundedRect(QRectF(s*.14,s*.20,s*.72,s*.10), s*.04, s*.04)
        p.setBrush(c.lighter(130))
        p.drawRoundedRect(QRectF(s*.38,s*.13,s*.24,s*.09), s*.04, s*.04)
        body = QPainterPath()
        body.moveTo(s*.20,s*.30); body.lineTo(s*.26,s*.84)
        body.lineTo(s*.74,s*.84); body.lineTo(s*.80,s*.30)
        body.closeSubpath()
        p.setBrush(c.darker(130)); p.drawPath(body)
        pen = QPen(c.darker(160), s*.055, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        for x in [.40,.50,.60]:
            p.drawLine(QPointF(s*x,s*.38), QPointF(s*x,s*.76))

    # ── select / dashed rectangle ─────────────────────────────────────────────
    @classmethod
    def _i_select(cls, p, s):
        c = cls.BLUE2
        pen = QPen(c, s*.07); pen.setStyle(Qt.DashLine)
        p.setPen(pen)
        p.setBrush(QColor(c.red(),c.green(),c.blue(),35))
        p.drawRoundedRect(QRectF(s*.14,s*.14,s*.72,s*.72), s*.10, s*.10)
        p.setPen(Qt.NoPen); p.setBrush(c)
        r = s*.07
        for cx,cy in [(.14,.14),(.86,.14),(.14,.86),(.86,.86)]:
            p.drawEllipse(QRectF(s*cx-r, s*cy-r, r*2, r*2))

    # ── commit / checkmark ────────────────────────────────────────────────────
    @classmethod
    def _i_commit(cls, p, s):
        pen = QPen(cls.GREEN, s*.12, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        path = QPainterPath()
        path.moveTo(s*.18,s*.52); path.lineTo(s*.42,s*.74); path.lineTo(s*.82,s*.26)
        p.drawPath(path)

    # ── cancel / X ────────────────────────────────────────────────────────────
    @classmethod
    def _i_cancel(cls, p, s):
        pen = QPen(cls.RED, s*.11, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(s*.22,s*.22), QPointF(s*.78,s*.78))
        p.drawLine(QPointF(s*.78,s*.22), QPointF(s*.22,s*.78))

    # ── restore / undo ────────────────────────────────────────────────────────
    @classmethod
    def _i_restore(cls, p, s):
        c = cls.BLUE
        pen = QPen(c, s*.09, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(s*.18,s*.22,s*.64,s*.58), 30*16, 270*16)
        arr = QPainterPath()
        arr.moveTo(s*.50,s*.18); arr.lineTo(s*.32,s*.34); arr.lineTo(s*.68,s*.34)
        arr.closeSubpath()
        p.setBrush(c); p.setPen(Qt.NoPen); p.drawPath(arr)

    # ── axis ─────────────────────────────────────────────────────────────────
    @classmethod
    def _i_axis(cls, p, s):
        o = QPointF(s*.50, s*.62)
        p.setPen(QPen(QColor("#e05555"), s*.08, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(o, QPointF(s*.86,s*.80))
        p.setPen(QPen(QColor("#4caf7d"), s*.08, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(o, QPointF(s*.14,s*.80))
        p.setPen(QPen(QColor("#4f8ef7"), s*.08, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(o, QPointF(s*.50,s*.14))
        p.setPen(Qt.NoPen); p.setBrush(cls.WHITE)
        p.drawEllipse(QRectF(s*.43,s*.54,s*.14,s*.14))

    # ── grid ─────────────────────────────────────────────────────────────────
    @classmethod
    def _i_grid(cls, p, s):
        pen = QPen(cls.GRAY, s*.055, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        for i in [.22,.50,.78]:
            p.drawLine(QPointF(s*i,s*.18), QPointF(s*i,s*.82))
            p.drawLine(QPointF(s*.18,s*i), QPointF(s*.82,s*i))

    # ── zoom in ───────────────────────────────────────────────────────────────
    @classmethod
    def _i_zoom_in(cls, p, s):
        c = cls.BLUE2
        pen = QPen(c, s*.09, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(s*.14,s*.14,s*.52,s*.52))
        p.drawLine(QPointF(s*.58,s*.58), QPointF(s*.84,s*.84))
        p.drawLine(QPointF(s*.28,s*.40), QPointF(s*.52,s*.40))
        p.drawLine(QPointF(s*.40,s*.28), QPointF(s*.40,s*.52))

    # ── zoom out ──────────────────────────────────────────────────────────────
    @classmethod
    def _i_zoom_out(cls, p, s):
        c = cls.LGRAY
        pen = QPen(c, s*.09, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawEllipse(QRectF(s*.14,s*.14,s*.52,s*.52))
        p.drawLine(QPointF(s*.58,s*.58), QPointF(s*.84,s*.84))
        p.drawLine(QPointF(s*.28,s*.40), QPointF(s*.52,s*.40))

    # ── background color ─────────────────────────────────────────────────────
    @classmethod
    def _i_color(cls, p, s):
        c = cls.YELLOW
        p.setPen(Qt.NoPen)
        body = QPainterPath()
        body.moveTo(s*.28,s*.36); body.lineTo(s*.22,s*.78)
        body.lineTo(s*.72,s*.78); body.lineTo(s*.66,s*.36)
        body.closeSubpath()
        p.setBrush(c.darker(140)); p.drawPath(body)
        p.setBrush(c.darker(110))
        p.drawRect(QRectF(s*.24,s*.30,s*.46,s*.08))
        pen = QPen(cls.GRAY, s*.07, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(s*.30,s*.12,s*.34,s*.22), 0, 180*16)
        p.setPen(Qt.NoPen); p.setBrush(c)
        p.drawEllipse(QRectF(s*.34,s*.46,s*.28,s*.24))

    # ── auto rotate ───────────────────────────────────────────────────────────
    @classmethod
    def _i_rotate(cls, p, s):
        c = cls.BLUE
        pen = QPen(c, s*.09, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen); p.setBrush(Qt.NoBrush)
        p.drawArc(QRectF(s*.16,s*.16,s*.68,s*.68), -30*16, 300*16)
        arr = QPainterPath()
        arr.moveTo(s*.74,s*.68); arr.lineTo(s*.60,s*.60); arr.lineTo(s*.82,s*.54)
        arr.closeSubpath()
        p.setBrush(c); p.setPen(Qt.NoPen); p.drawPath(arr)

    # ── theme ─────────────────────────────────────────────────────────────────
    @classmethod
    def _i_theme(cls, p, s):
        p.setPen(Qt.NoPen)
        p.setBrush(cls.GRAY)
        p.drawEllipse(QRectF(s*.16,s*.16,s*.68,s*.68))
        p.setBrush(cls.BG)
        p.drawEllipse(QRectF(s*.26,s*.12,s*.68,s*.68))
        pen = QPen(cls.YELLOW, s*.07, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        for deg in range(0, 360, 60):
            rad = math.radians(deg)
            cx, cy = s*.50, s*.50
            p.drawLine(QPointF(cx+math.cos(rad)*s*.28, cy+math.sin(rad)*s*.28),
                       QPointF(cx+math.cos(rad)*s*.40, cy+math.sin(rad)*s*.40))

    # ── folder (train/test) ───────────────────────────────────────────────────
    @classmethod
    def _i_folder(cls, p, s):
        c = cls.YELLOW
        p.setPen(Qt.NoPen)
        p.setBrush(c.darker(150))
        p.drawRoundedRect(QRectF(s*.10,s*.34,s*.80,s*.50), s*.06, s*.06)
        tab = QPainterPath()
        tab.moveTo(s*.10,s*.34); tab.lineTo(s*.10,s*.26)
        tab.lineTo(s*.40,s*.26); tab.lineTo(s*.48,s*.34)
        tab.closeSubpath()
        p.setBrush(c.darker(120)); p.drawPath(tab)
        p.setBrush(c)
        p.drawRoundedRect(QRectF(s*.10,s*.40,s*.80,s*.44), s*.06, s*.06)

    # ── gear ─────────────────────────────────────────────────────────────────
    @classmethod
    def _i_gear(cls, p, s):
        c = cls.GRAY
        cx, cy = s*.50, s*.50
        r_o, r_i = s*.36, s*.24
        teeth = 8
        path = QPainterPath()
        for i in range(teeth * 2):
            angle = math.radians(i * 180 / teeth)
            r = r_o if i % 2 == 0 else r_i * 1.10
            x = cx + math.cos(angle) * r
            y = cy + math.sin(angle) * r
            if i == 0: path.moveTo(x, y)
            else: path.lineTo(x, y)
        path.closeSubpath()
        p.setPen(Qt.NoPen); p.setBrush(c); p.drawPath(path)
        p.setBrush(cls.BG)
        p.drawEllipse(QRectF(cx-s*.12, cy-s*.12, s*.24, s*.24))

    # ── info / help ───────────────────────────────────────────────────────────
    @classmethod
    def _i_info(cls, p, s):
        c = cls.BLUE
        p.setPen(Qt.NoPen); p.setBrush(c)
        p.drawEllipse(QRectF(s*.16,s*.16,s*.68,s*.68))
        pen = QPen(QColor("white"), s*.10, Qt.SolidLine, Qt.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(s*.50,s*.44), QPointF(s*.50,s*.72))
        p.setPen(Qt.NoPen); p.setBrush(QColor("white"))
        p.drawEllipse(QRectF(s*.43,s*.26,s*.14,s*.14))

    # ── color picker (prop panel solid-color button) ──────────────────────────
    @classmethod
    def _i_colorpicker(cls, p, s):
        cx, cy, r = s*.50, s*.50, s*.36
        seg = 12
        for i in range(seg):
            c = QColor.fromHsvF(i/seg, 0.85, 0.95)
            path = QPainterPath()
            path.moveTo(cx, cy)
            path.arcTo(QRectF(cx-r,cy-r,r*2,r*2), i*360/seg, 360/seg)
            path.closeSubpath()
            p.setBrush(c); p.setPen(Qt.NoPen); p.drawPath(path)
        p.setBrush(cls.BG)
        p.drawEllipse(QRectF(cx-s*.18, cy-s*.18, s*.36, s*.36))


# ─────────────────────────────────────────────────────────────────────────────
#  SystemIconHelper  (drop-in, now self-drawn)
# ─────────────────────────────────────────────────────────────────────────────

class SystemIconHelper:
    _MAP = {
        'open':       'open',
        'save':       'export',       # Export button
        'save_data':  'save_data',    # Save Data button  (distinct green floppy)
        'zoom-in':    'zoom_in',
        'zoom-out':   'zoom_out',
        'rotate':     'rotate',
        'theme':      'theme',
        'home':       'home',
        'grid':       'grid',
        'axis':       'axis',
        'clear':      'clear',        # broom  (orange)
        'color':      'color',        # paint bucket
        'delete':     'delete',       # trash  (red)
        'info':       'info',
        'select':     'select',
        'commit':     'commit',
        'cancel':     'cancel',
        'restore':    'restore',
        'folder':     'folder',
        'gear':       'gear',
        'colorpicker':'colorpicker',
    }

    @staticmethod
    def get_icon(name: str, size: int = 32) -> 'QIcon':
        mapped = SystemIconHelper._MAP.get(name, name).replace('-', '_')
        return UIIcons.get(mapped, size)


# ─────────────────────────────────────────────────────────────────────────────
#  Anomaly-type icons  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

class ModernIconFactory:
    @staticmethod
    def create_icon(name: str, size: int = 64, accent_color: str = None) -> 'QIcon':
        from PySide6.QtCore import Qt
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        color_base = QColor(accent_color) if accent_color else QColor(DesignTokens.ACCENT_BLUE)
        color_err  = QColor(DesignTokens.ANOMALY)
        rect = pixmap.rect().adjusted(6, 6, -6, -6)
        w, h = rect.width(), rect.height()
        pen_err = QPen(color_err); pen_err.setWidth(3)
        draw = {
            'sphere':  ModernIconFactory._draw_sphere,
            'scratch': ModernIconFactory._draw_scratch,
            'bend':    ModernIconFactory._draw_bend,
            'crack':   ModernIconFactory._draw_crack,
            'lasso':   ModernIconFactory._draw_lasso,
            'random':  ModernIconFactory._draw_random,
        }.get(name)
        if draw:
            draw(painter, rect, w, h, color_base, color_err, pen_err)
        painter.end()
        return QIcon(pixmap)

    @staticmethod
    def _draw_sphere(painter, rect, w, h, cb, ce, pe):
        g = QRadialGradient(w/2, h/2, w/2)
        g.setColorAt(0, cb.lighter(150)); g.setColorAt(.7, cb); g.setColorAt(1, cb.darker(120))
        painter.setBrush(QBrush(g)); painter.setPen(Qt.NoPen); painter.drawEllipse(rect)
        painter.setBrush(ce); painter.drawEllipse(int(w/2)-3, int(h/2)-3, 6, 6)

    @staticmethod
    def _draw_scratch(painter, rect, w, h, cb, ce, pe):
        painter.setBrush(QColor("#3a3a3a")); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect.adjusted(2,6,-2,-6), 4, 4)
        path = QPainterPath()
        path.moveTo(rect.left()+6, rect.bottom()-10); path.lineTo(rect.right()-6, rect.top()+10)
        gp = QPen(ce.lighter(130)); gp.setWidth(5)
        painter.setPen(gp); painter.drawPath(path)
        painter.setPen(pe); painter.drawPath(path)

    @staticmethod
    def _draw_bend(painter, rect, w, h, cb, ce, pe):
        path = QPainterPath()
        path.moveTo(rect.left(), rect.bottom()-8)
        path.quadTo(rect.center().x(), rect.top()-5, rect.right(), rect.bottom()-8)
        g = QLinearGradient(rect.left(), rect.center().y(), rect.right(), rect.center().y())
        g.setColorAt(0, cb); g.setColorAt(.5, cb.lighter(130)); g.setColorAt(1, cb)
        pt = QPen(QBrush(g), 10); pt.setCapStyle(Qt.RoundCap)
        painter.setPen(pt); painter.drawPath(path)
        painter.setPen(pe); painter.setBrush(ce)
        ap = QPainterPath()
        cx, cy = rect.center().x(), rect.center().y()-8
        ap.moveTo(cx,cy); ap.lineTo(cx-6,cy-10); ap.lineTo(cx+6,cy-10); ap.closeSubpath()
        painter.drawPath(ap)

    @staticmethod
    def _draw_crack(painter, rect, w, h, cb, ce, pe):
        painter.setBrush(QColor("#3a3a3a")); painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect.adjusted(3,3,-3,-3), 6, 6)
        cp = QPainterPath()
        cx, cy = rect.center().x(), rect.center().y()
        cp.moveTo(cx, rect.top()+8); cp.lineTo(cx-4,cy-4); cp.lineTo(cx+6,cy-2)
        cp.lineTo(cx+2,cy+4); cp.lineTo(cx-6,cy+2); cp.lineTo(cx,rect.bottom()-8)
        painter.setPen(pe); painter.drawPath(cp)

    @staticmethod
    def _draw_lasso(painter, rect, w, h, cb, ce, pe):
        pen = QPen(cb); pen.setWidth(3); pen.setStyle(Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(QColor(cb.red(),cb.green(),cb.blue(),40))
        painter.drawEllipse(rect.adjusted(2,2,-2,-2))
        painter.setBrush(cb.lighter(150)); painter.setPen(Qt.NoPen)
        for angle in [0,90,180,270]:
            rad = np.radians(angle)
            x = rect.center().x() + np.cos(rad)*(w/2-6)
            y = rect.center().y() + np.sin(rad)*(h/2-6)
            painter.drawEllipse(int(x)-3, int(y)-3, 6, 6)

    @staticmethod
    def _draw_random(painter, rect, w, h, cb, ce, pe):
        import random; random.seed(42)
        g = QRadialGradient(w/2,h/2,w/2)
        g.setColorAt(0, QColor(cb.red(),cb.green(),cb.blue(),60)); g.setColorAt(1, Qt.transparent)
        painter.setBrush(g); painter.setPen(Qt.NoPen); painter.drawEllipse(rect)
        for _ in range(15):
            rx = random.randint(rect.left()+4, rect.right()-4)
            ry = random.randint(rect.top()+4, rect.bottom()-4)
            sz = random.randint(2,5); op = random.randint(150,255)
            painter.setBrush(QColor(ce.red(),ce.green(),ce.blue(),op))
            painter.drawEllipse(rx,ry,sz,sz)


def load_external_icon(filename: str) -> 'QIcon':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, 'icons', filename)
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return ModernIconFactory.create_icon(os.path.splitext(filename)[0])
