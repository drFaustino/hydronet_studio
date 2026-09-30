# -*- coding: utf-8 -*-
"""Stile automatico: spessore (e colore) delle linee in funzione dell'ordine gerarchico."""
import numpy as np
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsCategorizedSymbolRenderer,
    QgsFeatureRequest,
    QgsGraduatedSymbolRenderer,
    QgsLineSymbol,
    QgsRendererCategory,
    QgsRendererRange,
)

MAX_CATEGORIES = 12
GRADUATED_CLASSES = 7


def tr(text):
    return QCoreApplication.translate("HydroNetStyler", text)


def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return QColor(
        int(round(c1.red() + (c2.red() - c1.red()) * t)),
        int(round(c1.green() + (c2.green() - c1.green()) * t)),
        int(round(c1.blue() + (c2.blue() - c1.blue()) * t)),
    )


def _symbol(color, width):
    return QgsLineSymbol.createSimple({
        "color": color.name(),
        "width": "%.3f" % width,
        "width_unit": "MM",
        "capstyle": "round",
        "joinstyle": "round",
    })


def _set_draw_order(renderer, field):
    """Disegna prima gli ordini bassi, cosi' i corsi principali restano in primo piano."""
    try:
        ob = QgsFeatureRequest.OrderBy([QgsFeatureRequest.OrderByClause(field, True)])
        renderer.setOrderBy(ob)
        renderer.setOrderByEnabled(True)
    except Exception:
        pass


def apply_order_style(layer, field, wmin=0.25, wmax=2.6,
                      color_min=QColor("#9ECAE1"), color_max=QColor("#08306B")):
    """
    Applica al layer lineare uno stile con spessore crescente con il valore di `field`.
    Ritorna una stringa descrittiva dello stile applicato.
    """
    idx = layer.fields().indexFromName(field)
    if idx < 0:
        raise ValueError(tr("Campo '%s' non trovato.") % field)
    values = sorted(v for v in layer.uniqueValues(idx) if v is not None)
    if not values:
        raise ValueError(tr("Il campo '%s' non contiene valori.") % field)
    vmin, vmax = float(values[0]), float(values[-1])
    span = (vmax - vmin) if vmax > vmin else 1.0

    if len(values) <= MAX_CATEGORIES:
        cats = []
        for v in values:
            t = (float(v) - vmin) / span if vmax > vmin else 1.0
            sym = _symbol(_lerp_color(color_min, color_max, t), wmin + (wmax - wmin) * t)
            cats.append(QgsRendererCategory(v, sym, tr("Ordine %s") % v))
        renderer = QgsCategorizedSymbolRenderer(field, cats)
        desc = tr("categorizzato (%d classi)") % len(cats)
    else:
        edges = np.unique(np.round(
            np.geomspace(max(vmin, 1.0), vmax + 1.0, GRADUATED_CLASSES + 1)).astype(int))
        ranges = []
        n = len(edges) - 1
        for i in range(n):
            lo = int(edges[i])
            hi = int(edges[i + 1]) - 1 if i < n - 1 else int(vmax)
            if hi < lo:
                hi = lo
            t = i / max(1, n - 1)
            sym = _symbol(_lerp_color(color_min, color_max, t), wmin + (wmax - wmin) * t)
            label = "%d" % lo if lo == hi else "%d – %d" % (lo, hi)
            ranges.append(QgsRendererRange(lo, hi, sym, label))
        renderer = QgsGraduatedSymbolRenderer(field, ranges)
        desc = tr("graduato (%d classi, scala geometrica)") % len(ranges)

    _set_draw_order(renderer, field)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    return desc
