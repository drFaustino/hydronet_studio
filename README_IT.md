# HydroNet Studio

Plugin per **QGIS 4.x (Qt6)** per l’analisi idrologica e l’estrazione di reticoli idrografici da DTM/DEM.

HydroNet Studio combina il pretrattamento altimetrico **Priority-Flood**, sei modelli di instradamento del deflusso — **D8, D∞, Rho8, MFD, MD∞ e DEMON stream-tube** — e criteri configurabili di innesco dei canali basati su **area drenata, relazione pendenza–area, SPI e TWI**.

Il motore mantiene la coerenza topologica del routing anche nei metodi a flusso frazionato, separando il calcolo dell’accumulo dalla successiva estrazione del reticolo. Il risultato può essere ordinato secondo diversi metodi gerarchici e rappresentato automaticamente con larghezze e stili coerenti con l’ordine del reticolo.

---

## Funzionalità principali

* **Pretrattamento altimetrico Priority-Flood** per eliminare le depressioni topografiche non drenanti e costruire un campo altimetrico coerente con il routing.
* Sei modelli di deflusso:

  * **D8**
  * **D∞ (D-Infinity)**
  * **Rho8**
  * **MFD (Multiple Flow Direction)**
  * **MD∞ (Multiple-Direction D-Infinity)**
  * **DEMON stream-tube**, nella variante conservativa implementata da HydroNet.
* Estrazione del reticolo mediante quattro criteri configurabili di innesco:

  * **area drenata minima**;
  * **relazione pendenza–area**;
  * **Stream Power Index (SPI)**;
  * **Topographic Wetness Index (TWI)**.
* Routing frazionato conservativo: ogni cella distribuisce il proprio contributo secondo le frazioni definite dal modello, senza introdurre ricevitori aggiuntivi durante l’accumulo.
* Nei metodi a flusso frazionato viene mantenuto un **asse principale continuo** per la costruzione del reticolo vettoriale, distinto dal routing raster utilizzato per l’accumulo.
* Accumulo del deflusso mediante **grafo vettorializzato e Kahn generalizzato a frontiere**, evitando il precedente ciclo Python cella-per-cella.
* Controllo della conservazione della massa: le frazioni di routing sono normalizzate e la somma del contributo trasferito da ciascuna cella è conservata.
* Ordinamento gerarchico del reticolo con:

  * **Strahler**;
  * **Shreve**;
  * **Horton**;
  * **Gravelius/Hack**;
  * **Topologico**.
* Possibilità di calcolare contemporaneamente più ordinamenti; ogni metodo selezionato viene scritto in un campo dedicato della tabella attributi.
* **Stile automatico** del reticolo in funzione dell’ordine gerarchico, con larghezza e colore configurabili.
* Applicazione dello stile sia al risultato appena estratto sia a un layer lineare già presente nel progetto.
* Smussatura opzionale delle geometrie mediante:

  * filtro gaussiano;
  * Chaikin;
  * spline Catmull–Rom;
  * combinazione **Naturale**.
* Le confluenze vengono preservate topologicamente durante la costruzione delle geometrie.
* Interfaccia grafica indipendente, **non ancorabile e non modale**, organizzata in pannelli.
* Elaborazione in **thread separato**, con aggiornamento dello stato di avanzamento senza bloccare l’interfaccia di QGIS.
* Il plugin non modifica la finestra principale di QGIS: non introduce dock o pannelli permanenti e aggiunge soltanto il comando nella toolbar e nel menu dei plugin.
* Interfaccia disponibile in **italiano e inglese**, con rilevamento automatico della lingua di QGIS e fallback all’italiano.

---

## Installazione

1. Comprimi la cartella `hydronet_studio` in un file `.zip`.

2. La cartella `hydronet_studio` deve essere direttamente alla **radice dell’archivio ZIP**.

3. In QGIS apri:

   **Plugin → Gestisci e installa plugin → Installa da ZIP**

