# -*- coding: utf-8 -*-
"""HydroNet Studio - classe principale del plugin QGIS."""
import os

from qgis.PyQt.QtCore import QCoreApplication, QLocale, QSettings, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

PLUGIN_DIR = os.path.dirname(__file__)


class HydroNetStudioPlugin:
    """Punto di ingresso del plugin. Non modifica la finestra principale di QGIS
    oltre all'aggiunta di una voce di menu e di un pulsante nella toolbar."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.menu = "&HydroNet Studio"
        self.translator = None
        self._install_translator()

    # -- localizzazione ------------------------------------------------
    def _install_translator(self):
        locale = QSettings().value("locale/userLocale", QLocale().name())
        locale = (locale or "en")[:2]
        qm_path = os.path.join(PLUGIN_DIR, "i18n", "hydronet_studio_%s.qm" % locale)
        if os.path.exists(qm_path):
            self.translator = QTranslator()
            if self.translator.load(qm_path):
                QCoreApplication.installTranslator(self.translator)

    # -- ciclo di vita del plugin ---------------------------------------
    def initGui(self):
        icon = QIcon(os.path.join(PLUGIN_DIR, "icon.svg"))
        self.action = QAction(icon, self.tr("HydroNet Studio…"), self.iface.mainWindow())
        self.action.setStatusTip(
            self.tr("Estrai un reticolo idrografico gerarchico da un DTM/DEM"))
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.menu, self.action)

    def unload(self):
        if self.action:
            self.iface.removePluginMenu(self.menu, self.action)
            self.iface.removeToolBarIcon(self.action)
            self.action = None
        if self.dialog is not None:
            self.dialog.close()
            self.dialog.cleanup()
            self.dialog = None
        if self.translator is not None:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None

    def run(self):
        # Finestra indipendente (non ancorabile, non modale): non tocca il
        # layout della finestra principale di QGIS. Viene creata una sola
        # volta e riutilizzata/riportata in primo piano alle chiamate successive.
        if self.dialog is None:
            from .dialog import HydroNetDialog
            self.dialog = HydroNetDialog(self.iface, os.path.join(PLUGIN_DIR, "icon.svg"),
                                         parent=self.iface.mainWindow())
            self.dialog.destroyed.connect(self._on_dialog_destroyed)
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    def _on_dialog_destroyed(self):
        self.dialog = None

    def tr(self, text):
        return QCoreApplication.translate("HydroNetStudioPlugin", text)
