# -*- coding: utf-8 -*-
"""
HydroNet Studio
Estrae da un DTM/DEM un reticolo idrografico smussato naturalmente, con
ordinamento gerarchico (Strahler, Shreve, Horton, Gravelius/Hack,
topologico) e stile automatico degli spessori.
"""


def classFactory(iface):
    from .plugin import HydroNetStudioPlugin
    return HydroNetStudioPlugin(iface)