4. Seleziona l’archivio ZIP.

5. Attiva **HydroNet Studio** nell’elenco dei plugin installati.

Dopo l’installazione, il comando **HydroNet Studio…** sarà disponibile nel menu dei plugin e nella toolbar.

---

## Requisiti

* **QGIS 4.x**
* Python e **Qt6** forniti da QGIS.
* **GDAL/OGR** e **NumPy**, normalmente già inclusi nella distribuzione QGIS.

Non sono richieste installazioni Python separate per le dipendenze standard utilizzate dal plugin.

---

# Modelli di deflusso

## D8 — O'Callaghan & Mark (1984)

D8 è un metodo **single-flow-direction deterministico**.

Per ogni cella viene individuato il vicino con la maggiore pendenza positiva in discesa fra gli otto vicini della griglia. L'intero contributo della cella viene quindi trasferito a un solo ricevitore.

La pendenza viene calcolata tenendo conto della distanza effettiva fra le celle: per una griglia quadrata le direzioni diagonali hanno distanza `√2` volte la dimensione della cella.

Il modello produce un campo di direzione discreto e convergente, nel quale ogni cella possiede al massimo un ricevitore.

---

## D∞ — Tarboton (1997)

D∞ rappresenta la direzione di deflusso come un **angolo continuo**, anziché vincolarla alle otto direzioni cardinali e diagonali.

Per ciascuna cella vengono considerate le otto faccette triangolari formate dal centro della cella e da due vicini adiacenti. Su ciascuna faccetta viene determinato il piano locale e la corrispondente direzione di massima discesa.

La faccetta valida viene selezionata sulla base della massima pendenza e la direzione risultante può assumere qualsiasi angolo all'interno della faccetta.

Quando la direzione cade fra i due vertici della faccetta, il contributo viene ripartito fra quei **due soli ricevitori**, secondo la posizione angolare della direzione rispetto ai lati della faccetta.

Il routing raster conserva quindi le frazioni D∞ originali.

Per la costruzione del reticolo vettoriale viene inoltre identificato un asse principale coerente con la direzione continua, senza modificare le frazioni utilizzate dall'accumulo.

---

## Rho8 — Fairfield & Leymarie (1991)

Rho8 è una variante **stocastica single-flow-direction** della famiglia D8.

Fra i vicini a quota inferiore vengono considerati i ricevitori ammissibili. La probabilità di selezione è determinata in funzione della pendenza locale, così che le direzioni più ripide abbiano maggiore probabilità di essere selezionate.

Una volta effettuata l'estrazione, il **100% del contributo** della cella viene trasferito al singolo ricevitore selezionato.

La realizzazione pseudo-casuale è controllata da un **seed configurabile**, rendendo possibile ripetere esattamente lo stesso calcolo.

Non viene introdotta alcuna potenza empirica arbitraria della pendenza nel calcolo delle probabilità.

---

## MFD — Quinn et al. (1991)

MFD distribuisce il deflusso fra più vicini a quota inferiore.

Per ciascun ricevitore `i`, la frazione viene calcolata come:

```text
f_i = [tan(β_i)^p L_i] / Σ[tan(β_j)^p L_j]
```

dove:

* `β_i` è l'angolo di pendenza verso il ricevitore `i`;
* `p` è l'esponente della distribuzione;
* `L_i` è la lunghezza di contorno efficace associata alla direzione;
* la somma è estesa a tutti i ricevitori ammissibili.

Nella formulazione di riferimento utilizzata dal plugin, `p = 1`.

Per una griglia quadrata vengono utilizzate le lunghezze di contorno efficaci associate alle direzioni cardinali e diagonali, rispettivamente `0,5` e `0,354` volte la dimensione della cella.

L'introduzione di `L_i` evita di trattare cardinali e diagonali come se avessero la stessa larghezza efficace di contorno.

Le frazioni vengono successivamente normalizzate in modo che:

```text
Σ f_i = 1
```

garantendo la conservazione del contributo durante l'accumulo.

