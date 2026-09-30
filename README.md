# HydroNet Studio

Plugin for **QGIS 4.x (Qt6)** for hydrological analysis and hydrographic-network extraction from DTM/DEM data.

HydroNet Studio combines **Priority-Flood** elevation preprocessing, six flow-routing models — **D8, D∞, Rho8, MFD, MD∞, and DEMON stream-tube** — and configurable channel-initiation criteria based on **contributing area, slope–area relationships, SPI, and TWI**.

The engine preserves routing consistency for fractional-flow methods by separating flow accumulation from subsequent vector-network extraction. The resulting network can be analyzed using several hierarchical stream-ordering methods and automatically styled according to network hierarchy.

---

## Main features

* **Priority-Flood elevation preprocessing** to remove non-draining topographic depressions and produce a hydrologically consistent elevation surface.
* Six flow-routing models:

  * **D8**
  * **D∞ (D-Infinity)**
  * **Rho8**
  * **MFD (Multiple Flow Direction)**
  * **MD∞ (Multiple-Direction D-Infinity)**
  * **DEMON stream-tube**, using the conservative HydroNet formulation.
* Network extraction using four configurable channel-initiation criteria:

  * **minimum contributing area**;
  * **slope–area relationship**;
  * **Stream Power Index (SPI)**;
  * **Topographic Wetness Index (TWI)**.
* Conservative fractional routing: each cell distributes its contribution according to the fractions defined by the selected model, without introducing additional receivers during accumulation.
* Fractional-flow methods preserve a **continuous main channel axis** for vector-network construction, independently from the raster routing used for flow accumulation.
* Flow accumulation through a **vectorized routing graph and frontier-based generalized Kahn algorithm**, eliminating the previous Python cell-by-cell accumulation loop.
* Mass-conservation checks: routing fractions are normalized so that the total contribution transferred by each cell is conserved.
* Hierarchical stream ordering using:

  * **Strahler**;
  * **Shreve**;
  * **Horton**;
  * **Gravelius/Hack**;
  * **Topological ordering**.
* Multiple ordering methods can be calculated simultaneously; each selected method produces a dedicated attribute field.
* **Automatic network styling** according to hierarchical order, with configurable line width and color.
* Automatic styling can be applied both to newly extracted networks and to existing line layers.
* Optional geometry smoothing using:

  * Gaussian filtering;
  * Chaikin;
  * Catmull–Rom splines;
  * **Natural** combined smoothing.
* Confluences are preserved topologically during geometry generation.
* Modern, independent GUI: **non-dockable and non-modal**, organized into dedicated panels.
* Processing runs in a **background thread**, keeping the QGIS interface responsive while displaying progress.
* The plugin does not modify the main QGIS window: it does not create permanent docks or panels and only adds a toolbar button and a plugin-menu entry.
* Available in **Italian and English**, with automatic detection of the QGIS language and Italian fallback.

---

## Installation

1. Compress the `hydronet_studio` folder into a `.zip` archive.

2. The `hydronet_studio` folder must be located directly at the **root of the ZIP archive**.

3. In QGIS, open:

   **Plugins → Manage and Install Plugins → Install from ZIP**

4. Select the ZIP archive.

5. Enable **HydroNet Studio** in the installed plugins list.

After installation, **HydroNet Studio…** will be available from the plugin menu and toolbar.

---

## Requirements

* **QGIS 4.x**
* Python and **Qt6** provided by QGIS.
* **GDAL/OGR** and **NumPy**, normally included with QGIS.

No separate Python installation is required for the standard dependencies used by the plugin.

---

# Flow-routing models

## D8 — O'Callaghan & Mark (1984)

D8 is a **deterministic single-flow-direction** method.

For each cell, the neighboring cell with the greatest positive downslope gradient is selected among the eight cardinal and diagonal neighbors. The entire contribution of the cell is then transferred to that single receiver.

The slope calculation accounts for the actual distance between cell centers. For a square grid, diagonal directions therefore use a distance equal to `√2` times the cell size.

