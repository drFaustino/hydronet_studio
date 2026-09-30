# -*- coding: utf-8 -*-
"""Interfaccia grafica di HydroNet Studio (finestra indipendente, non ancorabile)."""
import math
import os
import re
import tempfile
import time

from qgis.PyQt.QtCore import Qt, QCoreApplication, QTimer
from qgis.PyQt.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen
from qgis.PyQt.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSizePolicy, QSlider,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)
from qgis.core import (
    Qgis, QgsProject, QgsRasterLayer, QgsUnitTypes, QgsVectorLayer,
)
from qgis.gui import QgsColorButton

from . import engine, styler
from .worker import HydroWorker


def tr(text):
    """Marca (e traduce, se disponibile un file .qm caricato) le stringhe dell'interfaccia."""
    return QCoreApplication.translate("HydroNetDialog", text)


def _order_info():
    return [
        ("strahler", tr("Strahler"),
         tr("Metodo gerarchico basato sulla struttura della rete idrografica. "
            "I tratti che partono dalle sorgenti hanno ordine 1. Quando due tratti "
            "dello stesso ordine k confluiscono, il tratto risultante assume ordine k+1. "
            "Quando invece confluiscono tratti di ordine diverso, il tratto a valle "
            "mantiene l'ordine maggiore. In questo modo l'ordine aumenta solo quando "
            "si incontrano due rami di pari importanza gerarchica.")),

        ("shreve", tr("Shreve (magnitudo)"),
         tr("Metodo basato sulla magnitudo del bacino drenato dal singolo tratto. "
            "Ogni tratto che nasce da una sorgente ha magnitudo 1. In corrispondenza "
            "di una confluenza, la magnitudo del tratto a valle è data dalla somma "
            "delle magnitudo dei due tratti confluenti. Il valore ottenuto rappresenta "
            "quindi, in termini topologici, il numero complessivo di sorgenti che "
            "contribuiscono al deflusso del tratto considerato.")),

        ("horton", tr("Horton"),
         tr("Metodo gerarchico derivato dalla classificazione di Strahler, con "
            "particolare attenzione all'individuazione dell'asta principale. "
            "L'asta principale conserva il valore dell'ordine più elevato raggiunto "
            "lungo la rete fino alla sorgente, mentre i rami secondari vengono "
            "classificati in funzione della loro posizione gerarchica rispetto "
            "all'asta principale. È utile per descrivere la struttura gerarchica "
            "del reticolo distinguendo il corso principale dagli affluenti.")),

        ("gravelius", tr("Gravelius / Hack (asta principale)"),
         tr("Classificazione gerarchica basata sull'individuazione dell'asta "
            "principale, generalmente determinata seguendo il percorso associato "
            "alla maggiore area drenata. L'asta principale viene assegnata al livello "
            "1; gli affluenti che confluiscono direttamente nell'asta principale "
            "sono di livello 2; i corsi che alimentano questi affluenti sono di "
            "livello 3, e così via. Il valore aumenta quindi allontanandosi "
            "gerarchicamente dall'asta principale verso i rami più secondari.")),

        ("topologico", tr("Topologico (distanza dalla foce)"),
         tr("Ordine determinato esclusivamente dalla posizione topologica del tratto "
            "all'interno della rete rispetto allo sbocco finale. Il segmento che "
            "raggiunge direttamente la foce ha valore 1; procedendo verso monte, "
            "il valore aumenta di uno per ogni tratto che separa il segmento dalla "
            "foce. Il metodo non considera la dimensione del bacino, la portata "
            "o l'importanza idrologica del ramo, ma esclusivamente il numero di "
            "collegamenti necessari per raggiungere lo sbocco.")),
    ]


def _smooth_items():
    return [
        ("natural", tr("Naturale - gaussiana + spline (consigliato)")),
        ("gauss", tr("Media mobile gaussiana")),
        ("chaikin", tr("Chaikin (taglio degli angoli)")),
        ("spline", tr("Spline Catmull-Rom")),
        ("none", tr("Nessuna (percorso D8 grezzo)")),
    ]

STYLESHEET = """
QDialog { background:#F3F6FA; }
QWidget#sidebar { background:#0E2740; }
QLabel#brand { color:#FFFFFF; font-size:17px; font-weight:700; padding:18px 18px 2px 18px; }
QLabel#brandsub { color:#8FB4D9; font-size:11px; padding:0px 18px 14px 18px; }
QListWidget#nav { background:#0E2740; border:none; color:#C7D7E8; font-size:13px; outline:0; }
QListWidget#nav::item { padding:11px 14px; margin:2px 10px; border-radius:8px; }
QListWidget#nav::item:hover:!selected { background:#173A5C; }
QListWidget#nav::item:selected { background:#1E88E5; color:#FFFFFF; }
QLabel#pagetitle { color:#0E2740; font-size:20px; font-weight:700; }
QLabel#pagesub { color:#5C6E82; font-size:12px; }
QLabel#hint { color:#6B7A8C; font-size:11px; }
QLabel#info { color:#0E2740; background:#E8F1FB; border-radius:8px; padding:9px 12px; }
QLabel { color:#1F2D3D; }
QGroupBox { background:#FFFFFF; border:1px solid #DCE3EB; border-radius:10px;
            margin-top:16px; padding:16px 14px 12px 14px; font-weight:600; color:#0E2740; }
QGroupBox::title { subcontrol-origin:margin; left:14px; padding:0 6px; }
QCheckBox { color:#1F2D3D; spacing:8px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background:#FFFFFF; color:#1F2D3D; border:1px solid #C6D1DD; border-radius:6px;
    padding:5px 8px; min-height:22px; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border:1px solid #1E88E5; }
QComboBox QAbstractItemView { background:#FFFFFF; color:#1F2D3D; selection-background-color:#1E88E5; }
QPushButton { background:#FFFFFF; color:#0E2740; border:1px solid #C6D1DD; border-radius:8px;
              padding:8px 18px; }
QPushButton:hover { background:#EAF2FB; }
QPushButton:disabled { color:#9AA8B8; background:#F0F3F7; }
QPushButton#primary { background:#1E88E5; color:#FFFFFF; border:none; font-weight:700; padding:9px 26px; }
QPushButton#primary:hover { background:#1976D2; }
QPushButton#primary:disabled { background:#9CC6F0; color:#FFFFFF; }
QPushButton#danger { background:#FFFFFF; color:#C62828; border:1px solid #E0A5A5; }
QPushButton#danger:hover { background:#FDECEC; }
QProgressBar { border:none; border-radius:7px; background:#D9E2EC; text-align:center;
               color:#0E2740; min-height:16px; max-height:16px; font-weight:600; }
QProgressBar::chunk { border-radius:7px; background:#1E88E5; }
QPlainTextEdit#log { background:#0E1B2A; color:#B8F0D2; border-radius:8px; padding:6px;
                     font-family:Consolas,'DejaVu Sans Mono',monospace; font-size:11px; }
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin:border; subcontrol-position:top right;
    width:18px; border-left:1px solid #C6D1DD; background:#EEF3F8;
    border-top-right-radius:5px;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin:border; subcontrol-position:bottom right;
    width:18px; border-left:1px solid #C6D1DD; background:#EEF3F8;
    border-bottom-right-radius:5px;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background:#DCEAF7; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
    image:url(%ARROW_UP%);
    width:9px; height:9px;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
    image:url(%ARROW_DOWN%);
    width:9px; height:9px;
}
QSlider::groove:horizontal { height:6px; background:#D9E2EC; border-radius:3px; }
QSlider::handle:horizontal { background:#1E88E5; width:16px; margin:-5px 0; border-radius:8px; }
QSlider::sub-page:horizontal { background:#1E88E5; border-radius:3px; }
"""