---

## MD∞ — Seibert & McGlynn (2007)

MD∞ estende il concetto di direzione continua di D∞ consentendo una distribuzione del deflusso fra più direzioni ammissibili.

Il calcolo considera le faccette triangolari locali della griglia e combina:

1. la pendenza delle faccette;
2. la direzione continua del deflusso;
3. la posizione angolare rispetto ai vicini;
4. le regole di adiacenza previste dal metodo.

Il routing non viene quindi ottenuto applicando semplicemente un fattore di dispersione al D∞.

Le direzioni vengono costruite a partire dalla geometria locale delle faccette e le frazioni vengono normalizzate per garantire la conservazione del contributo.

Il metodo può quindi rappresentare distribuzioni multi-direzionali in modo più controllato rispetto a un MFD puramente basato sui vicini a quota inferiore.

---

## DEMON — variante conservativa basata su D∞

HydroNet non implementa DEMON come un semplice tracer cella-per-cella con nuove diramazioni geometriche.

La variante utilizzata dal motore parte dal **campo D∞** e conserva esattamente la coppia di celle riceventi individuata dal triangolo D∞.

Il rapporto fra le due frazioni viene quindi modulato mediante una misura locale della **convergenza/divergenza del campo di deflusso**.

In termini qualitativi:

* la convergenza tende a concentrare maggiormente il contributo;
* la divergenza tende a rendere più uniforme la ripartizione;
* la coppia di ricevitori non cambia;
* non vengono creati nuovi rami di routing;
* le due frazioni vengono sempre rinormalizzate affinché la loro somma sia pari a uno.

Questa formulazione impedisce che la ridistribuzione produca una proliferazione progressiva di ricevitori lungo il percorso e limita quindi la dispersione cumulativa del contributo.

La formulazione è specifica del motore HydroNet e deve essere considerata una **variante conservativa ispirata al principio DEMON**, non una riproduzione letterale di ogni dettaglio del modello DEMON originale.

---

# Accumulo del deflusso

L'accumulo viene calcolato a partire dal grafo diretto generato dal routing.

Ogni cella costituisce un nodo e ogni frazione di deflusso verso una cella ricevente costituisce un arco pesato.

Il motore utilizza un **Kahn generalizzato a frontiere**:

1. viene calcolato il numero di predecessori di ciascun nodo;
2. vengono individuate le celle senza contributi entranti;
3. le celle disponibili vengono elaborate per frontiere;
4. il contributo accumulato viene trasferito ai ricevitori mediante operazioni vettoriali;
5. il conteggio dei predecessori viene aggiornato in blocco;
6. le celle che raggiungono zero predecessori entrano nella frontiera successiva.

Non viene quindi eseguito un ciclo Python indipendente per ogni cella.

Il routing resta limitato ai vicini della griglia e ciascuna cella può avere al massimo otto ricevitori. Le frazioni uscenti vengono normalizzate e la massa viene conservata.

L'accumulo raster può essere interpretato come:

```text
A = accumulo del contributo superficiale
```

e viene successivamente convertito in area fisica mediante l'area reale della cella.

---

# Criteri di innesco dei canali

Il routing e l'innesco del reticolo sono due operazioni distinte.

Il **routing** stabilisce dove viene trasferito il deflusso.

Il **criterio di innesco** stabilisce quali celle, sulla base delle grandezze idrologiche o topografiche calcolate, vengono considerate appartenenti al reticolo.

Il plugin supporta quattro criteri.

---

## 1. Area drenata minima

```text
A ≥ A_min
```

dove `A` è l'area contribuente a monte.

La soglia viene espressa in **km²**.

L'area viene calcolata dall'accumulo raster moltiplicato per l'area reale della cella. Nei modelli a flusso frazionato l'accumulo può assumere valori non interi, senza perdere il proprio significato fisico.

Questo criterio è particolarmente diretto quando la soglia di formazione del reticolo è definita in termini di bacino contribuente minimo.