The resulting routing field is discrete and convergent, with at most one receiver per cell.

---

## D∞ — Tarboton (1997)

D∞ represents flow direction as a **continuous angle**, rather than restricting it to the eight grid directions.

For each cell, the eight triangular facets formed by the central cell and two adjacent neighbors are considered. A local plane is defined for each facet and its direction of maximum downslope is computed.

The valid facet is selected according to the maximum downslope gradient, and the resulting direction may take any angle within that facet.

When the direction lies between the two vertices of the facet, the contribution is divided between those **two receivers only**, according to the angular position of the continuous flow direction relative to the facet boundaries.

The raster routing therefore preserves the original D∞ fractions.

For vector-network construction, a principal receiver consistent with the continuous direction is identified separately, without modifying the fractions used by flow accumulation.

---

## Rho8 — Fairfield & Leymarie (1991)

Rho8 is a **stochastic single-flow-direction** extension of the D8 family.

Among downslope neighboring cells, eligible receivers are considered and their selection probabilities are determined from local slope, giving steeper directions a higher probability of being selected.

Once the random realization has been generated, **100% of the cell contribution** is transferred to the selected receiver.

The pseudo-random realization is controlled by a configurable **seed**, allowing the same calculation to be reproduced.

No arbitrary empirical power is applied to the slope in the probability calculation.

---

## MFD — Quinn et al. (1991)

MFD distributes flow among multiple downslope neighboring cells.

For each receiver `i`, the routing fraction is calculated as:

```text
f_i = [tan(β_i)^p L_i] / Σ[tan(β_j)^p L_j]
```

where:

* `β_i` is the slope angle toward receiver `i`;
* `p` is the distribution exponent;
* `L_i` is the effective contour length associated with the flow direction;
* the summation is performed over all eligible receivers.

The reference formulation used by the plugin uses `p = 1`.

For a square grid, effective contour lengths associated with cardinal and diagonal directions are represented by `0.5` and `0.354` times the cell size, respectively.

Including `L_i` prevents cardinal and diagonal directions from being treated as having identical effective contour widths.

The resulting fractions are normalized so that:

```text
Σ f_i = 1
```

thereby conserving the contribution during flow accumulation.

---

## MD∞ — Seibert & McGlynn (2007)

MD∞ extends the continuous-direction concept of D∞ by allowing flow to be distributed among multiple admissible directions.

The calculation considers the local triangular facets of the grid and combines:

1. facet slope;
2. continuous flow direction;
3. angular position relative to neighboring cells;
4. the adjacency rules defined by the method.

The method is therefore not obtained simply by applying an additional dispersion factor to D∞.

Directions are constructed from the local facet geometry and the resulting fractions are normalized to preserve the cell contribution.

This allows multi-directional flow to be represented while avoiding some of the excessive dispersion that can occur with purely neighbor-based MFD routing.

---

## DEMON — conservative D∞-based variant

HydroNet does not implement DEMON as a simple cell-by-cell tracer that creates additional geometric branches.

The implemented formulation starts from the **D∞ flow field** and preserves exactly the pair of receiving cells identified by the D∞ triangular facet.

Only the ratio between the two routing fractions is then modified according to a local measure of **flow-field convergence/divergence**.

Conceptually:

* convergence tends to concentrate the contribution;
* divergence tends to make the distribution more even;
* the receiver pair is not changed;
* no additional routing branches are created;
* the two fractions are always renormalized so that their sum is one.

This prevents the redistribution mechanism from progressively generating additional receivers along long flow paths and therefore limits cumulative dispersion.

This formulation is specific to the HydroNet engine and should be regarded as a **conservative DEMON-inspired variant**, rather than a literal reproduction of every implementation detail of the original DEMON model.

---

# Flow accumulation

Flow accumulation is computed from the directed routing graph generated by the selected flow model.

Each cell represents a graph node, while each fractional flow transfer to a receiving cell represents a weighted directed edge.

The engine uses a **frontier-based generalized Kahn algorithm**:

1. the number of incoming edges is computed for each node;
2. cells with no unresolved upstream dependencies are identified;
3. available cells are processed by frontier;
4. their accumulated contribution is transferred to receivers using vectorized operations;
5. predecessor counts are updated in blocks;
6. cells whose predecessor count reaches zero are added to the next frontier.

No independent Python loop is therefore executed for every raster cell.

Routing remains restricted to the local grid neighborhood. Each cell can have at most eight receivers, and outgoing fractions are normalized so that the total transferred contribution is conserved.

The resulting accumulation can be interpreted as:

```text
A = accumulated surface-flow contribution
```

and is converted to physical contributing area by multiplying by the actual cell area.

---

# Channel-initiation criteria

Routing and network initiation are treated as two separate operations.

**Routing** determines where flow is transferred.

The **channel-initiation criterion** determines which cells are considered part of the extracted network based on the calculated hydrological or topographic quantities.

HydroNet supports four criteria.

---

## 1. Minimum contributing area

```text
A ≥ A_min
```

where `A` is the upstream contributing area.

The threshold is expressed in **km²**.

The area is calculated from raster flow accumulation multiplied by the physical cell area. In fractional-flow methods the accumulation may be non-integer while retaining the same physical interpretation.

This criterion is particularly direct when channel initiation is defined in terms of a minimum contributing catchment area.

---

## 2. Slope–area relationship

The plugin supports the general form:

```text
a^n · S^m ≥ T
```

where:

* `a` is specific contributing area;
* `S` is slope;
* `n` and `m` are the relationship exponents;
* `T` is the initiation threshold.

In the implemented formulation, slope may be expressed as:

```text
S = sin(β)
```

according to the definition used by the engine.

The case `n = 1`, `m = 2` represents one configuration within the broader family of slope–area relationships commonly used for channel-initiation analysis.

The parameters are not assumed to be universal. Appropriate thresholds depend on terrain, material, vegetation, climate, and the dominant geomorphic process.

---

## 3. SPI — Stream Power Index

```text
SPI = a · tan(β)
```

where:

* `a` is specific contributing area;
* `β` is the slope angle.

SPI is a topographic index associated with flow concentration and the potential capacity of concentrated runoff to perform geomorphic work.

It should not be interpreted as a universal incision law or as a context-independent physical threshold.

HydroNet calculates specific contributing area using the effective local flow width associated with the principal flow direction.

---

## 4. TWI — Topographic Wetness Index

```text
TWI = ln(a / tan(β))
```

where:

* `a` is specific contributing area;
* `β` is slope.

TWI is a topographic index of potential water accumulation and saturation.

A TWI threshold therefore identifies areas that are topographically predisposed to saturation or flow concentration, rather than defining a universal physical law of channel formation.

---

# Network threshold

The network threshold can be defined using:

* **Contributing area**
* **Slope–area**
* **SPI**
* **TWI**

Changing the threshold criterion does not modify the flow-routing field or flow accumulation. It modifies the **channel-initiation mask** used to identify cells belonging to the extracted network.

Threshold units depend on the selected criterion.

In particular:

* contributing area is expressed in `km²`;
* slope–area uses the variables and exponents defined by the selected formulation;
* SPI and TWI retain their respective mathematical definitions and are not artificially converted into area thresholds.

This keeps the physical meaning of each quantity separate from the network-extraction threshold.

---

# Network extraction

After flow accumulation has been computed, the selected channel-initiation mask is applied.

For single-flow methods, the downstream path is directly determined by the single receiver.

For fractional-flow methods, raster routing may involve multiple receivers, while vector-network construction uses a **continuous principal channel axis** selected consistently with the dominant flow direction.

This separation is intentional:

* **flow accumulation** preserves the fractional behavior of the routing model;
* **vector extraction** constructs a continuous line network;
* network geometry does not modify the underlying flow balance.

In particular, vector extraction does not introduce a second flow redistribution step or add receivers to the accumulation graph.

---

# Stream ordering

HydroNet can calculate multiple stream-ordering systems simultaneously.

### Strahler

Tributaries of the same order retain that order; when two streams of the same order merge, the downstream order increases by one.