def _label(text, name=None, wrap=True):
    lb = QLabel(text)
    if name:
        lb.setObjectName(name)
    lb.setWordWrap(wrap)
    return lb


class SmoothPreview(QWidget):
    """Anteprima: percorso D8 grezzo (grigio) e linea smussata (blu)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._raw = engine.demo_staircase()
        self.method, self.strength, self.density = "natural", 2.0, 3

    def set_params(self, method, strength, density):
        self.method, self.strength, self.density = method, strength, density
        self.update()

    def _path(self, pts, rect):
        path = QPainterPath()
        m = 14
        w, h = rect.width() - 2 * m, rect.height() - 2 * m
        for i, (x, y) in enumerate(pts):
            px, py = m + x * w, m + (1.0 - y) * h
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        return path

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setPen(QPen(QColor("#DCE3EB"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(r.adjusted(0, 0, -1, -1), 10, 10)
        p.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor("#B0BAC6"), 1.4)
        p.setPen(pen)
        p.drawPath(self._path(self._raw, r))
        sm = engine.smooth_line(self._raw, self.method, self.strength, self.density)
        pen = QPen(QColor("#1565C0"), 3.0)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.drawPath(self._path(sm, r))
        p.end()


class StylePreview(QWidget):
    """Anteprima degli spessori assegnati dal minimo al massimo ordine."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.wmin, self.wmax = 0.25, 2.6
        self.c1, self.c2 = QColor("#9ECAE1"), QColor("#08306B")

    def set_params(self, wmin, wmax, c1, c2):
        self.wmin, self.wmax, self.c1, self.c2 = wmin, wmax, c1, c2
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setPen(QPen(QColor("#DCE3EB"), 1))
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(r.adjusted(0, 0, -1, -1), 10, 10)
        n = 5
        step = (r.height() - 24) / n
        for i in range(n):
            t = i / (n - 1)
            col = styler._lerp_color(self.c1, self.c2, t)
            w = (self.wmin + (self.wmax - self.wmin) * t) * 3.78
            pen = QPen(col, max(1.0, w))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            y = 18 + step * i + step / 2 - 6
            p.drawLine(int(r.left() + 40), int(y), int(r.right() - 40), int(y))
        p.end()