---

## 2. Relazione pendenza–area

Il plugin supporta una forma generale della relazione:

```text
a^n · S^m ≥ T
```

dove:

* `a` è l'area contribuente specifica;
* `S` è la pendenza;
* `n` e `m` sono gli esponenti della relazione;
* `T` è la soglia di innesco.

Nella formulazione implementata la pendenza utilizzata può essere espressa come:

```text
S = sin(β)
```

secondo la definizione adottata dal motore.

Il caso `n = 1`, `m = 2` costituisce una configurazione della famiglia delle relazioni pendenza–area frequentemente utilizzate per l'individuazione dell'innesco dei canali.

I parametri non devono essere considerati universali: la soglia effettiva dipende dalle caratteristiche del territorio, dal materiale, dalla vegetazione, dal clima e dal processo geomorfologico dominante.

---

## 3. SPI — Stream Power Index

```text
SPI = a · tan(β)
```

dove:

* `a` è l'area contribuente specifica;
* `β` è l'angolo di pendenza.

Lo SPI rappresenta un indice topografico associato alla concentrazione del deflusso e alla capacità potenziale del flusso di esercitare lavoro sul versante o sull'alveo.

Non deve essere interpretato come una legge universale di incisione o come una soglia fisica indipendente dal contesto.

HydroNet calcola l'area contribuente specifica tenendo conto della larghezza locale efficace associata al percorso di deflusso.

---

## 4. TWI — Topographic Wetness Index

```text
TWI = ln(a / tan(β))
```

dove:

* `a` è l'area contribuente specifica;
* `β` è la pendenza.

Il TWI è un indice topografico del potenziale accumulo d'acqua e della predisposizione alla saturazione.

Una soglia TWI identifica quindi aree topograficamente predisposte alla concentrazione o alla saturazione, ma non costituisce una legge universale di formazione dei canali.

---

# Soglia del reticolo

La soglia del reticolo può essere definita mediante:

* **Area drenata**
* **Pendenza–area**
* **SPI**
* **TWI**

La scelta del criterio non modifica il campo di routing né il calcolo dell'accumulo: modifica la **maschera di innesco** utilizzata per identificare le celle appartenenti alla rete.

Le unità della soglia dipendono dal criterio scelto.

In particolare:

* l'area drenata è espressa in `km²`;
* la relazione pendenza–area utilizza le grandezze e gli esponenti definiti dalla relativa formulazione;
* SPI e TWI mantengono le proprie definizioni matematiche e non vengono convertiti artificialmente in soglie di area.

Questo mantiene separati il significato fisico delle variabili e quello della soglia di estrazione.

---

# Estrazione del reticolo

Dopo il calcolo dell'accumulo viene applicata la maschera di innesco.

Nei metodi single-flow il percorso è direttamente determinato dal singolo ricevitore.

Nei metodi a flusso frazionato il routing raster può coinvolgere più ricevitori, ma la costruzione del reticolo vettoriale utilizza un **asse principale continuo**, selezionato coerentemente con la direzione dominante del flusso.

Questa separazione è intenzionale:

* l'**accumulo** conserva il comportamento frazionato del modello;
* l'**estrazione vettoriale** costruisce una rete lineare continua;
* la geometria del reticolo non modifica retroattivamente il bilancio del routing.

In particolare, l'estrazione non introduce una nuova redistribuzione del flusso né aggiunge ricevitori al grafo di accumulo.

---

# Ordinamento gerarchico

HydroNet può calcolare contemporaneamente più sistemi di ordinamento.

### Strahler

Assegna lo stesso ordine ai tributari dello stesso ordine; quando due tributari dello stesso ordine confluiscono, l'ordine aumenta di uno.

### Shreve

Attribuisce a ciascun segmento una **magnitudo** pari alla somma delle magnitudo dei tributari che lo alimentano.

### Horton

Ricostruisce la gerarchia secondo la classificazione e la continuità dell'asta principale.