### Shreve

Each segment receives a **magnitude** equal to the sum of the magnitudes of its upstream tributaries.

### Horton

The hierarchy is determined from stream classification and main-stem continuity.

### Gravelius/Hack

The main channel is identified and followed according to network structure and channel length.

### Topological

An order is assigned according to the position of each segment within the directed topology of the network.

Each selected ordering method generates a dedicated attribute field.

---

# Geometry smoothing

Smoothing is applied **after** the network topology has been constructed.

Available methods include:

* Gaussian filtering;
* Chaikin;
* Catmull–Rom splines;
* **Natural** combined smoothing.

Smoothing modifies the cartographic geometry but does not alter:

* flow routing;
* flow accumulation;
* channel-initiation criteria;
* stream ordering;
* network topology.

Confluences are kept consistent with the network structure during geometry generation.

---

# Automatic styling

HydroNet can automatically style network lines according to hierarchical order.

The style can use:

* increasing line width with stream order;
* graduated colors;
* configurable visual parameters.

Automatic styling can be applied both to:

1. the newly generated network layer;
2. an existing line layer already present in the QGIS project.

---

# Interface and processing

HydroNet Studio uses an independent **non-modal, non-dockable** window.

Users can therefore continue working in the QGIS project while the plugin interface remains open.

Computationally intensive processing runs in a **dedicated background thread**.

During processing:

* the main interface remains responsive;
* progress is displayed continuously;
* processing status can be updated without blocking QGIS;
* the progress indicator is reset when processing finishes.

The plugin does not create permanent QGIS docks or modify the main QGIS window.

---

# Output

The extracted network layer may contain attributes including:

* `seg_id` — segment identifier;
* `down_id` — downstream segment;
* `n_monte` — number of upstream segments;
* `flow_alg` — routing algorithm;
* `lunghezza_m` — segment length;
* `area_km2` — contributing area;
* `quota_monte` — upstream elevation;
* `quota_valle` — downstream or confluence elevation;
* `pendenza_pc` — percentage slope;
* fields corresponding to the selected stream-ordering methods.

Optionally, the processing workflow can also export:

* **filled/corrected DEM**;
* **flow-accumulation raster**;
* other intermediate raster products supported by the workflow.

---

# Translations

Qt Linguist translation source files are stored in:

```text
i18n/*.ts
```

The compiled translation files included with the plugin are:

```text
i18n/hydronet_studio_en.qm
i18n/hydronet_studio_it.qm
```

After modifying translatable strings, the English translation can be regenerated with:

```bash
pylupdate6 dialog.py worker.py styler.py plugin.py \
    -ts i18n/hydronet_studio_en.ts

lrelease i18n/hydronet_studio_en.ts
```

---

# Methodological references

The principal formulations used by the engine are based on:

* **O'Callaghan, J.F. & Mark, D.M. (1984)** — D8 drainage-direction analysis;
* **Fairfield, J. & Leymarie, P. (1991)** — Rho8;
* **Quinn et al. (1991)** — Multiple Flow Direction;
* **Tarboton, D.G. (1997)** — D-Infinity;
* **Seibert, J. & McGlynn, B. (2007)** — MD∞;
* DEMON/stream-tube literature concerning the representation of flow convergence and divergence.

The formulations implemented by HydroNet should be distinguished from later software-specific variants and simplified approximations found in other GIS implementations.

---

# Interfaces

<img width="949" height="914" alt="img1" src="https://github.com/user-attachments/assets/3ecec7f9-ad14-4e4d-9068-6acf3f67c9d4" />

<img width="947" height="914" alt="img2" src="https://github.com/user-attachments/assets/ed0b99f3-f578-497e-870e-fa767f7ce1de" />

<img width="950" height="917" alt="img3" src="https://github.com/user-attachments/assets/117c8986-6056-4a0e-bf3d-60e34f7a43ea" />

<img width="1602" height="959" alt="img4" src="https://github.com/user-attachments/assets/624c1790-4205-4804-a3ec-83504de434d7" />