class HydroNetDialog(QDialog):
    def __init__(self, iface, icon_path=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.worker = None
        self._success = False
        self._path_edited = False
        self.setWindowTitle(tr("HydroNet Studio - Reticolo idrografico da DTM/DEM"))
        if icon_path and os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMinMaxButtonsHint)
        self.setSizeGripEnabled(True)
        self.setMinimumSize(900, 500)
        self.resize(950, 600)
        self.setStyleSheet(
            STYLESHEET.replace("%ARROW_UP%", os.path.join(os.path.dirname(__file__), "arrow-up.svg").replace("\\", "/"))
                      .replace("%ARROW_DOWN%", os.path.join(os.path.dirname(__file__), "arrow-down.svg").replace("\\", "/"))
        )
        self._build_ui()
        self._connect()
        self._refresh_layers()
        self._update_smooth_preview()
        self._update_style_preview()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # sidebar
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(210)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 0, 0, 12)
        sl.setSpacing(0)
        sl.addWidget(_label(tr("HydroNet Studio"), "brand", False))
        sl.addWidget(_label(tr("Reticolo idrografico da DTM"), "brandsub", False))
        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFrameShape(QFrame.Shape.NoFrame)
        self.nav.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        for t in ("1   " + tr("Input"), "2   " + tr("Idrologia"), "3   " + tr("Smussatura"),
                  "4   " + tr("Ordinamento"), "5   " + tr("Stile"), "6   " + tr("Output")):
            self.nav.addItem(t)
        sl.addWidget(self.nav, 1)
        root.addWidget(side)

        # contenuto
        right = QVBoxLayout()
        right.setContentsMargins(22, 18, 22, 16)
        right.setSpacing(10)
        self.stack = QStackedWidget()
        for builder in (self._page_input, self._page_hydro, self._page_smooth,
                        self._page_order, self._page_style, self._page_output):
            self.stack.addWidget(builder())
        right.addWidget(self.stack, 1)

        self.log = QPlainTextEdit()
        self.log.setObjectName("log")
        self.log.setReadOnly(True)
        self.log.setFixedHeight(110)
        right.addWidget(self.log)

        bar = QHBoxLayout()
        bar.setSpacing(10)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        bar.addWidget(self.progress, 1)
        self.btn_run = QPushButton(tr("Avvia elaborazione"))
        self.btn_run.setObjectName("primary")
        self.btn_cancel = QPushButton(tr("Annulla"))
        self.btn_cancel.setObjectName("danger")
        self.btn_cancel.setEnabled(False)
        self.btn_close = QPushButton(tr("Chiudi"))
        bar.addWidget(self.btn_run)
        bar.addWidget(self.btn_cancel)
        bar.addWidget(self.btn_close)
        right.addLayout(bar)
        root.addLayout(right, 1)
        self.nav.setCurrentRow(0)

    def _page(self, title, sub):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        lay.addWidget(_label(title, "pagetitle", False))
        lay.addWidget(_label(sub, "pagesub"))
        return w, lay

    # 1 - input
    def _page_input(self):
        w, lay = self._page(
            tr("Dati di input"),
            tr("Seleziona il modello digitale del terreno (DTM/DEM) caricato nel progetto.")
        )

        g = QGroupBox(tr("Modello digitale del terreno"))
        f = QFormLayout(g)
        f.setSpacing(10)

        self.cmb_raster = QComboBox()
        self.cmb_band = QComboBox()

        f.addRow(tr("Raster DTM/DEM:"), self.cmb_raster)
        f.addRow(tr("Banda:"), self.cmb_band)

        self.chk_nodata = QCheckBox(
            tr("Considera anche questo valore come NoData:")
        )

        self.spn_nodata = QDoubleSpinBox()
        self.spn_nodata.setRange(-1e12, 1e12)
        self.spn_nodata.setDecimals(3)
        self.spn_nodata.setValue(-9999.0)
        self.spn_nodata.setEnabled(False)

        row = QHBoxLayout()
        row.addWidget(self.chk_nodata)
        row.addWidget(self.spn_nodata)
        f.addRow(row)

        lay.addWidget(g)

        self.lbl_info = _label(
            tr("Nessun raster selezionato."),
            "info"
        )
        lay.addWidget(self.lbl_info)

        lay.addWidget(_label(
            tr(
                "Buona pratica: usa preferibilmente un DTM/DEM in un sistema di "
                "riferimento proiettato con unità metriche (metri). I raster geografici "
                "espressi in gradi sono supportati tramite una conversione approssimata "
                "delle distanze, ma un CRS metrico è consigliato per le analisi "
                "idrologiche quantitative."
            ),
            "hint"
        ))

        lay.addWidget(_label(
            tr(
                "Verifica che il DTM abbia una risoluzione adeguata alla scala "
                "dell'analisi e che il valore NoData sia correttamente identificato. "
                "Depressioni, artefatti, ponti, strade e discontinuità del modello "
                "del terreno possono influenzare le direzioni di deflusso e "
                "l'accumulo. Il modello applica un riempimento delle depressioni "
                "prima del calcolo del routing."
            ),
            "hint"
        ))

        lay.addStretch(1)
        return w

    # 2 - idrologia
    def _page_hydro(self):
        w, lay = self._page(tr("Idrologia ed estrazione"),
                            tr("Il DEM viene prima trattato con Priority-Flood per garantire un drenaggio coerente; quindi viene applicato il modello di deflusso selezionato."))
        g0 = QGroupBox(tr("Modello di direzione del deflusso"))
        f0 = QFormLayout(g0)
        f0.setSpacing(10)
        self.cmb_flow_method = QComboBox()
        flow_items = [
            ("d8", tr("D8 - massima pendenza (8 direzioni)")),
            ("dinf", tr("D∞ - Tarboton (direzione continua + 1–2 ricevitori)")),
            ("rho8", tr("Rho8 - Fairfield & Leymarie (stocastico)")),
            ("mfd", tr("MFD classico - Quinn et al. (p=1, lunghezza di contorno)")),
            ("mdinf", tr("MD∞ - Seibert & McGlynn (triangolare multiplo)")),
            ("demon", tr("DEMON - Costa-Cabral & Burges (stream tube)")),
        ]
        for key, label in flow_items:
            self.cmb_flow_method.addItem(label, key)
        self.cmb_flow_method.setCurrentIndex(1)
        self.spn_flow_seed = QSpinBox()
        self.spn_flow_seed.setRange(0, 2147483647)
        self.spn_flow_seed.setValue(42)
        f0.addRow(tr("Algoritmo:"), self.cmb_flow_method)
        f0.addRow(tr("Seed casuale (Rho8):"), self.spn_flow_seed)
        lay.addWidget(g0)
        self.lbl_flow_info = _label("", "hint")
        self.lbl_flow_info.setWordWrap(True)
        lay.addWidget(self.lbl_flow_info)
        self.cmb_flow_method.currentIndexChanged.connect(self._update_flow_description)
        self._update_flow_description()
        g = QGroupBox(tr("Soglia di innesco dei canali"))
        f = QFormLayout(g)
        f.setSpacing(10)
        self.cmb_thr_mode = QComboBox()
        threshold_items = [
            ("area", tr("Area drenata minima (km²)")),
            ("slope_area", tr("Relazione pendenza–area (Montgomery–Dietrich)")),
            ("spi", tr("SPI - Stream Power Index")),
            ("twi", tr("TWI - Topographic Wetness Index")),
        ]
        for key, label in threshold_items:
            self.cmb_thr_mode.addItem(label, key)
        self.spn_thr = QDoubleSpinBox()
        self.spn_thr.setDecimals(6)
        self.spn_thr.setRange(0.000001, 1e9)
        self.spn_thr.setValue(0.05)
        f.addRow(tr("Criterio:"), self.cmb_thr_mode)
        f.addRow(tr("Soglia principale:"), self.spn_thr)
        self.spn_thr_n = QDoubleSpinBox(); self.spn_thr_n.setRange(0.01, 5.0); self.spn_thr_n.setDecimals(2); self.spn_thr_n.setValue(1.0)
        self.spn_thr_m = QDoubleSpinBox(); self.spn_thr_m.setRange(0.01, 6.0); self.spn_thr_m.setDecimals(2); self.spn_thr_m.setValue(2.0)
        self.spn_thr_p = QDoubleSpinBox(); self.spn_thr_p.setRange(0.1, 5.0); self.spn_thr_p.setDecimals(2); self.spn_thr_p.setValue(1.1)
        self.lbl_thr_n = _label(tr("Esponente n della relazione area–pendenza"), "hint")
        self.lbl_thr_m = _label(tr("Esponente m della relazione area–pendenza"), "hint")
        self.lbl_thr_extra = _label("", "hint")
        f.addRow(tr("Esponente n:"), self.spn_thr_n)
        f.addRow(tr("Esponente m:"), self.spn_thr_m)
        self.lbl_thr = _label("", "hint")
        f.addRow(self.lbl_thr)
        lay.addWidget(g)
        self.lbl_thr_desc = _label("", "hint")
        self.lbl_thr_desc.setWordWrap(True)
        lay.addWidget(self.lbl_thr_desc)
        self.cmb_thr_mode.currentIndexChanged.connect(self._update_threshold_description)
        self.spn_thr.valueChanged.connect(self._update_thr_hint)
        self.spn_thr_n.valueChanged.connect(self._update_thr_hint)
        self.spn_thr_m.valueChanged.connect(self._update_thr_hint)
        self._update_threshold_description()
        lay.addWidget(_label(
            tr("Per l'area drenata la soglia è espressa in km². Gli altri criteri sono indici adimensionali o con unità proprie e vengono applicati direttamente al raster derivato; la descrizione mostra esattamente il significato della soglia."), "hint"))
        lay.addStretch(1)
        return w

    # 3 - smussatura
    def _page_smooth(self):
        w, lay = self._page(
            tr("Smussatura del reticolo"),
            tr(
                "Riduce l'effetto a gradini tipico delle geometrie raster e rende "
                "le aste del reticolo più fluide. La smussatura viene applicata "
                "alla geometria delle polilinee dopo l'estrazione del reticolo e "
                "non modifica il DTM, le direzioni di deflusso o il calcolo "
                "dell'accumulo."
            )
        )

        g = QGroupBox(tr("Parametri"))
        f = QFormLayout(g)
        f.setSpacing(10)

        self.cmb_smooth = QComboBox()
        for k, t in _smooth_items():
            self.cmb_smooth.addItem(t, k)

        f.addRow(
            tr("Metodo:"),
            self.cmb_smooth
        )

        self.sld_strength = QSlider(Qt.Orientation.Horizontal)
        self.sld_strength.setRange(0, 100)
        self.sld_strength.setValue(20)

        self.spn_strength = QDoubleSpinBox()
        self.spn_strength.setRange(0.0, 10.0)
        self.spn_strength.setSingleStep(0.5)
        self.spn_strength.setDecimals(1)
        self.spn_strength.setValue(2.0)

        r = QHBoxLayout()
        r.addWidget(self.sld_strength, 1)
        r.addWidget(self.spn_strength)

        f.addRow(
            tr("Intensità:"),
            r
        )

        self.spn_density = QSpinBox()
        self.spn_density.setRange(1, 12)
        self.spn_density.setValue(3)

        f.addRow(
            tr("Densità spline (punti/tratto):"),
            self.spn_density
        )

        f.addRow(
            _label(
                tr(
                    "L'intensità controlla la forza della smussatura. Per il metodo "
                    "Gaussiano corrisponde al valore sigma, espresso in vertici; "
                    "per Chaikin corrisponde al numero di iterazioni. La densità "
                    "della spline controlla invece il numero di suddivisioni "
                    "utilizzate tra i vertici della curva."
                ),
                "hint"
            )
        )

        lay.addWidget(g)

        lay.addWidget(
            _label(
                tr(
                    "I punti iniziale e finale di ciascun tratto vengono mantenuti "
                    "come estremi della geometria. La smussatura modifica invece "
                    "la forma del percorso tra gli estremi."
                ),
                "hint"
            )
        )

        lay.addWidget(
            _label(
                tr(
                    "Una smussatura più intensa produce linee più morbide ma può "
                    "allontanare maggiormente la geometria dalla traccia raster "
                    "originale. Per una rappresentazione cartografica naturale "
                    "sono generalmente preferibili valori moderati."
                ),
                "hint"
            )
        )

        lay.addWidget(
            _label(
                tr(
                    "Metodi disponibili: Gaussiana per attenuare i cambi bruschi "
                    "di direzione; Chaikin per arrotondare progressivamente i "
                    "vertici; Catmull-Rom per ottenere una curva interpolata; "
                    "Naturale per combinare attenuazione Gaussiana e spline."
                ),
                "hint"
            )
        )

        lay.addWidget(
            _label(
                tr(
                    "Anteprima: grigio = geometria originale del reticolo; "
                    "blu = geometria dopo la smussatura."
                ),
                "hint"
            )
        )

        self.smooth_preview = SmoothPreview()
        lay.addWidget(self.smooth_preview)

        lay.addStretch(1)
        return w

    # 4 - ordinamento
    def _page_order(self):
        w, lay = self._page(tr("Ordinamento gerarchico"),
                            tr("Scegli uno o piu' metodi: ognuno genera un campo dedicato nella tabella."))
        g = QGroupBox(tr("Metodi di ordinamento"))
        gl = QVBoxLayout(g)
        gl.setSpacing(8)
        self.order_checks = {}
        for key, name, desc in _order_info():
            cb = QCheckBox(name)
            cb.setChecked(key in ("strahler", "shreve"))
            self.order_checks[key] = cb
            gl.addWidget(cb)
            hint = _label(desc, "hint")
            hint.setContentsMargins(26, 0, 0, 4)
            gl.addWidget(hint)
        lay.addWidget(g)
        lay.addStretch(1)
        return w

    # 5 - stile
    def _page_style(self):
        w, lay = self._page(tr("Stile automatico"),
                            tr("Spessore (e colore) delle linee proporzionali all'ordine gerarchico."))
        g = QGroupBox(tr("Stile del nuovo reticolo"))
        f = QFormLayout(g)
        f.setSpacing(10)
        self.chk_style = QCheckBox(tr("Applica automaticamente lo stile al risultato"))
        self.chk_style.setChecked(True)
        f.addRow(self.chk_style)
        self.cmb_style_field = QComboBox()
        f.addRow(tr("Ordinamento da usare:"), self.cmb_style_field)
        self.spn_wmin = QDoubleSpinBox()
        self.spn_wmin.setRange(0.05, 5.0)
        self.spn_wmin.setSingleStep(0.05)
        self.spn_wmin.setSuffix(" mm")
        self.spn_wmin.setValue(0.25)
        self.spn_wmax = QDoubleSpinBox()
        self.spn_wmax.setRange(0.1, 12.0)
        self.spn_wmax.setSingleStep(0.1)
        self.spn_wmax.setSuffix(" mm")
        self.spn_wmax.setValue(2.6)
        f.addRow(tr("Spessore ordine minimo:"), self.spn_wmin)
        f.addRow(tr("Spessore ordine massimo:"), self.spn_wmax)
        self.col_min = QgsColorButton()
        self.col_min.setColor(QColor("#9ECAE1"))
        self.col_max = QgsColorButton()
        self.col_max.setColor(QColor("#08306B"))
        f.addRow(tr("Colore ordine minimo:"), self.col_min)
        f.addRow(tr("Colore ordine massimo:"), self.col_max)
        lay.addWidget(g)
        self.style_preview = StylePreview()
        lay.addWidget(self.style_preview)

        g2 = QGroupBox(tr("Applica lo stile a un layer lineare esistente"))
        f2 = QFormLayout(g2)
        f2.setSpacing(10)
        self.cmb_exist_layer = QComboBox()
        self.cmb_exist_field = QComboBox()
        self.btn_apply_exist = QPushButton(tr("Applica stile"))
        f2.addRow(tr("Layer:"), self.cmb_exist_layer)
        f2.addRow(tr("Campo ordine (numerico):"), self.cmb_exist_field)
        f2.addRow(self.btn_apply_exist)
        lay.addWidget(g2)
        lay.addStretch(1)
        return w

    # 6 - output
    def _page_output(self):
        w, lay = self._page(
            tr("Output"),
            tr(
                "Configura il GeoPackage di uscita e, se necessario, salva "
                "anche i raster utilizzati durante l'analisi."
            )
        )

        # ------------------------------------------------------------------
        # File di uscita
        # ------------------------------------------------------------------
        g = QGroupBox(tr("File di uscita"))
        f = QFormLayout(g)
        f.setSpacing(10)

        self.edt_out = QLineEdit()
        btn = QPushButton(tr("Sfoglia…"))
        self.btn_browse = btn

        r = QHBoxLayout()
        r.addWidget(self.edt_out, 1)
        r.addWidget(btn)

        f.addRow(tr("GeoPackage:"), r)

        self.edt_name = QLineEdit(tr("Reticolo idrografico"))
        f.addRow(tr("Nome del layer:"), self.edt_name)

        lay.addWidget(g)

        # ------------------------------------------------------------------
        # Prodotti aggiuntivi
        # ------------------------------------------------------------------
        g2 = QGroupBox(tr("Prodotti aggiuntivi"))
        gl = QVBoxLayout(g2)
        gl.setSpacing(6)

        self.chk_filled = QCheckBox(
            tr("Salva il DEM depresso riempito (GeoTIFF)")
        )

        self.chk_acc = QCheckBox(
            tr("Salva il raster di flow accumulation (GeoTIFF)")
        )

        self.chk_load = QCheckBox(
            tr("Carica nel progetto anche i raster salvati")
        )
        self.chk_load.setChecked(True)

        for c in (self.chk_filled, self.chk_acc, self.chk_load):
            gl.addWidget(c)

        gl.addWidget(_label(
            tr(
                "Il DEM riempito è la superficie corretta utilizzata per "
                "garantire la continuità del drenaggio attraverso le depressioni. "
                "Il raster di flow accumulation rappresenta invece la quantità "
                "di deflusso accumulata a monte di ciascuna cella."
            ),
            "hint"
        ))

        lay.addWidget(g2)

        # ------------------------------------------------------------------
        # Contenuto del reticolo
        # ------------------------------------------------------------------
        g3 = QGroupBox(tr("Contenuto del reticolo"))
        g3l = QVBoxLayout(g3)
        g3l.setSpacing(6)

        g3l.addWidget(_label(
            tr(
                "Il GeoPackage contiene un segmento per ciascuna asta del "
                "reticolo, collegata topologicamente al segmento a valle. "
                "La geometria viene ricavata dal percorso di drenaggio raster "
                "e può essere successivamente smussata senza spostare i nodi "
                "di connessione."
            ),
            "info"
        ))

        g3l.addWidget(_label(
            tr(
                "Per ogni segmento vengono salvati, quando disponibili, "
                "identificativo, segmento a valle, numero di aste confluenti, "
                "lunghezza, area drenata, quota a monte, quota a valle, "
                "pendenza media e algoritmo di routing utilizzato."
            ),
            "hint"
        ))

        g3l.addWidget(_label(
            tr(
                "Gli ordinamenti gerarchici selezionati vengono aggiunti "
                "come campi distinti: Strahler, Shreve, Horton, "
                "Gravelius/Hack e Topologico."
            ),
            "hint"
        ))

        lay.addWidget(g3)

        # ------------------------------------------------------------------
        # Nota sui dati di accumulo
        # ------------------------------------------------------------------
        lay.addWidget(_label(
            tr(
                "Nota: l'area drenata è espressa in km² e deriva dalla "
                "flow accumulation moltiplicata per l'area della cella. "
                "Nei metodi a flusso frazionato (D∞, MD∞, MFD e DEMON) "
                "l'accumulo può assumere valori decimali perché il flusso "
                "di una cella può essere distribuito tra più direzioni."
            ),
            "hint"
        ))

        lay.addStretch(1)
        return w

    # ------------------------------------------------------------- segnali

    def _connect(self):
        """Collega tutti i segnali dell'interfaccia ai relativi handler."""

        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

        self.cmb_raster.currentIndexChanged.connect(
            self._on_raster_changed
        )

        self.chk_nodata.toggled.connect(
            self.spn_nodata.setEnabled
        )

        # Smussatura
        self.cmb_smooth.currentIndexChanged.connect(
            self._update_smooth_preview
        )

        self.sld_strength.valueChanged.connect(
            self._on_slider
        )

        self.spn_strength.valueChanged.connect(
            self._on_spin_strength
        )

        self.spn_density.valueChanged.connect(
            self._update_smooth_preview
        )

        # Ordinamenti
        for cb in self.order_checks.values():
            cb.toggled.connect(
                self._refresh_style_fields
            )

        # Stile
        for wdg in (self.spn_wmin, self.spn_wmax):
            wdg.valueChanged.connect(
                self._update_style_preview
            )

        for wdg in (self.col_min, self.col_max):
            wdg.colorChanged.connect(
                self._update_style_preview
            )

        # Layer esistente
        self.cmb_exist_layer.currentIndexChanged.connect(
            self._refresh_exist_fields
        )

        self.btn_apply_exist.clicked.connect(
            self._apply_existing_style
        )

        # Output
        self.edt_out.textEdited.connect(
            lambda _text: setattr(self, "_path_edited", True)
        )

        self.btn_browse.clicked.connect(
            self._browse
        )

        # Elaborazione
        self.btn_run.clicked.connect(
            self._start
        )

        self.btn_cancel.clicked.connect(
            self._cancel
        )

        self.btn_close.clicked.connect(
            self.close
        )

        # Aggiornamento automatico dei layer QGIS
        prj = QgsProject.instance()

        prj.layersAdded.connect(
            self._refresh_layers
        )

        prj.layersRemoved.connect(
            self._refresh_layers
        )

        # Stato iniziale
        self._refresh_style_fields()
        self._update_style_preview()


    # --------------------------------------------------------- smussatura

    def _update_smooth_preview(self, *_args):
        """Aggiorna l'anteprima della smussatura."""

        if not hasattr(self, "smooth_preview"):
            return

        method = self.cmb_smooth.currentData()

        if not method:
            method = "natural"

        strength = self.spn_strength.value()
        density = self.spn_density.value()

        self.smooth_preview.set_params(
            method,
            strength,
            density,
        )


    def _on_slider(self, value):
        """
        Sincronizza lo slider con il valore numerico della forza.

        Slider:
            0 ... 100

        SpinBox:
            0.0 ... 10.0
        """

        strength = float(value) / 10.0

        self.spn_strength.blockSignals(True)

        try:
            self.spn_strength.setValue(strength)
        finally:
            self.spn_strength.blockSignals(False)

        self._update_smooth_preview()


    def _on_spin_strength(self, value):
        """Sincronizza il campo numerico con lo slider."""

        slider_value = int(round(float(value) * 10.0))

        slider_value = max(
            self.sld_strength.minimum(),
            min(self.sld_strength.maximum(), slider_value),
        )

        self.sld_strength.blockSignals(True)

        try:
            self.sld_strength.setValue(slider_value)
        finally:
            self.sld_strength.blockSignals(False)

        self._update_smooth_preview()


    # -------------------------------------------------------------- stile

    def _refresh_style_fields(self, *_args):
        """
        Aggiorna l'elenco dei campi di ordinamento disponibili
        per lo stile automatico.
        """

        if not hasattr(self, "cmb_style_field"):
            return

        previous = self.cmb_style_field.currentData()

        self.cmb_style_field.blockSignals(True)

        try:
            self.cmb_style_field.clear()

            labels = {
                key: name
                for key, name, _desc in _order_info()
            }

            for key, cb in self.order_checks.items():
                if cb.isChecked():
                    self.cmb_style_field.addItem(
                        labels.get(key, key),
                        key,
                    )

            # Mantieni la selezione precedente se ancora disponibile.
            idx = self.cmb_style_field.findData(previous)

            if idx >= 0:
                self.cmb_style_field.setCurrentIndex(idx)
            elif self.cmb_style_field.count() > 0:
                self.cmb_style_field.setCurrentIndex(0)

        finally:
            self.cmb_style_field.blockSignals(False)

        enabled = self.cmb_style_field.count() > 0

        self.cmb_style_field.setEnabled(enabled)
        self.spn_wmin.setEnabled(enabled)
        self.spn_wmax.setEnabled(enabled)
        self.col_min.setEnabled(enabled)
        self.col_max.setEnabled(enabled)

        self._update_style_preview()


    def _update_style_preview(self, *_args):
        """Aggiorna l'anteprima grafica dello stile."""

        if not hasattr(self, "style_preview"):
            return

        wmin = float(self.spn_wmin.value())
        wmax = float(self.spn_wmax.value())

        # Evita una scala invertita.
        if wmax < wmin:
            wmax = wmin

        c1 = self.col_min.color()
        c2 = self.col_max.color()

        self.style_preview.set_params(
            wmin,
            wmax,
            c1,
            c2,
        )


    # ------------------------------------------------------ layer esistente

    def _refresh_exist_fields(self, *_args):
        """
        Aggiorna l'elenco dei campi numerici del layer lineare esistente.
        """

        if not hasattr(self, "cmb_exist_layer"):
            return

        previous = self.cmb_exist_field.currentData()

        self.cmb_exist_field.blockSignals(True)

        try:
            self.cmb_exist_field.clear()

            layer_id = self.cmb_exist_layer.currentData()

            if not layer_id:
                self.cmb_exist_field.setEnabled(False)
                self.btn_apply_exist.setEnabled(False)
                return

            layer = QgsProject.instance().mapLayer(layer_id)

            if not isinstance(layer, QgsVectorLayer):
                self.cmb_exist_field.setEnabled(False)
                self.btn_apply_exist.setEnabled(False)
                return

            if not layer.isValid():
                self.cmb_exist_field.setEnabled(False)
                self.btn_apply_exist.setEnabled(False)
                return

            if layer.geometryType() != Qgis.GeometryType.Line:
                self.cmb_exist_field.setEnabled(False)
                self.btn_apply_exist.setEnabled(False)
                return

            for field in layer.fields():
                try:
                    numeric = field.isNumeric()
                except Exception:
                    numeric = False

                if numeric:
                    self.cmb_exist_field.addItem(
                        field.name(),
                        field.name(),
                    )

            idx = self.cmb_exist_field.findData(previous)

            if idx >= 0:
                self.cmb_exist_field.setCurrentIndex(idx)
            elif self.cmb_exist_field.count() > 0:
                self.cmb_exist_field.setCurrentIndex(0)

        finally:
            self.cmb_exist_field.blockSignals(False)

        enabled = self.cmb_exist_field.count() > 0

        self.cmb_exist_field.setEnabled(enabled)
        self.btn_apply_exist.setEnabled(enabled)


    def _apply_existing_style(self):
        """Applica lo stile automatico al layer lineare selezionato."""

        layer_id = self.cmb_exist_layer.currentData()

        if not layer_id:
            QMessageBox.warning(
                self,
                tr("HydroNet Studio"),
                tr("Seleziona un layer lineare."),
            )
            return

        layer = QgsProject.instance().mapLayer(layer_id)

        if not isinstance(layer, QgsVectorLayer) or not layer.isValid():
            QMessageBox.warning(
                self,
                tr("HydroNet Studio"),
                tr("Il layer selezionato non è valido."),
            )
            return

        if layer.geometryType() != Qgis.GeometryType.Line:
            QMessageBox.warning(
                self,
                tr("HydroNet Studio"),
                tr("Il layer selezionato deve essere lineare."),
            )
            return

        field = self.cmb_exist_field.currentData()

        if not field:
            QMessageBox.warning(
                self,
                tr("HydroNet Studio"),
                tr("Seleziona un campo numerico di ordinamento."),
            )
            return

        wmin = float(self.spn_wmin.value())
        wmax = float(self.spn_wmax.value())

        if wmax < wmin:
            QMessageBox.warning(
                self,
                tr("HydroNet Studio"),
                tr(
                    "Lo spessore massimo deve essere maggiore "
                    "o uguale allo spessore minimo."
                ),
            )
            return

        try:
            desc = styler.apply_order_style(
                layer,
                field,
                wmin,
                wmax,
                self.col_min.color(),
                self.col_max.color(),
            )

            try:
                layer.saveDefaultStyle()
            except Exception as exc:
                self._log(tr("Avviso: impossibile salvare lo stile predefinito: %s") % exc)

            layer.triggerRepaint()

            self._log(
                tr(
                    "Stile applicato al layer '%s' "
                    "sul campo '%s': %s"
                )
                % (
                    layer.name(),
                    field,
                    desc,
                )
            )

            QMessageBox.information(
                self,
                tr("HydroNet Studio"),
                tr(
                    "Stile applicato correttamente al layer '%s'."
                )
                % layer.name(),
            )

        except Exception as exc:
            self._log(
                tr("Errore nell'applicazione dello stile: %s")
                % exc
            )

            QMessageBox.critical(
                self,
                tr("HydroNet Studio"),
                tr(
                    "Impossibile applicare lo stile:\n%s"
                )
                % exc,
            )


    # ------------------------------------------------------------- output

    def _browse(self):
        """Seleziona il file GeoPackage di output."""

        current = self.edt_out.text().strip()

        if current:
            start_dir = os.path.dirname(current)

            if not os.path.isdir(start_dir):
                start_dir = ""

            start_path = current if start_dir else ""
        else:
            start_path = ""

        path, _filter = QFileDialog.getSaveFileName(
            self,
            tr("Seleziona GeoPackage di output"),
            start_path,
            tr("GeoPackage (*.gpkg);;Tutti i file (*.*)"),
        )

        if not path:
            return

        if not path.lower().endswith(".gpkg"):
            path += ".gpkg"

        self.edt_out.setText(path)
        self._path_edited = True


    # --------------------------------------------------------------- log

    def _log(self, text):
        """Scrive un messaggio nel pannello di log."""

        if not hasattr(self, "log"):
            return

        self.log.appendPlainText(str(text))

        scrollbar = self.log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


    # ------------------------------------------------------------ cleanup

    def cleanup(self):
        """Disconnette i segnali collegati al progetto QGIS."""

        prj = QgsProject.instance()

        for signal in (
            prj.layersAdded,
            prj.layersRemoved,
        ):
            try:
                signal.disconnect(self._refresh_layers)
            except (TypeError, RuntimeError) as exc:
                self._log(tr("Avviso: segnale già disconnesso o non disponibile: %s") % exc)


    def showEvent(self, event):
        """Aggiorna i layer ogni volta che la finestra viene mostrata."""

        self._refresh_layers()

        self._refresh_style_fields()
        self._refresh_exist_fields()

        super().showEvent(event)

    # ------------------------------------------------------ elenchi layer
    def _refresh_layers(self, *_args):
        prj = QgsProject.instance()
        # raster
        cur = self.cmb_raster.currentData()
        self.cmb_raster.blockSignals(True)
        self.cmb_raster.clear()
        for lyr in prj.mapLayers().values():
            if isinstance(lyr, QgsRasterLayer) and lyr.isValid() and lyr.providerType() == "gdal":
                self.cmb_raster.addItem(lyr.name(), lyr.id())
        i = self.cmb_raster.findData(cur)
        self.cmb_raster.setCurrentIndex(i if i >= 0 else 0)
        self.cmb_raster.blockSignals(False)
        self._on_raster_changed()
        # vettoriali lineari
        curv = self.cmb_exist_layer.currentData()
        self.cmb_exist_layer.blockSignals(True)
        self.cmb_exist_layer.clear()
        for lyr in prj.mapLayers().values():
            if isinstance(lyr, QgsVectorLayer) and lyr.isValid() \
                    and lyr.geometryType() == Qgis.GeometryType.Line:
                self.cmb_exist_layer.addItem(lyr.name(), lyr.id())
        i = self.cmb_exist_layer.findData(curv)
        self.cmb_exist_layer.setCurrentIndex(i if i >= 0 else 0)
        self.cmb_exist_layer.blockSignals(False)
        self._refresh_exist_fields()

    def _current_raster(self):
        lid = self.cmb_raster.currentData()
        return QgsProject.instance().mapLayer(lid) if lid else None

    def _meters_factors(self, layer):
        try:
            crs = layer.crs()
            if crs.isGeographic():
                lat = math.radians(layer.extent().center().y())
                return 111320.0 * math.cos(lat), 110540.0
            f = QgsUnitTypes.fromUnitToUnitFactor(crs.mapUnits(), Qgis.DistanceUnit.Meters)
            return f, f
        except Exception:
            return 1.0, 1.0

    def _pixel_m(self, layer):
        prov = layer.dataProvider()
        ext = prov.extent()
        mx, my = self._meters_factors(layer)
        return ext.width() / prov.xSize() * mx, ext.height() / prov.ySize() * my

    def _on_raster_changed(self, *_args):
        layer = self._current_raster()
        self.cmb_band.clear()
        if layer is None:
            self.lbl_info.setText(tr("Nessun raster (GDAL) disponibile nel progetto."))
            self.lbl_thr.setText("")
            return
        for b in range(1, layer.bandCount() + 1):
            self.cmb_band.addItem(tr("Banda %d - %s") % (b, layer.bandName(b)), b)
        prov = layer.dataProvider()
        rx, ry = self._pixel_m(layer)
        self.lbl_info.setText(
            "%d × %d celle   •   risoluzione ≈ %.2f × %.2f m   •   CRS: %s"
            % (prov.xSize(), prov.ySize(), rx, ry, layer.crs().authid() or "n.d."))
        if not self._path_edited:
            base = layer.source().split("|")[0]
            folder = os.path.dirname(base) if os.path.isfile(base) else tempfile.gettempdir()
            if not os.access(folder, os.W_OK):
                folder = tempfile.gettempdir()
            name = re.sub(r"[^\w\-]+", "_", layer.name()) + "_reticolo.gpkg"
            self.edt_out.setText(os.path.join(folder, name))
        self._update_thr_hint()

    def _update_flow_description(self, *_a):
        descriptions = {
            "d8": tr(
                "D8 assegna il 100% del flusso alla cella vicina con la massima pendenza "
                "tra le 8 direzioni cardinali e diagonali. È deterministico e molto semplice, "
                "ma introduce una quantizzazione angolare a 45° e può creare percorsi geometrici "
                "paralleli o diagonali. A parità di pendenza, la scelta dipende dalla regola di "
                "priorità adottata dall'algoritmo."
            ),

            "dinf": tr(
                "D∞ (Tarboton) divide la superficie locale in 8 triangoli adiacenti e calcola, "
                "in ciascun triangolo, il vettore di massima discesa di un piano locale. La direzione "
                "è quindi continua su 360° e non è vincolata agli angoli del D8. L'accumulo segue il "
                "vettore; per costruire il reticolo rasterizzato viene mantenuto un asse principale verso "
                "il vicino più coerente con la direzione calcolata. Questo permette di rappresentare "
                "meglio le direzioni intermedie rispetto alle sole 8 direzioni del D8."
            ),

            "rho8": tr(
                "Rho8 (Fairfield & Leymarie, 1991) mantiene un solo ricevitore, ma sceglie "
                "casualmente fra i vicini a quota inferiore con probabilità proporzionale alla "
                "pendenza locale. Il 100% del flusso segue il vicino estratto. Il seed rende la "
                "realizzazione riproducibile; non viene usata una potenza arbitraria della pendenza. "
                "Il metodo è pensato per ridurre il bias direzionale del reticolo mantenendo un "
                "routing convergente a singolo flusso."
                " Una volta "
                "effettuata la selezione, il 100% del flusso viene indirizzato verso il vicino "
                "scelto, esattamente come nel D8. "
                "Rispetto al D8 deterministico, la componente casuale permette di evitare che "
                "la scelta sistematica della massima pendenza produca sempre gli stessi "
                "percorsi fortemente allineati alla griglia, soprattutto su superfici poco "
                "inclinate o caratterizzate da molte direzioni possibili. "
                "Il parametro seed controlla il generatore pseudo-casuale: utilizzando lo "
                "stesso seed si ottiene la stessa sequenza di scelte e quindi un risultato "
                "riproducibile; cambiando il seed si ottiene invece una diversa realizzazione "
                "del reticolo di drenaggio. Il seed non modifica le quote del DEM né le "
                "pendenze calcolate, ma determina esclusivamente quale delle direzioni "
                "ammissibili viene estratta casualmente."
            ),

            "mfd": tr(
                "MFD di Quinn et al. (1991) distribuisce il contributo a tutte le celle vicine a quota inferiore. "
                "La frazione è f_i = tan(β_i)^p L_i / Σ(tan(β_j)^p L_j), con p=1 nella formulazione originale. "
                "L_i è la lunghezza di contorno efficace: 0,5 della dimensione ortogonale per cardinali e "
                "0,354 della dimensione della cella per diagonali nel caso quadrato. Il routing è vettoriale "
                "e mass-conservativo."
            ),

            "mdinf": tr(
                "MD∞ (Seibert & McGlynn, 2007) combina faccette triangolari e multiple flow direction. "
                "Vengono valutate tutte le faccette locali; le direzioni valide sono pesate secondo la "
                "pendenza con esponente configurabile (default 1,1) e, quando una direzione cade tra "
                "due vicini, la quota viene ulteriormente ripartita in base alla distanza angolare. "
                "Questo evita la dispersione irrealistica del MFD classico su superfici piane/concave e "
                "permette più ricevitori sulle superfici convesse."
            ),

            "demon": tr(
                "DEMON-conservativo: parte dalla coppia di ricevitori e dalla direzione D∞, poi modula "
                "solo il rapporto di ripartizione con la divergenza del campo vettoriale D∞. La divergenza "
                "positiva tende a rendere il riparto più simmetrico, quella negativa lo concentra, senza "
                "introdurre nuovi ricevitori. Le frazioni sono sempre rinormalizzate a somma uno: non c'è "
                "dispersione cumulativa a quattro celle e il routing resta mass-conservativo. La formulazione "
                "geometrica DEMON originale di Costa-Cabral & Burges (1994) è usata qui come riferimento "
                "concettuale, non come stream-tube tracer separato."
            ),
        }
        self.lbl_flow_info.setText(descriptions.get(self.cmb_flow_method.currentData(), ""))

    # -------------------------------------------------------------- soglia
    def _update_threshold_description(self, *_a):
        mode = self.cmb_thr_mode.currentData()
        desc = {
            "area": tr("Area drenata minima: una cella diventa canale quando l'area contribuente a monte raggiunge la soglia in km². È il criterio più diretto e indipendente dalla scala dell'algoritmo di routing."),
            "slope_area": tr("Pendenza–area: il canale viene avviato quando a^n·S^m supera la soglia, con a area contribuente specifica, S = sin(β), e n,m esponenti. È una forma standard della relazione topografica di channel initiation; i parametri vanno calibrati sul contesto locale."),
            "spi": tr("SPI (Stream Power Index): usa la potenziale concentrazione del deflusso, SPI = a·tan(β), dove a è l'area contribuente specifica e β la pendenza. Valori elevati identificano zone dove contributo e pendenza favoriscono la concentrazione del flusso."),
            "twi": tr("TWI (Topographic Wetness Index): TWI = ln(a/tan(β)). È un indice di potenziale saturazione/accumulo idrico, non una legge universale di incisione dei canali; valori elevati selezionano le zone topograficamente più umide."),
        }
        self.lbl_thr_desc.setText(desc.get(mode, ""))
        slope_area = mode == "slope_area"
        self.spn_thr_n.setEnabled(slope_area)
        self.spn_thr_m.setEnabled(slope_area)
        self.spn_thr.setDecimals(6 if mode != "twi" else 3)
        if mode == "area":
            self.spn_thr.setSuffix(tr(" km²"))
            self.spn_thr.setValue(min(max(self.spn_thr.value(), 1e-6), 1e9))
        elif mode == "slope_area":
            self.spn_thr.setSuffix(tr(" (unità di a^n)"))
        elif mode == "spi":
            self.spn_thr.setSuffix("")
        elif mode == "twi":
            self.spn_thr.setSuffix("")
        self._update_thr_hint()

    def _update_thr_hint(self, *_a):
        layer = self._current_raster()
        mode = self.cmb_thr_mode.currentData()
        if layer is None:
            self.lbl_thr.setText("")
            return
        rx, ry = self._pixel_m(layer)
        area = rx * ry
        v = self.spn_thr.value()
        if mode == "area":
            self.lbl_thr.setText(tr("≈ %.3f celle equivalenti") % (v * 1e6 / area))
        elif mode == "slope_area":
            self.lbl_thr.setText(tr("Criterio: A^%.2f · S^%.2f ≥ %.6g") % (self.spn_thr_n.value(), self.spn_thr_m.value(), v))
        elif mode == "spi":
            self.lbl_thr.setText(tr("Criterio: SPI ≥ %.6g") % v)
        else:
            self.lbl_thr.setText(tr("Criterio: TWI ≥ %.6g") % v)


    def _collect_params(self):
        layer = self._current_raster()
        if layer is None:
            raise ValueError(tr("Seleziona un DTM/DEM di input."))
        orders = [k for k, cb in self.order_checks.items() if cb.isChecked()]
        if not orders:
            raise ValueError(tr("Seleziona almeno un metodo di ordinamento."))
        out = self.edt_out.text().strip()
        if not out:
            raise ValueError(tr("Indica il file GeoPackage di uscita."))
        if not out.lower().endswith(".gpkg"):
            out += ".gpkg"
        try:
            os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        except OSError as exc:
            raise ValueError(tr("Cartella di uscita non valida: %s") % exc)
        if os.path.exists(out):
            ans = QMessageBox.question(
                self, tr("HydroNet Studio"), tr("Il file '%s' esiste gia'. Sovrascriverlo?") % out,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans != QMessageBox.StandardButton.Yes:
                raise ValueError(tr("Elaborazione annullata: scegli un altro file di uscita."))
        prov = layer.dataProvider()
        cols, rows = prov.xSize(), prov.ySize()
        if cols * rows > 30e6:
            ans = QMessageBox.question(
                self, tr("HydroNet Studio"),
                tr("Il raster ha %.0f milioni di celle: l'elaborazione richiedera' molto tempo "
                   "e memoria. Continuare?") % (cols * rows / 1e6),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans != QMessageBox.StandardButton.Yes:
                raise ValueError(tr("Elaborazione annullata."))
        ext = prov.extent()
        mx, my = self._meters_factors(layer)
        try:
            prov_clone = prov.clone() or prov
        except Exception:
            prov_clone = prov
        name = self.edt_name.text().strip() or tr("Reticolo idrografico")
        return {
            "provider": prov_clone,
            "band": self.cmb_band.currentData() or 1,
            "extent": ext,
            "cols": cols, "rows": rows,
            "xmin": ext.xMinimum(), "ymax": ext.yMaximum(),
            "xres": ext.width() / cols, "yres": ext.height() / rows,
            "mx": mx, "my": my,
            "crs_wkt": layer.crs().toWkt() if layer.crs().isValid() else "",
            "nodata_extra": self.spn_nodata.value() if self.chk_nodata.isChecked() else None,
            "flow_method": self.cmb_flow_method.currentData() or "d8",
            "flow_seed": self.spn_flow_seed.value(),
            "thr_mode": self.cmb_thr_mode.currentData(),
            "thr_value": self.spn_thr.value(),
            "thr_n": self.spn_thr_n.value(),
            "thr_m": self.spn_thr_m.value(),
            "smooth_method": self.cmb_smooth.currentData(),
            "smooth_strength": self.spn_strength.value(),
            "smooth_density": self.spn_density.value(),
            "orders": orders,
            "out_gpkg": out,
            "layer_name": re.sub(r"[^\w]+", "_", name).strip("_") or "reticolo",
            "display_name": name,
            "save_filled": self.chk_filled.isChecked(),
            "save_acc": self.chk_acc.isChecked(),
        }

    def _set_running(self, running):
        self.btn_run.setEnabled(not running)
        self.btn_cancel.setEnabled(running)
        self.nav.setEnabled(not running)
        self.stack.setEnabled(not running)

    def _start(self):
        if self.worker is not None:
            return
        try:
            params = self._collect_params()
        except ValueError as exc:
            QMessageBox.warning(self, "HydroNet Studio", str(exc))
            return
        self._params = params
        self._success = False
        self.log.clear()
        self.progress.setValue(0)
        self._set_running(True)
        self._log(tr("Avvio elaborazione."))
        self.worker = HydroWorker(params, self)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.message.connect(self._log)
        self.worker.succeeded.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.finished.connect(self._on_thread_finished)
        self.worker.start()

    def _cancel(self):
        if self.worker is not None:
            self._log(tr("Annullamento in corso…"))
            self.btn_cancel.setEnabled(False)
            self.worker.cancel()

    def _on_success(self, res):
        self._success = True
        self.progress.setValue(100)
        p = self._params
        prj = QgsProject.instance()
        try:
            if p["save_filled"] or p["save_acc"]:
                if self.chk_load.isChecked():
                    for path in res["rasters"]:
                        rl = QgsRasterLayer(path, os.path.splitext(os.path.basename(path))[0])
                        if rl.isValid():
                            prj.addMapLayer(rl)
            uri = "%s|layername=%s" % (res["gpkg"], res["layer_name"])
            vl = QgsVectorLayer(uri, p["display_name"], "ogr")
            if not vl.isValid():
                raise RuntimeError(tr("Impossibile caricare il layer risultante."))
            if self.chk_style.isChecked() and res["orders"]:
                field = self.cmb_style_field.currentData()
                if field not in res["orders"]:
                    field = next(iter(res["orders"]))
                desc = styler.apply_order_style(vl, field, self.spn_wmin.value(),
                                                self.spn_wmax.value(), self.col_min.color(),
                                                self.col_max.color())
                self._log(tr("Stile %s sul campo '%s'.") % (desc, field))
                try:
                    vl.saveDefaultStyle()
                except Exception as exc:
                    self._log(tr("Avviso: impossibile salvare lo stile predefinito: %s") % exc)
            prj.addMapLayer(vl)
        except Exception as exc:
            self._log(tr("ERRORE nel caricamento: %s") % exc)
        for k, vals in res["orders"].items():
            self._log(tr("Ordine %s: da %d a %d.") % (k, vals[0], vals[-1]))
        self._log(tr("Completato: %d segmenti -> %s") % (res["n_segments"], res["gpkg"]))

    def _on_failed(self, tb):
        self._log(tr("ERRORE:\n") + tb)
        last = tb.strip().splitlines()[-1] if tb.strip() else "errore sconosciuto"
        QMessageBox.critical(self, tr("HydroNet Studio"), tr("Elaborazione fallita:\n%s") % last)

    def _on_cancelled(self):
        self._log(tr("Elaborazione annullata dall'utente."))

    def _on_thread_finished(self):
        w = self.worker
        self.worker = None
        if w is not None:
            w.deleteLater()
        self._set_running(False)
        if self._success:
            # mostra il 100% per un istante, poi riporta la barra a zero
            QTimer.singleShot(1200, lambda: self.progress.setValue(0))
        else:
            self.progress.setValue(0)

    # ------------------------------------------------------------ chiusura
    def closeEvent(self, event):
        if self.worker is not None:
            ans = QMessageBox.question(
                self, tr("HydroNet Studio"), tr("Elaborazione in corso. Annullarla e chiudere?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ans != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.worker.cancel()
            self.worker.wait(15000)
        super().closeEvent(event)