### Gravelius/Hack

Identifica e segue l'asta principale sulla base della struttura e della lunghezza del reticolo.

### Topologico

Assegna un ordine basato sulla posizione del segmento all'interno della struttura diretta della rete.

Ogni metodo selezionato produce un proprio campo nella tabella attributi.

---

# Smussatura delle geometrie

La smussatura viene applicata **dopo** la costruzione topologica della rete.

Sono disponibili:

* filtro gaussiano;
* Chaikin;
* spline Catmull–Rom;
* combinazione **Naturale**.

La smussatura agisce sulla geometria cartografica e non modifica il routing raster, l'accumulo o la gerarchia topologica.

Le confluenze vengono mantenute coerenti con la struttura della rete durante la generazione delle geometrie.

---

# Stile automatico

Il plugin può assegnare automaticamente lo stile alle linee in funzione dell'ordine gerarchico.

Lo stile può utilizzare:

* larghezza crescente con l'ordine;
* colore graduato;
* parametri configurabili dall'utente.

L'applicazione dello stile è disponibile sia per:

1. il layer appena prodotto;
2. un layer lineare già presente nel progetto QGIS.

---

# Interfaccia ed elaborazione

HydroNet Studio utilizza una finestra grafica indipendente, **non modale e non ancorabile**.

È quindi possibile continuare a lavorare nel progetto QGIS mentre il pannello del plugin rimane aperto.

Le elaborazioni numericamente intensive vengono eseguite in un **thread separato**.

Durante l'elaborazione:

* l'interfaccia principale rimane reattiva;
* viene visualizzato l'avanzamento;
* le operazioni possono aggiornare lo stato senza bloccare QGIS;
* al termine la barra di avanzamento viene riportata allo stato iniziale.

Il plugin non crea dock permanenti e non modifica la finestra principale di QGIS.

---

# Output

Il layer vettoriale del reticolo può contenere, fra gli altri, i seguenti attributi:

* `seg_id` — identificatore del segmento;
* `down_id` — segmento ricevente;
* `n_monte` — numero dei segmenti a monte;
* `flow_alg` — algoritmo di routing utilizzato;
* `lunghezza_m` — lunghezza del segmento;
* `area_km2` — area contribuente;
* `quota_monte` — quota alla testata del segmento;
* `quota_valle` — quota alla confluenza o all'uscita;
* `pendenza_pc` — pendenza percentuale;
* campi relativi agli ordinamenti selezionati.

Facoltativamente possono essere esportati anche:

* **DEM corretto/riempito**;
* **raster di accumulo del deflusso**;
* altri raster intermedi previsti dal processo.

---

# Traduzioni

I file sorgente delle traduzioni Qt Linguist sono disponibili in:

```text
i18n/*.ts
```

I file compilati inclusi nel plugin sono:

```text
i18n/hydronet_studio_en.qm
i18n/hydronet_studio_it.qm
```

Dopo una modifica alle stringhe del plugin è possibile rigenerare le traduzioni con:

```bash
pylupdate6 dialog.py worker.py styler.py plugin.py \
    -ts i18n/hydronet_studio_en.ts

lrelease i18n/hydronet_studio_en.ts
```

---

# Riferimenti metodologici

Le principali formulazioni utilizzate dal motore fanno riferimento a:

* **O'Callaghan, J.F. & Mark, D.M. (1984)** — estrazione delle direzioni di drenaggio mediante D8;
* **Fairfield, J. & Leymarie, P. (1991)** — Rho8;
* **Quinn et al. (1991)** — Multiple Flow Direction;
* **Tarboton, D.G. (1997)** — D-Infinity;
* **Seibert, J. & McGlynn, B. (2007)** — MD∞;
* letteratura DEMON/stream-tube per la rappresentazione della convergenza e divergenza del deflusso.

Le formulazioni implementate devono essere distinte dalle successive varianti software o dalle approssimazioni presenti in altri pacchetti GIS.
