# -*- coding: utf-8 -*-
"""Thread di elaborazione: lettura DEM, idrologia, ordinamenti, smussatura, scrittura GPKG."""
import math
import os
import traceback

import numpy as np
from qgis.PyQt.QtCore import QCoreApplication, QThread, pyqtSignal
from qgis.core import Qgis

from . import engine


def tr(text):
    """Marca (e traduce, se disponibile) le stringhe generate dal motore di elaborazione."""
    return QCoreApplication.translate("HydroWorker", text)

ORDER_FIELDS = {
    "strahler": "strahler",
    "shreve": "shreve",
    "horton": "horton",
    "gravelius": "gravelius",
    "topologico": "topologico",
}


def _dtype_map():
    m = {}
    for name, dt in (("Byte", np.uint8), ("Int8", np.int8), ("UInt16", np.uint16),
                     ("Int16", np.int16), ("UInt32", np.uint32), ("Int32", np.int32),
                     ("Float32", np.float32), ("Float64", np.float64)):
        enum = getattr(Qgis.DataType, name, None)
        if enum is not None:
            m[enum] = dt
    return m


class HydroWorker(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.p = params
        self._cancel = False

    # -- controllo ---------------------------------------------------------
    def cancel(self):
        self._cancel = True

    def _chk(self):
        if self._cancel:
            raise engine.Cancelled()

    def _stage(self, a, b):
        def cb(f):
            self.progress.emit(int(a + (b - a) * max(0.0, min(1.0, f))))
        return cb

    def _log(self, txt):
        self.message.emit(txt)

    # -- thread ------------------------------------------------------------
    def run(self):
        try:
            res = self._pipeline()
            self.succeeded.emit(res)
        except engine.Cancelled:
            self.cancelled.emit()
        except Exception:
            self.failed.emit(traceback.format_exc())

    # -- lettura DEM -------------------------------------------------------
    def _read_dem(self):
        p = self.p
        prov = p["provider"]
        cols, rows = p["cols"], p["rows"]
        block = prov.block(p["band"], p["extent"], cols, rows)
        if block is None or not block.isValid():
            raise RuntimeError(tr("Impossibile leggere il raster in ingresso."))
        npdt = _dtype_map().get(block.dataType())
        if npdt is None:
            raise RuntimeError(tr("Tipo di dato raster non supportato."))
        arr = np.frombuffer(bytes(block.data()), dtype=npdt)
        if arr.size != cols * rows:
            raise RuntimeError(tr("Dimensioni del blocco raster inattese."))
        arr = arr.reshape(rows, cols).astype(np.float64)
        mask = ~np.isfinite(arr)
        if block.hasNoDataValue():
            mask |= (arr == block.noDataValue())
        mask |= np.abs(arr) > 1e30
        if p.get("nodata_extra") is not None:
            mask |= (arr == p["nodata_extra"])
        arr[mask] = np.nan
        return arr

    # -- pipeline ----------------------------------------------------------
    def _pipeline(self):
        p = self.p
        cols, rows = p["cols"], p["rows"]
        xmin, ymax = p["xmin"], p["ymax"]
        xres, yres = p["xres"], p["yres"]
        mx, my = p["mx"], p["my"]
        rx, ry = xres * mx, yres * my
        cell_area = rx * ry

        self._log(tr("Lettura del DEM…"))
        self.progress.emit(1)
        dem = self._read_dem()
        self._chk()
        valid = ~np.isnan(dem)
        nvalid = int(valid.sum())
        if nvalid < 9:
            raise RuntimeError(tr("Il DEM non contiene abbastanza celle valide."))
        self._log(tr("DEM: %d × %d celle, risoluzione %.2f × %.2f m, %d celle valide.")
                  % (cols, rows, rx, ry, nvalid))
        self.progress.emit(4)

        flow_method = p.get("flow_method", "d8")
        method_label = tr(engine.FLOW_METHOD_INFO.get(flow_method, flow_method))
        self._log(tr("Riempimento depressioni e direzioni di drenaggio (%s)…")
                  % method_label)
        filled, recv_pf, seeds = engine.priority_flood(dem, self._stage(4, 34), self._chk)
        if flow_method == "d8":
            recv = engine.refine_receivers(filled, recv_pf, seeds, rx, ry)
        else:
            recv = engine.flow_direction_advanced(
                filled, rx, ry, flow_method, int(p.get("flow_seed", 42)),
                self._stage(34, 43), self._chk)
            # Le celle di sbocco e le celle senza vicini più bassi conservano
            # la direzione garantita dal Priority-Flood.
            recv = np.where(recv >= 0, recv, recv_pf)
        self._chk()
        filled_cells = int(np.nansum(filled > dem + 1e-9))
        self._log(tr("Celle riempite: %d.") % filled_cells)

        self._log(tr("Flow accumulation (%s)…") % flow_method)
        acc = engine.flow_accumulation(
            recv, valid, self._stage(44, 62), self._chk,
            filled=filled, rx=rx, ry=ry, method=flow_method,
            seed=int(p.get("flow_seed", 42)),
            exponent=float(p.get("flow_exponent", 1.0)))
        self._chk()

        # Criterio di innesco del canale. L'area drenata resta un criterio
        # assoluto in km²; gli altri criteri sono applicati al raster derivato
        # secondo le loro formulazioni pubblicate.
        thr_mode = p.get("thr_mode", "area") or "area"
        thr_value = float(p["thr_value"])
        if thr_value <= 0:
            raise RuntimeError(tr("La soglia di innesco deve essere maggiore di zero."))
        self._log(tr("Calcolo del criterio di innesco: %s…") % thr_mode)
        stream_mask = engine.channel_initiation_mask(
            acc, filled, rx, ry, recv, mode=thr_mode, threshold=thr_value,
            n=float(p.get("thr_n", 1.0)), m=float(p.get("thr_m", 2.0)))
        nstream = int(stream_mask.sum())
        self._log(tr("Celle che soddisfano il criterio: %d.") % nstream)
        if thr_mode == "area":
            self._log(tr("Soglia di area drenata: %.6f km² (%.3f celle equivalenti).")
                      % (thr_value, thr_value * 1e6 / cell_area))
        elif thr_mode == "slope_area":
            self._log(tr("Soglia pendenza–area: a^%.2f · S^%.2f ≥ %.6g.")
                      % (float(p.get("thr_n",1.0)), float(p.get("thr_m",2.0)), thr_value))
        elif thr_mode == "spi":
            self._log(tr("Soglia SPI: %.6g.") % thr_value)
        else:
            self._log(tr("Soglia TWI: %.6g.") % thr_value)

        self._log(tr("Estrazione del reticolo…"))
        net = engine.extract_network(recv, acc, check=self._chk,
                                     filled=filled, cell_area=cell_area,
                                     stream_mask=stream_mask)
        if net is None:
            raise RuntimeError(tr("Nessun canale estratto con la soglia impostata: "
                               "riduci l'area minima drenata."))
        paths = net["paths"]
        nseg = len(paths)
        self._log(tr("Segmenti estratti: %d (sbocchi: %d).") % (nseg, len(net["roots"])))
        self.progress.emit(70)
        self._chk()

        accf = acc.ravel()
        key = [accf[pt[-1] if net["down"][i] < 0 else pt[-2]] for i, pt in enumerate(paths)]

        self._log(tr("Calcolo degli ordinamenti gerarchici…"))
        wanted = p["orders"]
        strahler = engine.order_strahler(net)
        orders = {}
        if "strahler" in wanted:
            orders["strahler"] = strahler
        if "shreve" in wanted:
            orders["shreve"] = engine.order_shreve(net)
        if "horton" in wanted:
            orders["horton"] = engine.order_horton(net, strahler, key)
        if "gravelius" in wanted:
            orders["gravelius"] = engine.order_gravelius(net, key)
        if "topologico" in wanted:
            orders["topologico"] = engine.order_topological(net)
        self.progress.emit(76)
        self._chk()

        # -- geometrie smussate ------------------------------------------
        self._log(tr("Smussatura delle linee (%s)…") % p["smooth_method"])
        filledf = filled.ravel()
        records = []
        for i, pt in enumerate(paths):
            if (i & 0x1FF) == 0:
                self._chk()
                self.progress.emit(76 + int(14 * i / max(1, nseg)))
            arr = np.asarray(pt, dtype=np.int64)
            rr, cc = np.divmod(arr, cols)
            xy = np.column_stack([xmin + (cc + 0.5) * xres, ymax - (rr + 0.5) * yres])
            sm = engine.smooth_line(xy, p["smooth_method"], p["smooth_strength"],
                                    p["smooth_density"])
            d = np.diff(sm, axis=0)
            length = float(np.sum(np.hypot(d[:, 0] * mx, d[:, 1] * my)))
            e_up, e_dn = float(filledf[arr[0]]), float(filledf[arr[-1]])
            slope = (e_up - e_dn) / length * 100.0 if length > 0 else 0.0
            rec = {
                "geom": sm,
                "attrs": {
                    "seg_id": i + 1,
                    "down_id": (net["down"][i] + 1) if net["down"][i] >= 0 else None,
                    "n_monte": len(net["children"][i]),
                    "lunghezza_m": round(length, 3),
                    "area_km2": round(float(key[i]) * cell_area / 1e6, 6),
                    "quota_monte": round(e_up, 3),
                    "quota_valle": round(e_dn, 3),
                    "pendenza_pc": round(slope, 4),
                    "flow_alg": flow_method,
                },
            }
            for k, vals in orders.items():
                rec["attrs"][ORDER_FIELDS[k]] = int(vals[i])
            records.append(rec)
        self._chk()

        # -- scrittura ---------------------------------------------------
        self._log(tr("Scrittura del GeoPackage…"))
        self.progress.emit(91)
        int_fields = ["seg_id", "down_id", "n_monte"] + [ORDER_FIELDS[k] for k in orders]
        real_fields = ["lunghezza_m", "area_km2", "quota_monte", "quota_valle", "pendenza_pc"]
        text_fields = ["flow_alg"]
        self._write_gpkg(p["out_gpkg"], p["layer_name"], p["crs_wkt"], records,
                         int_fields, real_fields, text_fields)
        self.progress.emit(96)

        rasters = []
        base = os.path.splitext(p["out_gpkg"])[0]
        gt = (xmin, xres, 0.0, ymax, 0.0, -yres)
        if p["save_filled"]:
            path = base + "_dem_riempito.tif"
            self._write_tif(path, np.where(valid, filled, np.nan), gt, p["crs_wkt"])
            rasters.append(path)
        if p["save_acc"]:
            path = base + "_flow_acc.tif"
            self._write_tif(path, np.where(valid, acc, np.nan), gt, p["crs_wkt"])
            rasters.append(path)
        self.progress.emit(99)

        summary = {k: sorted(set(v)) for k, v in orders.items()}
        return {
            "gpkg": p["out_gpkg"],
            "layer_name": p["layer_name"],
            "n_segments": nseg,
            "orders": summary,
            "rasters": rasters,
            "threshold_mode": thr_mode,
            "threshold_value": thr_value,
        }

    # -- I/O ---------------------------------------------------------------
    @staticmethod
    def _write_gpkg(
        path,
        layer_name,
        crs_wkt,
        records,
        int_fields,
        real_fields,
        text_fields=None,
    ):
        from osgeo import ogr, osr

        drv = ogr.GetDriverByName("GPKG")

        if os.path.exists(path):
            if drv.DeleteDataSource(path) != 0:
                raise RuntimeError(
                    tr("Impossibile sovrascrivere '%s' (file in uso?).") % path
                )

        ds = drv.CreateDataSource(path)
        if ds is None:
            raise RuntimeError(
                tr("Impossibile creare '%s'.") % path
            )

        srs = None
        if crs_wkt:
            srs = osr.SpatialReference()
            srs.ImportFromWkt(crs_wkt)

            try:
                srs.SetAxisMappingStrategy(
                    osr.OAMS_TRADITIONAL_GIS_ORDER
                )
            except (AttributeError, RuntimeError):
                # Older GDAL/OSR builds may not expose axis-mapping control.
                # Keep the layer creation compatible.
                pass

        lyr = ds.CreateLayer(
            layer_name,
            srs,
            ogr.wkbLineString,
        )

        for field_name in int_fields:
            lyr.CreateField(
                ogr.FieldDefn(field_name, ogr.OFTInteger)
            )

        for field_name in real_fields:
            lyr.CreateField(
                ogr.FieldDefn(field_name, ogr.OFTReal)
            )

        for field_name in (text_fields or []):
            lyr.CreateField(
                ogr.FieldDefn(field_name, ogr.OFTString)
            )

        defn = lyr.GetLayerDefn()

        lyr.StartTransaction()

        for rec in records:
            feat = ogr.Feature(defn)

            for key, value in rec["attrs"].items():
                if value is not None:
                    feat.SetField(key, value)

            geom = ogr.Geometry(ogr.wkbLineString)

            for x, y in rec["geom"]:
                geom.AddPoint_2D(
                    float(x),
                    float(y),
                )

            feat.SetGeometry(geom)
            lyr.CreateFeature(feat)
            feat = None

        lyr.CommitTransaction()
        ds = None

    @staticmethod
    def _write_tif(path, arr, gt, crs_wkt):
        from osgeo import gdal

        rows, cols = arr.shape
        drv = gdal.GetDriverByName("GTiff")

        ds = drv.Create(
            path,
            cols,
            rows,
            1,
            gdal.GDT_Float32,
            options=["COMPRESS=DEFLATE", "TILED=YES"],
        )

        ds.SetGeoTransform(gt)

        if crs_wkt:
            ds.SetProjection(crs_wkt)

        band = ds.GetRasterBand(1)
        band.SetNoDataValue(-9999.0)

        out = np.where(
            np.isnan(arr),
            -9999.0,
            arr,
        ).astype(np.float32)

        band.WriteArray(out)
        band.FlushCache()
        ds = None
