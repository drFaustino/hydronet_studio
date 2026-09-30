# -*- coding: utf-8 -*-
"""
HydroNet Studio - motore idrologico (solo numpy, nessuna dipendenza da Qt/QGIS).

Pipeline:
    1. Priority-Flood (riempimento depressioni + direzioni di drenaggio garantite)
    2. Raffinamento D8 a massima pendenza sulle celle non piatte
    3. Flow accumulation vettorizzata (Kahn per livelli)
    4. Estrazione reticolo per soglia + tracciamento segmenti (tra confluenze)
    5. Ordinamenti gerarchici (Strahler, Shreve, Horton, Gravelius/Hack, Topologico)
    6. Smussatura naturale delle polilinee (gaussiana / Chaikin / Catmull-Rom)
"""
import heapq
import math

import numpy as np


class Cancelled(Exception):
    """Sollevata quando l'utente annulla l'elaborazione."""


NEIGH = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def _noop(*_a, **_k):
    return None


# --------------------------------------------------------------------------
# 1. Riempimento depressioni + direzioni (Priority-Flood, Barnes et al. 2014)
# --------------------------------------------------------------------------
def priority_flood(dem, progress=None, check=None):
    """
    dem: array 2D float64 con NaN per NoData.
    Ritorna (filled, recv, seeds):
        filled : DEM depresso riempito
        recv   : indice piatto della cella ricevente (-1 = sbocco / NoData)
        seeds  : maschera delle celle di sbocco (bordo o adiacenti a NoData)
    """
    progress = progress or _noop
    check = check or _noop
    rows, cols = dem.shape
    R, C = rows + 2, cols + 2

    Z = np.full((R, C), np.nan, dtype=np.float64)
    Z[1:-1, 1:-1] = dem
    invalid = np.isnan(Z)
    valid = ~invalid

    nb_invalid = np.zeros((R, C), dtype=bool)
    for dy, dx in NEIGH:
        nb_invalid |= np.roll(np.roll(invalid, dy, axis=0), dx, axis=1)
    seeds_mask = valid & nb_invalid

    zl = Z.ravel().tolist()
    filled = list(zl)
    closed = bytearray(invalid.ravel().astype(np.uint8).tobytes())
    recv = [-1] * (R * C)

    heap = []
    scale = float(np.nanmax(np.abs(dem))) if np.isfinite(dem).any() else 1.0
    epsilon = max(1e-10, scale * 1e-12)
    for i in np.flatnonzero(seeds_mask.ravel()).tolist():
        heap.append((zl[i], i))
        closed[i] = 1
    heapq.heapify(heap)

    offs = (-C - 1, -C, -C + 1, -1, 1, C - 1, C, C + 1)
    total = max(1, int(valid.sum()))
    pop, push = heapq.heappop, heapq.heappush
    n = 0
    while heap:
        zc, c = pop(heap)
        for o in offs:
            k = c + o
            if closed[k]:
                continue
            closed[k] = 1
            recv[k] = c
            zk = zl[k]
            if zk < zc:
                # Priority-Flood epsilon ordering: remove flat cells as true
                # hydrologic flats while keeping the perturbation far below
                # DEM precision for normal terrain.
                zk = zc + epsilon
                filled[k] = zk
            push(heap, (zk, k))
        n += 1
        if (n & 0x3FFF) == 0:
            check()
            progress(min(1.0, n / total))
    progress(1.0)

    filled_a = np.array(filled, dtype=np.float64).reshape(R, C)[1:-1, 1:-1]
    recv_p = np.array(recv, dtype=np.int64).reshape(R, C)[1:-1, 1:-1]
    seeds = seeds_mask[1:-1, 1:-1]

    recv_u = np.full((rows, cols), -1, dtype=np.int64)
    m = recv_p >= 0
    rp = recv_p[m]
    recv_u[m] = (rp // C - 1) * cols + (rp % C - 1)
    return filled_a, recv_u, seeds


def refine_receivers(filled, recv_pf, seeds, rx, ry):
    """
    D8 a massima pendenza dove esiste un vicino strettamente piu' basso;
    altrove (piane / aree riempite) si mantiene la direzione Priority-Flood.
    rx, ry: dimensione cella in metri.
    """
    rows, cols = filled.shape
    Zp = np.pad(filled, 1, mode="constant", constant_values=np.nan)
    best = np.zeros((rows, cols), dtype=np.float64)
    bdir = np.full((rows, cols), -1, dtype=np.int8)
    with np.errstate(invalid="ignore"):
        for k, (dy, dx) in enumerate(NEIGH):
            nb = Zp[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols]
            dist = math.hypot(dy * ry, dx * rx)
            s = (filled - nb) / dist
            better = s > best
            best = np.where(better, s, best)
            bdir[better] = k
    yy, xx = np.indices((rows, cols))
    dyv = np.array([d[0] for d in NEIGH], dtype=np.int64)
    dxv = np.array([d[1] for d in NEIGH], dtype=np.int64)
    tgt = (yy + dyv[bdir]) * cols + (xx + dxv[bdir])
    use = (bdir >= 0) & (~seeds) & (~np.isnan(filled))
    return np.where(use, tgt, recv_pf)



# --------------------------------------------------------------------------
# 2. Direzioni di deflusso avanzate
# --------------------------------------------------------------------------
FLOW_METHODS = ("d8", "dinf", "rho8", "mfd", "mdinf", "demon")

FLOW_METHOD_INFO = {
    "d8": "D8 - massima pendenza (8 direzioni)",
    "dinf": "D∞ - vettore continuo a 360°",
    "rho8": "Rho8 - routing D8 stocastico pesato dalla pendenza",
    "mfd": "MFD classico - flusso verso tutte le celle più basse",
    "mdinf": "MD∞ - D-Infinity multiplo, frazionato sui due lati",
    "demon": "DEMON - routing multi-direzionale sulla superficie",
}


def _valid_neighbors(z, r, c, rx, ry):
    """Restituisce (direzione, indice piatto, pendenza positiva) dei vicini più bassi."""
    rows, cols = z.shape
    out = []
    z0 = z[r, c]
    for k, (dy, dx) in enumerate(NEIGH):
        rr, cc = r + dy, c + dx
        if 0 <= rr < rows and 0 <= cc < cols and np.isfinite(z[rr, cc]):
            dz = z0 - z[rr, cc]
            if dz > 0.0:
                dist = math.hypot(dx * rx, dy * ry)
                out.append((k, rr * cols + cc, dz / dist))
    return out


def _vec_angle(x, y):
    return math.atan2(y, x) % (2.0 * math.pi)


def _angdiff(a, b):
    return (a - b + math.pi) % (2.0 * math.pi) - math.pi


def _dinf_direction(z, r, c, rx, ry):
    """
    Approssimazione fedele al principio D∞ di Tarboton:
    la cella è divisa in 8 triangoli formati da due vicini adiacenti.
    Per ogni triangolo si calcola il piano locale e il vettore di massima
    discesa; se il vettore esce dal triangolo, si usa il lato più ripido.
    Ritorna (angolo, pendenza, due direzioni delimitanti, pesi).
    """
    rows, cols = z.shape
    z0 = z[r, c]
    best_s = 0.0
    best_a = None
    best_pair = None
    # angoli geografici: x verso est, y verso nord
    xy = []
    for k, (dy, dx) in enumerate(NEIGH):
        rr, cc = r + dy, c + dx
        if 0 <= rr < rows and 0 <= cc < cols and np.isfinite(z[rr, cc]):
            x, y = dx * rx, -dy * ry
            xy.append((k, rr, cc, x, y, _vec_angle(x, y)))
    if len(xy) < 1:
        return None

    for i in range(8):
        k1 = i
        k2 = (i + 1) % 8
        a1 = next((q for q in xy if q[0] == k1), None)
        a2 = next((q for q in xy if q[0] == k2), None)
        if a1 is None or a2 is None:
            continue
        x1, y1, x2, y2 = a1[3], a1[4], a2[3], a2[4]
        dz1 = z0 - z[a1[1], a1[2]]
        dz2 = z0 - z[a2[1], a2[2]]
        A = np.array([[x1, y1], [x2, y2]], dtype=float)
        b = np.array([-dz1, -dz2], dtype=float)
        try:
            gx, gy = np.linalg.solve(A, b)  # gradiente di quota
        except np.linalg.LinAlgError:
            continue
        vx, vy = -gx, -gy
        slope = math.hypot(vx, vy)
        if slope <= 0:
            continue
        ang = _vec_angle(vx, vy)
        lo = a1[5]
        span = (_angdiff(a2[5], lo)) % (2.0 * math.pi)
        inside = 0.0 <= span <= math.pi + 1e-12 and (_angdiff(ang, lo) % (2.0 * math.pi)) <= span + 1e-12
        if not inside:
            # proietta sul lato più ripido: uno dei due lati
            s1 = dz1 / math.hypot(x1, y1)
            s2 = dz2 / math.hypot(x2, y2)
            if max(s1, s2) <= 0:
                continue
            if s1 >= s2:
                ang, slope = a1[5], s1
            else:
                ang, slope = a2[5], s2
        if slope > best_s:
            best_s, best_a, best_pair = slope, ang, (k1, k2)

    if best_a is None:
        return None
    return best_a, best_s, best_pair


def _direction_index_for_angle(angle):
    # NEIGH è ordinato: NW,N,NE,W,E,SW,S,SE; convertiamo a coordinate geografiche.
    angles = []
    for k, (dy, dx) in enumerate(NEIGH):
        angles.append((_vec_angle(dx, -dy), k))
    return min(angles, key=lambda q: abs(_angdiff(angle, q[0])))[1]


def _neighbor_slope_arrays(z, rx, ry):
    """Restituisce pendenze positive verso gli 8 vicini, vettorialmente."""
    rows, cols = z.shape
    zp = np.pad(z, 1, mode="constant", constant_values=np.nan)
    slopes = np.full((8, rows, cols), np.nan, dtype=np.float64)
    for k, (dy, dx) in enumerate(NEIGH):
        nb = zp[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols]
        dist = math.hypot(dx * rx, dy * ry)
        with np.errstate(invalid="ignore", divide="ignore"):
            slopes[k] = np.maximum((z - nb) / dist, 0.0)
    return slopes



def _dinf_fields_vectorized(z, rx, ry):
    """Tarboton (1997) D∞ in closed form on the eight triangular facets.

    Each facet is ordered as (cardinal neighbour, adjacent diagonal
    neighbour).  For that facet

        s1 = (z0-z1)/d1
        s2 = (z1-z2)/d2
        r  = atan2(s2, s1)

    is clipped to the facet angular interval.  The resulting direction is
    the steepest downward vector on that triangular plane; flow is later
    apportioned only to the two cells defining that facet.
    """
    rows, cols = z.shape
    zp = np.pad(z, 1, mode="constant", constant_values=np.nan)

    # Cardinal first, diagonal second.  This is the closed-form geometry used
    # by Tarboton's triangular-facet construction.
    facets = (
        (1, 2), (1, 0),       # N-NE, N-NW
        (4, 2), (4, 7),       # E-NE, E-SE
        (6, 7), (6, 5),       # S-SE, S-SW
        (3, 5), (3, 0),       # W-SW, W-NW
    )
    neigh_angles = np.array(
        [_vec_angle(dx * rx, -dy * ry) for dy, dx in NEIGH], dtype=float
    )

    best_s = np.full((rows, cols), -np.inf, dtype=float)
    best_a = np.full((rows, cols), np.nan, dtype=float)
    best_k1 = np.full((rows, cols), -1, dtype=np.int8)
    best_k2 = np.full((rows, cols), -1, dtype=np.int8)
    slopes8 = _neighbor_slope_arrays(z, rx, ry)

    for k1, k2 in facets:
        dy1, dx1 = NEIGH[k1]
        dy2, dx2 = NEIGH[k2]
        n1 = zp[1 + dy1:1 + dy1 + rows, 1 + dx1:1 + dx1 + cols]
        n2 = zp[1 + dy2:1 + dy2 + rows, 1 + dx2:1 + dx2 + cols]

        d1 = math.hypot(dx1 * rx, dy1 * ry)
        d2 = math.hypot((dx2 - dx1) * rx, (dy2 - dy1) * ry)
        ddiag = math.hypot(dx2 * rx, dy2 * ry)
        a1 = neigh_angles[k1]
        a2 = neigh_angles[k2]
        signed_span = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
        theta = abs(signed_span)

        with np.errstate(invalid="ignore", divide="ignore"):
            s1 = (z - n1) / d1
            s2 = (n1 - n2) / d2
            r = np.arctan2(s2, s1)

        low = r < 0.0
        high = r > theta
        radj = np.clip(r, 0.0, theta)
        with np.errstate(invalid="ignore", divide="ignore"):
            sf = np.where(
                low, s1,
                np.where(high, (z - n2) / ddiag, np.hypot(s1, s2))
            )
        sf = np.where(np.isfinite(sf), sf, -np.inf)
        usable = np.isfinite(n1) & np.isfinite(n2)
        sf = np.where(usable, sf, -np.inf)

        # Move from the cardinal edge toward the diagonal edge.
        ang = a1 + np.sign(signed_span) * radj
        ang = (ang + 2.0 * math.pi) % (2.0 * math.pi)

        take = sf > best_s
        best_s = np.where(take, sf, best_s)
        best_a = np.where(take, ang, best_a)
        best_k1 = np.where(take, k1, best_k1)
        best_k2 = np.where(take, k2, best_k2)

    return best_a, best_s, best_k1, best_k2, slopes8


def _dinf_routing_vectorized(z, rx, ry):
    """Return Tarboton D∞ receivers and proportions, max. two per cell."""
    rows, cols = z.shape
    N = rows * cols
    angle, slope, k1, k2, slopes8 = _dinf_fields_vectorized(z, rx, ry)

    r1 = np.full((rows, cols), -1, dtype=np.int64)
    r2 = np.full((rows, cols), -1, dtype=np.int64)
    w1 = np.zeros((rows, cols), dtype=float)
    w2 = np.zeros((rows, cols), dtype=float)

    valid = np.isfinite(z) & np.isfinite(slope) & (slope > 0)
    yy, xx = np.indices((rows, cols))

    # Reconstruct the angular interval of the selected facet.  This gives
    # the exact Tarboton angular proportions without inverse trigonometric
    # recomputation from the final direction.
    a1 = np.take(
        np.array([_vec_angle(dx * rx, -dy * ry) for dy, dx in NEIGH]),
        np.clip(k1, 0, 7)
    )
    a2 = np.take(
        np.array([_vec_angle(dx * rx, -dy * ry) for dy, dx in NEIGH]),
        np.clip(k2, 0, 7)
    )
    signed = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
    span = np.abs(signed)
    pos_ccw = (angle - a1) % (2.0 * math.pi)
    pos_cw = (a1 - angle) % (2.0 * math.pi)
    pos = np.where(signed >= 0.0, pos_ccw, pos_cw)
    pos = np.clip(pos, 0.0, np.maximum(span, 1e-15))
    p2 = np.divide(pos, np.maximum(span, 1e-15))
    p1 = 1.0 - p2

    d1r = np.array([d[0] for d in NEIGH], dtype=np.int64)
    d1c = np.array([d[1] for d in NEIGH], dtype=np.int64)
    d2r = d1r
    d2c = d1c
    dr1 = d1r[np.clip(k1, 0, 7)]
    dc1 = d1c[np.clip(k1, 0, 7)]
    dr2 = d2r[np.clip(k2, 0, 7)]
    dc2 = d2c[np.clip(k2, 0, 7)]
    rr1, cc1 = yy + dr1, xx + dc1
    rr2, cc2 = yy + dr2, xx + dc2

    ok1 = valid & (rr1 >= 0) & (rr1 < rows) & (cc1 >= 0) & (cc1 < cols)
    ok2 = valid & (rr2 >= 0) & (rr2 < rows) & (cc2 >= 0) & (cc2 < cols)
    flatz = z.ravel()
    id1 = np.where(ok1, rr1 * cols + cc1, -1)
    id2 = np.where(ok2, rr2 * cols + cc2, -1)
    z1 = np.where(ok1, flatz[np.clip(id1, 0, N - 1)].reshape(rows, cols), np.nan)
    z2 = np.where(ok2, flatz[np.clip(id2, 0, N - 1)].reshape(rows, cols), np.nan)
    down1 = ok1 & np.isfinite(z1) & (z1 < z)
    down2 = ok2 & np.isfinite(z2) & (z2 < z)

    both = down1 & down2
    only1 = down1 & ~down2
    only2 = down2 & ~down1
    r1[both], r2[both] = id1[both], id2[both]
    w1[both], w2[both] = p1[both], p2[both]
    r1[only1], w1[only1] = id1[only1], 1.0
    r1[only2], w1[only2] = id2[only2], 1.0

    # Boundary/saddle fallback: D8 steepest lower neighbour.
    fallback = valid & (w1 <= 0)
    d8k = np.argmax(np.where(np.isfinite(slopes8), slopes8, -np.inf), axis=0)
    d8s = np.take_along_axis(slopes8, d8k[None, ...], axis=0)[0]
    dr, dc = d1r[d8k], d1c[d8k]
    rr, cc = yy + dr, xx + dc
    ok = fallback & np.isfinite(d8s) & (d8s > 0) & (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
    r1[ok] = rr[ok] * cols + cc[ok]
    r2[ok] = -1
    w1[ok] = 1.0
    w2[ok] = 0.0
    return r1, r2, w1, w2, angle, slope, slopes8


def _mfd_quinn_vectorized(z, rx, ry, exponent=1.0):
    """Quinn et al. (1991) MFD with effective contour lengths.

    F_i = (tan(beta_i)^p L_i) / sum_j(tan(beta_j)^p L_j)

    Quinn's original p=1.  For a rectangular cell the cardinal contour
    lengths are half the orthogonal cell dimension.  For a diagonal route the
    0.35 h term is generalized from the projected cell geometry.
    """
    slopes = _neighbor_slope_arrays(z, rx, ry)
    positive = np.where(np.isfinite(slopes), np.maximum(slopes, 0.0), 0.0)
    L = np.empty(8, dtype=float)
    for k, (dy, dx) in enumerate(NEIGH):
        if dy == 0:
            L[k] = 0.5 * ry
        elif dx == 0:
            L[k] = 0.5 * rx
        else:
            d = math.hypot(dx * rx, dy * ry)
            ux, uy = (dx * rx) / d, (dy * ry) / d
            # Quinn's 0.35 h is the square-cell limit.
            L[k] = 0.25 * (rx * abs(uy) + ry * abs(ux))
    with np.errstate(over="ignore", invalid="ignore"):
        weights = positive ** float(exponent) * L[:, None, None]
    sw = weights.sum(axis=0)
    return np.divide(
        weights, sw[None, ...],
        out=np.zeros_like(weights),
        where=sw[None, ...] > 0
    ), slopes


def _rho8_routing_vectorized(z, rx, ry, seed=42):
    """Fairfield & Leymarie (1991) Rho8: SFD, slope-weighted stochastic choice."""
    slopes = _neighbor_slope_arrays(z, rx, ry)
    positive = np.where(np.isfinite(slopes), np.maximum(slopes, 0.0), 0.0)
    total = positive.sum(axis=0)
    rng = np.random.default_rng(seed)
    u = rng.random(z.shape) * total
    cdf = np.cumsum(positive, axis=0)
    k = np.sum(cdf < u[None, ...], axis=0).astype(np.int8)
    k = np.clip(k, 0, 7)

    rows, cols = z.shape
    yy, xx = np.indices(z.shape)
    dr = np.array([d[0] for d in NEIGH], dtype=np.int64)[k]
    dc = np.array([d[1] for d in NEIGH], dtype=np.int64)[k]
    rr, cc = yy + dr, xx + dc
    chosen_s = np.take_along_axis(positive, k[None, ...], axis=0)[0]
    good = np.isfinite(z) & (total > 0) & (chosen_s > 0) & (rr >= 0) & (rr < rows) & (cc >= 0) & (z[rr.clip(0, rows-1), cc.clip(0, cols-1)] < z)
    recv = np.full(z.shape, -1, dtype=np.int64)
    recv[good] = rr[good] * cols + cc[good]
    return recv, k, slopes


def _mdinf_routing_vectorized(z, rx, ry, exponent=1.1):
    """Seibert & McGlynn (2007) triangular MD∞, vectorized over the raster.

    All eight triangular facets are evaluated in closed form.  A facet whose
    steepest direction lies inside its angular sector contributes to its two
    bounding neighbours by angular partitioning.  A direction that points
    exactly toward a neighbour is retained only when the same edge direction
    is selected by the adjacent facet, as specified by the MD∞ construction.
    The resulting neighbour weights are normalized to unit total.
    """
    rows, cols = z.shape
    zp = np.pad(z, 1, mode="constant", constant_values=np.nan)
    facets = (
        (1, 2), (1, 0),
        (4, 2), (4, 7),
        (6, 7), (6, 5),
        (3, 5), (3, 0),
    )
    neigh_angles = np.array(
        [_vec_angle(dx * rx, -dy * ry) for dy, dx in NEIGH], dtype=float
    )

    fs = np.full((8, rows, cols), -np.inf, dtype=float)
    fp = np.zeros((8, rows, cols), dtype=float)
    fin = np.zeros((8, rows, cols), dtype=bool)
    fedge = np.full((8, rows, cols), -1, dtype=np.int8)

    for i, (k1, k2) in enumerate(facets):
        dy1, dx1 = NEIGH[k1]
        dy2, dx2 = NEIGH[k2]
        n1 = zp[1 + dy1:1 + dy1 + rows, 1 + dx1:1 + dx1 + cols]
        n2 = zp[1 + dy2:1 + dy2 + rows, 1 + dx2:1 + dx2 + cols]
        d1 = math.hypot(dx1 * rx, dy1 * ry)
        d2 = math.hypot((dx2 - dx1) * rx, (dy2 - dy1) * ry)
        ddiag = math.hypot(dx2 * rx, dy2 * ry)
        a1, a2 = neigh_angles[k1], neigh_angles[k2]
        signed = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
        theta = abs(signed)

        with np.errstate(invalid="ignore", divide="ignore"):
            s1 = (z - n1) / d1
            s2 = (n1 - n2) / d2
            rr = np.arctan2(s2, s1)

        low = rr < 0.0
        high = rr > theta
        inside = ~(low | high)
        radj = np.clip(rr, 0.0, theta)
        with np.errstate(invalid="ignore", divide="ignore"):
            slope = np.where(
                low, s1,
                np.where(high, (z - n2) / ddiag, np.hypot(s1, s2))
            )
        valid = np.isfinite(n1) & np.isfinite(n2) & np.isfinite(slope) & (slope > 0)
        fs[i] = np.where(valid, slope, -np.inf)
        fin[i] = valid & inside
        fp[i] = np.divide(radj, max(theta, 1e-15))
        fedge[i] = np.where(low, k1, np.where(high, k2, -1))

    # For each neighbour direction, these are the two adjacent facets sharing
    # that edge. A boundary direction is retained only if both facets select it.
    edge_facets = {
        0: (1, 7),  # NW
        1: (0, 1),  # N
        2: (0, 2),  # NE
        3: (6, 7),  # W
        4: (2, 3),  # E
        5: (5, 6),  # SW
        6: (4, 5),  # S
        7: (3, 4),  # SE
    }
    contrib = np.zeros((8, rows, cols), dtype=float)
    for i in range(8):
        valid_i = np.isfinite(fs[i]) & (fs[i] > 0)
        # Interior facet: split its own two edge directions.
        k1, k2 = facets[i]
        wi = np.where(fin[i], fs[i] ** float(exponent), 0.0)
        contrib[k1] += wi * (1.0 - fp[i])
        contrib[k2] += wi * fp[i]

        # Exterior direction: admit it only if the adjacent facet selects the
        # same direction outside its own sector.
        edge = fedge[i]
        for k in (k1, k2):
            j0, j1 = edge_facets[k]
            other = j1 if j0 == i else j0
            same = valid_i & (~fin[i]) & (edge == k) & (~fin[other]) & (fedge[other] == k)
            contrib[k] += np.where(same, fs[i] ** float(exponent), 0.0)

    sw = contrib.sum(axis=0)
    frac = np.divide(
        contrib, sw[None, ...],
        out=np.zeros_like(contrib),
        where=sw[None, ...] > 0
    )
    yy, xx = np.indices((rows, cols))
    recv = np.full((rows, cols, 8), -1, dtype=np.int64)
    for k, (dy, dx) in enumerate(NEIGH):
        rr, cc = yy + dy, xx + dx
        inside = (
            (frac[k] > 0) & np.isfinite(z) &
            (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
        )
        nb = z[np.clip(rr, 0, rows - 1), np.clip(cc, 0, cols - 1)]
        inside &= np.isfinite(nb) & (nb < z)
        recv[..., k] = np.where(inside, rr * cols + cc, -1)
        frac[k] = np.where(inside, frac[k], 0.0)

    # Renormalize after boundary clipping; this preserves conservation.
    sw = frac.sum(axis=0)
    frac = np.divide(frac, sw[None, ...], out=frac, where=sw[None, ...] > 0)

    # At raster boundaries a complete pair of triangular facets may be
    # unavailable. Preserve the hydrologic graph with the steepest valid
    # downslope neighbour rather than dropping the boundary cell.
    noflow = np.isfinite(z) & (sw <= 0)
    slopes8 = _neighbor_slope_arrays(z, rx, ry)
    k8 = np.argmax(np.where(np.isfinite(slopes8), slopes8, -np.inf), axis=0)
    s8 = np.take_along_axis(slopes8, k8[None, ...], axis=0)[0]
    yy, xx = np.indices((rows, cols))
    for k, (dy, dx) in enumerate(NEIGH):
        rr, cc = yy + dy, xx + dx
        ok = (
            noflow & (s8 > 0) & (k8 == k) &
            (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
        )
        nb = z[np.clip(rr, 0, rows - 1), np.clip(cc, 0, cols - 1)]
        ok &= np.isfinite(nb) & (nb < z)
        recv[..., k] = np.where(ok, rr * cols + cc, recv[..., k])
        frac[k] = np.where(ok, 1.0, frac[k])

    sw = frac.sum(axis=0)
    frac = np.divide(frac, sw[None, ...], out=frac, where=sw[None, ...] > 0)
    kmax = np.argmax(frac, axis=0)
    main = np.take_along_axis(recv, kmax[..., None], axis=2)[..., 0]
    return recv, np.moveaxis(frac, 0, -1), main


def _demon_divergence_modulated_dinf(z, rx, ry, strength=1.0):
    """Conservative DEMON variant built on the D∞ vector field.

    The D∞ pair of receivers is immutable: no third/fourth receiver is ever
    introduced.  Only the split ratio is modified.

    Let q = S (cos(alpha), sin(alpha)) be the local downslope vector and
    D = div(q).  Positive D is locally divergent and negative D convergent.
    The normalized divergence is mapped to a bounded gain.  Divergence pulls
    the two-cell split toward 1/2; convergence sharpens the existing D∞ split.
    The weights are renormalized to sum exactly to one, so the routing is
    conservative by construction.
    """
    r1, r2, w1, w2, angle, slope, slopes8 = _dinf_routing_vectorized(z, rx, ry)
    slope_safe = np.where(np.isfinite(slope) & (slope > 0), slope, 0.0)
    angle_safe = np.where(np.isfinite(angle), angle, 0.0)
    qx = slope_safe * np.cos(angle_safe)
    qy = slope_safe * np.sin(angle_safe)

    qxp = np.pad(qx, 1, mode="edge")
    qyp = np.pad(qy, 1, mode="edge")
    dqx_dx = (qxp[1:-1, 2:] - qxp[1:-1, :-2]) / (2.0 * rx)
    dqy_dy = (qyp[2:, 1:-1] - qyp[:-2, 1:-1]) / (2.0 * ry)
    div = dqx_dx + dqy_dy

    scale = np.maximum(
        np.hypot(qx, qy) / max(min(rx, ry), 1e-12),
        np.nanmedian(np.hypot(qx, qy)[np.isfinite(qx)]) / max(min(rx, ry), 1e-12) if np.isfinite(qx).any() else 1.0e-12
    )
    eta = np.divide(div, scale, out=np.zeros_like(div), where=scale > 1e-15)
    eta = np.clip(np.nan_to_num(eta, nan=0.0, posinf=2.0, neginf=-2.0), -2.0, 2.0)

    # g<1 for divergence => less asymmetry, g>1 for convergence => more.
    g = np.exp(-float(strength) * eta)
    base = np.clip(w2, 0.0, 1.0)
    mod = np.clip(0.5 + (base - 0.5) * g, 0.0, 1.0)

    active = (r2 >= 0) & (w1 > 0) & (w2 > 0)
    w2 = np.where(active, mod, w2)
    w1 = np.where(active, 1.0 - w2, w1)
    # Exact conservation and robust one-receiver fallback.
    total = w1 + w2
    w1 = np.divide(w1, total, out=w1, where=total > 0)
    w2 = np.divide(w2, total, out=w2, where=total > 0)
    return r1, r2, w1, w2, angle, slope, div


def _routing_arrays(z, rx, ry, method, seed=42, exponent=1.0):
    """Build a compact <=8-edge routing graph for vectorized Kahn accumulation."""
    rows, cols = z.shape
    N = rows * cols
    recv = np.full((N, 8), -1, dtype=np.int64)
    frac = np.zeros((N, 8), dtype=float)

    if method == "rho8":
        r, k, _ = _rho8_routing_vectorized(z, rx, ry, seed)
        recv[:, 0] = r.ravel()
        frac[:, 0] = (r.ravel() >= 0).astype(float)
        main = r
        return recv, frac, main

    if method == "d8":
        slopes = _neighbor_slope_arrays(z, rx, ry)
        k = np.argmax(np.where(np.isfinite(slopes), slopes, -np.inf), axis=0)
        s = np.take_along_axis(slopes, k[None, ...], axis=0)[0]
        yy, xx = np.indices(z.shape)
        dr = np.array([d[0] for d in NEIGH], dtype=np.int64)[k]
        dc = np.array([d[1] for d in NEIGH], dtype=np.int64)[k]
        rr, cc = yy + dr, xx + dc
        good = np.isfinite(z) & np.isfinite(s) & (s > 0) & (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
        main = np.full(z.shape, -1, dtype=np.int64)
        main[good] = rr[good] * cols + cc[good]
        recv[:, 0] = main.ravel()
        frac[:, 0] = good.ravel().astype(float)
        return recv, frac, main

    if method == "dinf":
        r1, r2, w1, w2, *_ = _dinf_routing_vectorized(z, rx, ry)
        main = np.where((w2 > w1) & (r2 >= 0), r2, r1)
        recv[:, 0], recv[:, 1] = r1.ravel(), r2.ravel()
        frac[:, 0], frac[:, 1] = w1.ravel(), w2.ravel()
        return recv, frac, main

    if method == "mdinf":
        r, f, main = _mdinf_routing_vectorized(z, rx, ry, exponent=1.1)
        recv[:, :] = r.reshape(N, 8)
        frac[:, :] = f.reshape(N, 8)
        return recv, frac, main

    if method == "mfd":
        weights, slopes = _mfd_quinn_vectorized(z, rx, ry, exponent)
        yy, xx = np.indices(z.shape)
        for k, (dy, dx) in enumerate(NEIGH):
            rr, cc = yy + dy, xx + dx
            good = (weights[k] > 0) & np.isfinite(z) & (rr >= 0) & (rr < rows) & (cc >= 0) & (cc < cols)
            good &= np.isfinite(z[np.clip(rr, 0, rows-1), np.clip(cc, 0, cols-1)])
            good &= z[np.clip(rr, 0, rows-1), np.clip(cc, 0, cols-1)] < z
            recv[:, k] = np.where(good, rr * cols + cc, -1).ravel()
            frac[:, k] = np.where(good, weights[k], 0.0).ravel()
        # Preserve the physically strongest receiver as the single extraction axis.
        kmax = np.argmax(frac, axis=1)
        main = recv[np.arange(N), kmax].reshape(rows, cols)
        return recv, frac, main

    if method == "demon":
        r1, r2, w1, w2, *_ = _demon_divergence_modulated_dinf(z, rx, ry)
        main = np.where((w2 > w1) & (r2 >= 0), r2, r1)
        recv[:, 0], recv[:, 1] = r1.ravel(), r2.ravel()
        frac[:, 0], frac[:, 1] = w1.ravel(), w2.ravel()
        return recv, frac, main

    raise ValueError("Metodo di deflusso non supportato: %s" % method)


def flow_direction_advanced(filled, rx, ry, method="dinf", seed=42, progress=None, check=None):
    """Build the principal receiver axis from the same routing graph used for accumulation."""
    progress = progress or _noop
    check = check or _noop
    if method not in FLOW_METHODS:
        raise ValueError("Metodo di deflusso non supportato: %s" % method)
    _, _, main = _routing_arrays(filled, rx, ry, method, seed=seed, exponent=1.0)
    progress(1.0)
    check()
    return main


def flow_accumulation(recv, valid, progress=None, check=None, filled=None,
                      rx=1.0, ry=1.0, method="d8", seed=42, exponent=1.0):
    """Mass-conserving upslope area using one generalized vectorized Kahn pass.

    Kahn's topological algorithm is applied to the routing DAG.  Edges are
    processed in frontiers rather than one Python iteration per raster cell;
    all eight possible outgoing edges of a frontier are accumulated with
    NumPy scatter-adds and indegree updates.
    """
    progress = progress or _noop
    check = check or _noop
    if filled is None:
        raise ValueError("filled richiesto")

    z = np.asarray(filled, dtype=float)
    v = np.asarray(valid, dtype=bool).ravel()
    N = z.size
    edge_dst, edge_w, main = _routing_arrays(
        z, rx, ry, method, seed=seed, exponent=exponent
    )
    active = edge_dst >= 0
    indeg = np.bincount(
        edge_dst[active].ravel(),
        minlength=N
    ).astype(np.int32)

    # A cell with no incoming edge is a Kahn source.  Invalid cells are
    # excluded from the graph.  Sources still contribute one cell area.
    valid_flat = v
    indeg[~valid_flat] = 0
    frontier = np.flatnonzero(valid_flat & (indeg == 0))

    acc = np.zeros(N, dtype=float)
    acc[valid_flat] = 1.0
    processed = 0
    total_valid = max(1, int(valid_flat.sum()))

    while frontier.size:
        check()
        processed += frontier.size
        if processed == frontier.size or (processed & 0x3FFF) < frontier.size:
            progress(min(0.99, processed / total_valid))

        dst = edge_dst[frontier].ravel()
        ww = edge_w[frontier].ravel()
        src_amount = np.repeat(acc[frontier], edge_dst.shape[1])
        ok = (dst >= 0) & (ww > 0) & valid_flat[np.clip(dst, 0, N - 1)]
        if np.any(ok):
            np.add.at(acc, dst[ok], src_amount[ok] * ww[ok])

        # Generalized Kahn: remove all outgoing edges of the current frontier
        # in one vectorized operation and enqueue newly zero-indegree nodes.
        good_edges = (dst >= 0) & valid_flat[np.clip(dst, 0, N - 1)]
        counts = np.bincount(dst[good_edges], minlength=N).astype(np.int32)
        indeg -= counts
        # Prevent re-enqueuing nodes that were already consumed.
        # A monotonically increasing 'seen' bitset is cheaper than per-cell sets.
        if 'done' not in locals():
            done = np.zeros(N, dtype=bool)
        done[frontier] = True
        frontier = np.flatnonzero((indeg == 0) & valid_flat & ~done)

    # The filled DEM should define an acyclic graph. If not, fail loudly rather
    # than silently returning a non-conservative accumulation.
    if int(done.sum()) < int(valid_flat.sum()):
        raise RuntimeError(
            "Routing graph non aciclico: il DEM riempito non garantisce un DAG."
        )

    progress(1.0)
    return acc.reshape(z.shape)


def channel_initiation_mask(acc, filled, rx, ry, recv, mode="area", threshold=0.05, n=1.0, m=2.0):
    """Compute a channel-initiation mask using published terrain criteria.

    area: A >= threshold [km²]
    slope_area: A^n * sin(beta)^m >= threshold, A in m²
    spi: a * tan(beta) >= threshold, a = A / local flow width [m]
    twi: ln(a / tan(beta)) >= threshold
    """
    valid=np.isfinite(filled)&np.isfinite(acc)
    A=np.maximum(acc,0.0)*(rx*ry)
    if mode=="area":
        return valid & (A >= float(threshold)*1e6)
    # Horn slope; DEMON aspect is handled by the same local terrain gradient.
    zp=np.pad(filled,1,mode="constant",constant_values=np.nan)
    e,w=zp[1:-1,2:],zp[1:-1,:-2]; n0,s0=zp[:-2,1:-1],zp[2:,1:-1]
    ne,nw,se,sw=zp[:-2,2:],zp[:-2,:-2],zp[2:,2:],zp[2:,:-2]
    with np.errstate(invalid="ignore",divide="ignore"):
        dzdx=((nw+2*w+sw)-(ne+2*e+se))/(8*rx)
        dzdy=((nw+2*n0+ne)-(sw+2*s0+se))/(8*ry)
    slope=np.hypot(dzdx,dzdy)
    beta=np.arctan(slope)
    # Local flow direction and rectangular-cell cross-sectional width.
    yy,xx=np.indices(filled.shape)
    rr=np.where(recv>=0,recv//filled.shape[1],yy); cc=np.where(recv>=0,recv%filled.shape[1],xx)
    vx=(cc-xx)*rx; vy=-(rr-yy)*ry
    norm=np.hypot(vx,vy)
    vx=np.divide(vx,norm,out=np.zeros_like(vx,dtype=float),where=norm>0)
    vy=np.divide(vy,norm,out=np.zeros_like(vy,dtype=float),where=norm>0)
    # Full cell width projected orthogonally to the local flow direction.
    width=np.abs(vy)*rx+np.abs(vx)*ry
    width=np.where(width>0,np.maximum(width,1e-12),math.sqrt(rx*ry))
    a=A/width
    tanb=np.tan(beta)
    if mode=="slope_area":
        S=np.sin(beta)
        return valid & np.isfinite(S) & ((a**float(n))*(S**float(m)) >= float(threshold))
    if mode=="spi":
        spi=a*tanb
        return valid & np.isfinite(spi) & (spi>=float(threshold))
    if mode=="twi":
        twi=np.full_like(a,np.nan,dtype=float)
        with np.errstate(divide="ignore",invalid="ignore"): twi=np.log(a/np.maximum(tanb,1e-12))
        return valid & np.isfinite(twi) & (twi>=float(threshold))
    raise ValueError("Criterio di innesco non supportato: %s"%mode)


# --------------------------------------------------------------------------
# 3. Estrazione reticolo e tracciamento segmenti
# --------------------------------------------------------------------------
def extract_network(recv, acc, threshold=None, check=None, filled=None, cell_area=None, stream_mask=None):
    """
    Estrae il reticolo mantenendo un asse principale continuo anche per i
    metodi a flusso frazionato.

    La soglia seleziona le celle-canale (accumulo * area >= soglia quando
    cell_area è fornita). Il tracciamento dell'asse NON si interrompe quando
    una cella intermedia è sotto soglia: si segue il ricevitore principale
    fino alla successiva cella-canale. Questo evita i buchi tipici di MFD,
    MD∞ e DEMON, dove una singola cella può ricevere solo una frazione del
    flusso principale.
    """
    check = check or _noop
    rows, cols = recv.shape
    N = rows * cols
    r = recv.ravel().astype(np.int64, copy=False)
    a = acc.ravel()

    if stream_mask is not None:
        stream = np.asarray(stream_mask, dtype=bool).ravel()
    elif threshold is not None:
        if cell_area is not None:
            stream = np.isfinite(a) & ((a * float(cell_area)) >= float(threshold))
        else:
            stream = np.isfinite(a) & (a >= float(threshold))
    else:
        raise ValueError("threshold o stream_mask richiesto")
    sidx = np.flatnonzero(stream)
    if sidx.size < 2:
        return None

    # next_stream[c] = prima cella-canale incontrata seguendo il ricevitore
    # principale. Per i metodi frazionati il ricevitore principale può passare
    # attraverso celle sotto soglia: il collegamento non deve interrompersi.
    next_stream = np.full(N, -1, dtype=np.int64)
    if filled is not None:
        z = filled.ravel()
        valid = np.isfinite(z) & (r >= 0)
        order = np.flatnonzero(np.isfinite(z))
        # Il ricevitore principale è sempre a quota inferiore; quindi
        # next_stream del ricevitore deve essere già noto. Elaboriamo dal
        # basso verso l'alto (quota crescente).
        order = order[np.argsort(z[order], kind="stable")]
        stream_flat = stream
        for j, idx in enumerate(order):
            if (j & 0x1FFFF) == 0:
                check()
            n = r[idx]
            if n < 0 or not valid[idx]:
                continue
            if stream_flat[n]:
                next_stream[idx] = n
            else:
                next_stream[idx] = next_stream[n]
    else:
        # fallback robusto senza quota: path compression iterativo.
        for idx in sidx:
            c = int(idx)
            seen = set()
            while c >= 0 and c not in seen:
                seen.add(c)
                n = int(r[c])
                if n < 0:
                    c = -1
                    break
                if stream[n]:
                    c = n
                    break
                c = n
            next_stream[idx] = c

    # Costruisce il grafo solo tra celle-canale. Il numero di ingressi è
    # quindi quello delle aste principali, non dei soli vicini immediati.
    dst = next_stream[sidx]
    ok = dst >= 0
    src_ok = sidx[ok]
    dst_ok = dst[ok]
    if src_ok.size == 0:
        return None
    indeg = np.bincount(dst_ok, minlength=N)
    junction = sidx[indeg[sidx] >= 2]
    source = sidx[indeg[sidx] == 0]

    # Anche una sorgente che confluisce direttamente in un'altra sorgente
    # viene mantenuta: in reti molto piccole è preferibile a perdere l'asta.
    starts = np.unique(np.concatenate([source, junction])).tolist()
    jset = set(junction.tolist())
    streamset = set(sidx.tolist())
    next_map = {int(s): int(next_stream[s]) for s in sidx if next_stream[s] >= 0}

    paths = []
    target_for = {}
    for i, s0 in enumerate(starts):
        if (i & 0x1FFF) == 0:
            check()
        s = int(s0)
        candidate = next_map.get(s, -1)
        # Un segmento si interrompe solo davanti a una confluenza (junction).
        # Le celle-canale ordinarie vengono attraversate senza creare segmenti
        # artificialmente corti: in questo modo l'asse principale resta continuo.
        target = candidate if candidate in jset else -1

        path = [s]
        c = s
        seen = {c}
        # Segui il ricevitore principale cella per cella, includendo le celle
        # sotto soglia come geometria di collegamento.
        while True:
            n = int(r[c]) if c >= 0 else -1
            if n < 0 or n in seen:
                break
            path.append(n)
            seen.add(n)
            c = n
            if c == target or c in jset:
                break
        if len(path) > 1:
            paths.append(path)
            target_for[len(paths) - 1] = target if target in jset else -1

    if not paths:
        return None

    # Associa l'estremo a valle al segmento che parte da quella cella-canale.
    by_from = {int(p[0]): i for i, p in enumerate(paths)}
    down = [-1] * len(paths)
    for i, pth in enumerate(paths):
        end_cell = int(pth[-1])
        d = by_from.get(end_cell, -1)
        # Se il path termina in una cella sotto soglia, cerca il primo nodo
        # canale attraversato (normalmente coincide con next_stream[start]).
        if d < 0:
            target = target_for.get(i, -1)
            d = by_from.get(target, -1)
        down[i] = d

    children = [[] for _ in paths]
    for i, d in enumerate(down):
        if d >= 0 and i != d:
            children[d].append(i)

    roots = [i for i, d in enumerate(down) if d < 0]
    topdown = []
    stack = list(reversed(roots))
    seen_seg = set()
    while stack:
        i = stack.pop()
        if i in seen_seg:
            continue
        seen_seg.add(i)
        topdown.append(i)
        stack.extend(reversed(children[i]))

    # In caso di nodi non raggiunti da un root (DEM/NoData particolari),
    # aggiungili comunque per non perdere geometrie.
    if len(topdown) < len(paths):
        topdown.extend(i for i in range(len(paths)) if i not in seen_seg)

    return {"paths": paths, "down": down, "children": children,
            "topdown": topdown, "roots": roots}


# --------------------------------------------------------------------------
# 4. Ordinamenti gerarchici
# --------------------------------------------------------------------------
def order_strahler(net):
    ch, td = net["children"], net["topdown"]
    o = [0] * len(ch)
    for i in reversed(td):
        c = ch[i]
        if not c:
            o[i] = 1
        else:
            mx = max(o[k] for k in c)
            cnt = sum(1 for k in c if o[k] == mx)
            o[i] = mx + 1 if cnt >= 2 else mx
    return o


def order_shreve(net):
    ch, td = net["children"], net["topdown"]
    o = [0] * len(ch)
    for i in reversed(td):
        c = ch[i]
        o[i] = 1 if not c else sum(o[k] for k in c)
    return o


def order_horton(net, strahler, key):
    """Horton: il ramo principale mantiene l'ordine massimo fino alla sorgente."""
    ch, td, down = net["children"], net["topdown"], net["down"]
    h = [0] * len(ch)
    for i in td:
        if down[i] < 0:
            h[i] = strahler[i]
        c = ch[i]
        if c:
            main = max(c, key=lambda k: (strahler[k], key[k]))
            for k in c:
                h[k] = h[i] if k == main else strahler[k]
    return h


def order_gravelius(net, key):
    """Gravelius/Hack: asta principale = 1, affluenti diretti = 2, ecc."""
    ch, td, down = net["children"], net["topdown"], net["down"]
    g = [0] * len(ch)
    for i in td:
        if down[i] < 0:
            g[i] = 1
        c = ch[i]
        if c:
            main = max(c, key=lambda k: key[k])
            for k in c:
                g[k] = g[i] if k == main else g[i] + 1
    return g


def order_topological(net):
    """Ordine topologico: numero di segmenti tra il tratto e lo sbocco (+1)."""
    ch, td, down = net["children"], net["topdown"], net["down"]
    t = [0] * len(ch)
    for i in td:
        if down[i] < 0:
            t[i] = 1
        for k in ch[i]:
            t[k] = t[i] + 1
    return t


# --------------------------------------------------------------------------
# 5. Smussatura
# --------------------------------------------------------------------------
def gaussian_smooth(xy, sigma):
    """Media mobile gaussiana con estremi bloccati (riflessione puntuale)."""
    n = len(xy)
    if n < 3 or sigma <= 0:
        return xy
    rad = max(1, int(round(3.0 * sigma)))
    rad = min(rad, n - 1)
    x = np.arange(-rad, rad + 1, dtype=np.float64)
    k = np.exp(-0.5 * (x / sigma) ** 2)
    k /= k.sum()
    left = 2.0 * xy[0] - xy[rad:0:-1]
    right = 2.0 * xy[-1] - xy[-2:-rad - 2:-1]
    pad = np.vstack([left, xy, right])
    out = np.empty_like(xy)
    for j in range(2):
        out[:, j] = np.convolve(pad[:, j], k, mode="valid")
    out[0] = xy[0]
    out[-1] = xy[-1]
    return out


def chaikin(xy, iterations):
    for _ in range(int(iterations)):
        if len(xy) < 3:
            break
        p0, p1 = xy[:-1], xy[1:]
        q = 0.75 * p0 + 0.25 * p1
        r = 0.25 * p0 + 0.75 * p1
        new = np.empty((2 * len(q), 2))
        new[0::2] = q
        new[1::2] = r
        xy = np.vstack([xy[:1], new, xy[-1:]])
    return xy


def catmull_rom(xy, subdiv):
    subdiv = int(subdiv)
    n = len(xy)
    if n < 3 or subdiv < 1:
        return xy
    P = np.vstack([xy[:1], xy, xy[-1:]])
    p0, p1, p2, p3 = P[:-3], P[1:-2], P[2:-1], P[3:]
    t = (np.arange(subdiv, dtype=np.float64) / subdiv)[None, :, None]
    p0, p1, p2, p3 = (a[:, None, :] for a in (p0, p1, p2, p3))
    pts = 0.5 * ((2 * p1)
                 + (-p0 + p2) * t
                 + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                 + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)
    pts = pts.reshape(-1, 2)
    return np.vstack([pts, xy[-1:]])


SMOOTH_METHODS = ("none", "natural", "gauss", "chaikin", "spline")


def smooth_line(xy, method, strength=2.0, density=3):
    """
    method  : none | natural (gauss + spline) | gauss | chaikin | spline
    strength: sigma (in vertici) della gaussiana / n. iterazioni Chaikin
    density : suddivisioni per tratto della spline
    """
    xy = np.asarray(xy, dtype=np.float64)
    if method == "none" or len(xy) < 3:
        return xy
    if method == "gauss":
        return gaussian_smooth(xy, strength)
    if method == "chaikin":
        return chaikin(xy, max(1, int(round(strength))))
    if method == "spline":
        return catmull_rom(xy, density)
    # natural
    return catmull_rom(gaussian_smooth(xy, strength), density)


def demo_staircase():
    """Percorso D8 'a gradini' di esempio per l'anteprima (coordinate 0..1)."""
    cells = []
    prev = None
    for x in range(0, 41):
        y = int(round(7 + 4.5 * math.sin(x / 40.0 * 2 * math.pi * 1.4) + 1.5 * math.sin(x * 0.9)))
        if prev is not None:
            step = 1 if y > prev else -1
            for yy in range(prev + step, y, step):
                cells.append((x, yy))
        cells.append((x, y))
        prev = y
    a = np.array(cells, dtype=np.float64)
    a[:, 0] /= 40.0
    a[:, 1] = a[:, 1] / 14.0
    return a
