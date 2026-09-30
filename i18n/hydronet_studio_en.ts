<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="en_US">
<context>
    <name>HydroNetDialog</name>
    <message>
        <source> (unità di a^n)</source>
        <translation> (unity of a^n)</translation>
    </message>
    <message>
        <source> km²</source>
        <translation> km²</translation>
    </message>
    <message>
        <source>Algoritmo:</source>
        <translation>Algorithm:</translation>
    </message>
    <message>
        <source>Annulla</source>
        <translation>Cancel</translation>
    </message>
    <message>
        <source>Annullamento in corso…</source>
        <translation>Cancelling…</translation>
    </message>
    <message>
        <source>Anteprima: grigio = geometria originale del reticolo; blu = geometria dopo la smussatura.</source>
        <translation>Preview: gray = original mesh geometry; blue = geometry after smoothing.</translation>
    </message>
    <message>
        <source>Applica automaticamente lo stile al risultato</source>
        <translation>Automatically apply the style to the result</translation>
    </message>
    <message>
        <source>Applica lo stile a un layer lineare esistente</source>
        <translation>Apply the style to an existing line layer</translation>
    </message>
    <message>
        <source>Applica stile</source>
        <translation>Apply style</translation>
    </message>
    <message>
        <source>Area drenata minima (km²)</source>
        <translation>Minimum contributing area (km²)</translation>
    </message>
    <message>
        <source>Area drenata minima: una cella diventa canale quando l&apos;area contribuente a monte raggiunge la soglia in km². È il criterio più diretto e indipendente dalla scala dell&apos;algoritmo di routing.</source>
        <translation>Minimum contributing area: a cell becomes part of the channel network when upslope contributing area reaches the threshold in km². This is the most direct criterion and is independent of the selected routing formulation.</translation>
    </message>
    <message>
        <source>Avvia elaborazione</source>
        <translation>Run processing</translation>
    </message>
    <message>
        <source>Avvio elaborazione.</source>
        <translation>Starting processing.</translation>
    </message>
    <message>
        <source>Banda %d - %s</source>
        <translation>Band %d - %s</translation>
    </message>
    <message>
        <source>Banda:</source>
        <translation>Band:</translation>
    </message>
    <message>
        <source>Buona pratica: usa preferibilmente un DTM/DEM in un sistema di riferimento proiettato con unità metriche (metri). I raster geografici espressi in gradi sono supportati tramite una conversione approssimata delle distanze, ma un CRS metrico è consigliato per le analisi idrologiche quantitative.</source>
        <translation>Best practice: Preferably use a DTM/DEM in a projected reference system with metric units (meters). Geographic rasters expressed in degrees are supported through an approximate distance conversion, but a metric CRS is recommended for quantitative hydrologic analyses.</translation>
    </message>
    <message>
        <source>Campo ordine (numerico):</source>
        <translation>Order field (numeric):</translation>
    </message>
    <message>
        <source>Carica nel progetto anche i raster salvati</source>
        <translation>Also load the saved rasters into the project</translation>
    </message>
    <message>
        <source>Cartella di uscita non valida: %s</source>
        <translation>Invalid output folder: %s</translation>
    </message>
    <message>
        <source>Chaikin (taglio degli angoli)</source>
        <translation>Chaikin (corner cutting)</translation>
    </message>
    <message>
        <source>Chiudi</source>
        <translation>Close</translation>
    </message>
    <message>
        <source>Classificazione gerarchica basata sull&apos;individuazione dell&apos;asta principale, generalmente determinata seguendo il percorso associato alla maggiore area drenata. L&apos;asta principale viene assegnata al livello 1; gli affluenti che confluiscono direttamente nell&apos;asta principale sono di livello 2; i corsi che alimentano questi affluenti sono di livello 3, e così via. Il valore aumenta quindi allontanandosi gerarchicamente dall&apos;asta principale verso i rami più secondari.</source>
        <translation>A hierarchical classification based on the identification of the main stem, generally determined by following the path associated with the largest drainage area. The main stem is assigned level 1; tributaries flowing directly into the main stem are level 2; the watercourses feeding these tributaries are level 3, and so on. The value thus increases as one moves hierarchically away from the main stem toward the more secondary branches.</translation>
    </message>
    <message>
        <source>Colore ordine massimo:</source>
        <translation>Colour at maximum order:</translation>
    </message>
    <message>
        <source>Colore ordine minimo:</source>
        <translation>Colour at minimum order:</translation>
    </message>
    <message>
        <source>Completato: %d segmenti -&gt; %s</source>
        <translation>Completed: %d segments -&gt; %s</translation>
    </message>
    <message>
        <source>Configura il GeoPackage di uscita e, se necessario, salva anche i raster utilizzati durante l&apos;analisi.</source>
        <translation>Configure the output GeoPackage and, if necessary, also save the rasters used during the analysis.</translation>
    </message>
    <message>
        <source>Considera anche questo valore come NoData:</source>
        <translation>Also treat this value as NoData:</translation>
    </message>
    <message>
        <source>Contenuto del reticolo</source>
        <translation>Network content</translation>
    </message>
    <message>
        <source>Criterio:</source>
        <translation>Criterion:</translation>
    </message>
    <message>
        <source>Criterio: A^%.2f · S^%.2f ≥ %.6g</source>
        <translation>Criterion: A^%.2f · S^%.2f ≥ %.6g</translation>
    </message>
    <message>
        <source>Criterio: SPI ≥ %.6g</source>
        <translation>Criterion: SPI ≥ %.6g</translation>
    </message>
    <message>
        <source>Criterio: TWI ≥ %.6g</source>
        <translation>Criterion: TWI ≥ %.6g</translation>
    </message>
    <message>
        <source>D8 - massima pendenza (8 direzioni)</source>
        <translation>D8 - steepest descent (8 directions)</translation>
    </message>
    <message>
        <source>D8 assegna il 100% del flusso alla cella vicina con la massima pendenza tra le 8 direzioni cardinali e diagonali. È deterministico e molto semplice, ma introduce una quantizzazione angolare a 45° e può creare percorsi geometrici paralleli o diagonali. A parità di pendenza, la scelta dipende dalla regola di priorità adottata dall&apos;algoritmo.</source>
        <translation>D8 assigns 100% of the flow to the neighboring cell with the steepest slope among the eight cardinal and diagonal directions. It is deterministic and very simple, but it introduces 45° angular quantization and can create parallel or diagonal geometric paths. In the event of equal slopes, the choice depends on the priority rule adopted by the algorithm.</translation>
    </message>
    <message>
        <source>DEMON (Costa-Cabral &amp; Burges, 1994) rappresenta il deflusso come un tubo bidimensionale diretto dall&apos;aspetto locale. Il tubo attraversa la griglia tramite punti di ingresso/uscita e la sua larghezza resta costante su superfici planari, aumenta su topografia divergente e si restringe su topografia convergente. L&apos;accumulo è ottenuto sommando le frazioni di area dei tubi che attraversano ciascuna cella: non è un MFD basato su potenze arbitrarie della pendenza.</source>
        <translation>DEMON (Costa-Cabral &amp; Burges, 1994) represents runoff as a two-dimensional stream tube directed by local aspect. The tube crosses the grid through entry and exit points; its width remains constant on planar terrain and expands or contracts on divergent or convergent terrain. Contributing area is obtained from the geometric fractions of source-cell tubes crossing downstream cells.</translation>
    </message>
    <message>
        <source>DEMON - Costa-Cabral &amp; Burges (stream tube)</source>
        <translation>DEMON - Costa-Cabral &amp; Burges (stream tube)</translation>
    </message>
    <message>
        <source>Dati di input</source>
        <translation>Input data</translation>
    </message>
    <message>
        <source>Densità spline (punti/tratto):</source>
        <translation>Spline density (points/segment):</translation>
    </message>
    <message>
        <source>D∞ (Tarboton) divide la superficie locale in 8 triangoli adiacenti e calcola, in ciascun triangolo, il vettore di massima discesa di un piano locale. La direzione è quindi continua su 360° e non è vincolata agli angoli del D8. L&apos;accumulo segue il vettore; per costruire il reticolo rasterizzato viene mantenuto un asse principale verso il vicino più coerente con la direzione calcolata. Questo permette di rappresentare meglio le direzioni intermedie rispetto alle sole 8 direzioni del D8.</source>
        <translation>D∞ (Tarboton) divides the local surface into eight adjacent triangular facets and computes the steepest-descent vector on each local plane. The selected direction is continuous over 360°. Contributing area is partitioned between the two facet receivers according to angular proximity; the network geometry keeps a separate primary raster axis for connectivity.</translation>
    </message>
    <message>
        <source>D∞ - Tarboton (direzione continua + 1–2 ricevitori)</source>
        <translation>D∞ - Tarboton (continuous direction + 1-2 receivers)</translation>
    </message>
    <message>
        <source>ERRORE nel caricamento: %s</source>
        <translation>ERROR while loading: %s</translation>
    </message>
    <message>
        <source>ERRORE:
</source>
        <translation>ERROR:
</translation>
    </message>
    <message>
        <source>Elaborazione annullata dall&apos;utente.</source>
        <translation>Processing cancelled by the user.</translation>
    </message>
    <message>
        <source>Elaborazione annullata.</source>
        <translation>Processing cancelled.</translation>
    </message>
    <message>
        <source>Elaborazione annullata: scegli un altro file di uscita.</source>
        <translation>Processing cancelled: choose a different output file.</translation>
    </message>
    <message>
        <source>Elaborazione fallita:
%s</source>
        <translation>Processing failed:
%s</translation>
    </message>
    <message>
        <source>Elaborazione in corso. Annullarla e chiudere?</source>
        <translation>Processing is running. Cancel it and close?</translation>
    </message>
    <message>
        <source>Esponente m della relazione area–pendenza</source>
        <translation>Slope-area exponent m</translation>
    </message>
    <message>
        <source>Esponente m:</source>
        <translation>Exponent m:</translation>
    </message>
    <message>
        <source>Esponente n della relazione area–pendenza</source>
        <translation>Slope-area exponent n</translation>
    </message>
    <message>
        <source>Esponente n:</source>
        <translation>Exponent n:</translation>
    </message>
    <message>
        <source>File di uscita</source>
        <translation>Output file</translation>
    </message>
    <message>
        <source>GeoPackage:</source>
        <translation>GeoPackage:</translation>
    </message>
    <message>
        <source>Gli ordinamenti gerarchici selezionati vengono aggiunti come campi distinti: Strahler, Shreve, Horton, Gravelius/Hack e Topologico.</source>
        <translation>The selected hierarchical ordering systems are added as distinct fields: Strahler, Shreve, Horton, Gravelius/Hack, and Topological.</translation>
    </message>
    <message>
        <source>Gravelius / Hack (asta principale)</source>
        <translation>Gravelius / Hack (main stem)</translation>
    </message>
    <message>
        <source>Horton</source>
        <translation>Horton</translation>
    </message>
    <message>
        <source>HydroNet Studio</source>
        <translation>HydroNet Studio</translation>
    </message>
    <message>
        <source>HydroNet Studio - Reticolo idrografico da DTM/DEM</source>
        <translation>HydroNet Studio - Hydrographic network from DTM/DEM</translation>
    </message>
    <message>
        <source>I punti iniziale e finale di ciascun tratto vengono mantenuti come estremi della geometria. La smussatura modifica invece la forma del percorso tra gli estremi.</source>
        <translation>The start and end points of each segment are preserved as the geometry&apos;s endpoints. Smoothing, however, alters the shape of the path between those endpoints.</translation>
    </message>
    <message>
        <source>Idrologia</source>
        <translation>Hydrology</translation>
    </message>
    <message>
        <source>Idrologia ed estrazione</source>
        <translation>Hydrology and extraction</translation>
    </message>
    <message>
        <source>Il DEM riempito è la superficie corretta utilizzata per garantire la continuità del drenaggio attraverso le depressioni. Il raster di flow accumulation rappresenta invece la quantità di deflusso accumulata a monte di ciascuna cella.</source>
        <translation>The filled DEM is the corrected surface used to ensure drainage continuity across depressions. The flow accumulation raster, on the other hand, represents the amount of runoff accumulated upstream of each cell.</translation>
    </message>
    <message>
        <source>Il DEM viene prima trattato con Priority-Flood per garantire un drenaggio coerente; quindi viene applicato il modello di deflusso selezionato.</source>
        <translation>The DEM is first processed with Priority-Flood to ensure consistent drainage; the selected flow-routing model is then applied.</translation>
    </message>
    <message>
        <source>Il GeoPackage contiene un segmento per ciascuna asta del reticolo, collegata topologicamente al segmento a valle. La geometria viene ricavata dal percorso di drenaggio raster e può essere successivamente smussata senza spostare i nodi di connessione.</source>
        <translation>The GeoPackage contains a segment for each reach of the network, topologically connected to the downstream segment. The geometry is derived from the raster drainage path and can subsequently be smoothed without shifting the connection nodes.</translation>
    </message>
    <message>
        <source>Il file &apos;%s&apos; esiste gia&apos;. Sovrascriverlo?</source>
        <translation>File &apos;%s&apos; already exists. Overwrite it?</translation>
    </message>
    <message>
        <source>Il raster ha %.0f milioni di celle: l&apos;elaborazione richiedera&apos; molto tempo e memoria. Continuare?</source>
        <translation>The raster has %.0f million cells: processing will need a lot of time and memory. Continue?</translation>
    </message>
    <message>
        <source>Impossibile caricare il layer risultante.</source>
        <translation>Could not load the resulting layer.</translation>
    </message>
    <message>
        <source>Indica il file GeoPackage di uscita.</source>
        <translation>Specify the output GeoPackage file.</translation>
    </message>
    <message>
        <source>Input</source>
        <translation>Input</translation>
    </message>
    <message>
        <source>Intensità:</source>
        <translation>Strength:</translation>
    </message>
    <message>
        <source>L&apos;intensità controlla la forza della smussatura. Per il metodo Gaussiano corrisponde al valore sigma, espresso in vertici; per Chaikin corrisponde al numero di iterazioni. La densità della spline controlla invece il numero di suddivisioni utilizzate tra i vertici della curva.</source>
        <translation>Intensity controls the strength of the smoothing. For the Gaussian method, it corresponds to the sigma value, expressed in vertices; for Chaikin, it corresponds to the number of iterations. Spline density, on the other hand, controls the number of subdivisions used between the curve&apos;s vertices.</translation>
    </message>
    <message>
        <source>Layer:</source>
        <translation>Layer:</translation>
    </message>
    <message>
        <source>MD∞ (Seibert &amp; McGlynn, 2007) combina faccette triangolari e multiple flow direction. Vengono valutate tutte le faccette locali; le direzioni valide sono pesate secondo la pendenza con esponente configurabile (default 1,1) e, quando una direzione cade tra due vicini, la quota viene ulteriormente ripartita in base alla distanza angolare. Questo evita la dispersione irrealistica del MFD classico su superfici piane/concave e permette più ricevitori sulle superfici convesse.</source>
        <translation>MD∞ (Seibert &amp; McGlynn, 2007) combines triangular facets with multiple-flow routing. All local facets are evaluated; valid downslope directions are weighted by gradient with an exponent (default 1.1), and directions falling between neighbours are further partitioned by angular position. This reduces unrealistic dispersion on planar or concave slopes while allowing multiple receivers on convex terrain.</translation>
    </message>
    <message>
        <source>MD∞ - Seibert &amp; McGlynn (triangolare multiplo)</source>
        <translation>MD∞ - Seibert &amp; McGlynn (triangular multiple flow)</translation>
    </message>
    <message>
        <source>MFD classico (Freeman, 1991; Quinn et al., 1991) distribuisce il contributo fra tutte le celle vicine a quota inferiore. La frazione è f_i = S_i^p L_i / Σ(S_j^p L_j), con p=1,1 nella formulazione classica di Freeman e L_i lunghezza di contorno efficace (0,5 della dimensione della faccia per cardinali e 0,354 per diagonali nel caso quadrato). Il routing è quindi realmente multi-direzionale e mass-conservativo.</source>
        <translation>The classic MFD (Freeman, 1991; Quinn et al., 1991) distributes the contribution among all neighboring cells at a lower elevation. The fraction is f_i = S_i^p L_i / Σ(S_j^p L_j), with p=1.1 in Freeman&apos;s classic formulation and L_i representing the effective contour length (0.5 times the face dimension for cardinal directions and 0.354 for diagonals in the square grid case). The routing is thus truly multi-directional and mass-conservative.</translation>
    </message>
    <message>
        <source>MFD classico - Freeman/Quinn (pesi S^1.1·L)</source>
        <translation>Classical MFD - Freeman/Quinn (S^1.1·L weights)</translation>
    </message>
    <message>
        <source>Media mobile gaussiana</source>
        <translation>Gaussian moving average</translation>
    </message>
    <message>
        <source>Metodi di ordinamento</source>
        <translation>Ordering methods</translation>
    </message>
    <message>
        <source>Metodi disponibili: Gaussiana per attenuare i cambi bruschi di direzione; Chaikin per arrotondare progressivamente i vertici; Catmull-Rom per ottenere una curva interpolata; Naturale per combinare attenuazione Gaussiana e spline.</source>
        <translation>Available methods: Gaussian, to smooth out abrupt changes in direction; Chaikin, to progressively round off vertices; Catmull-Rom, to obtain an interpolated curve; Natural, to combine Gaussian smoothing and splines.</translation>
    </message>
    <message>
        <source>Metodo basato sulla magnitudo del bacino drenato dal singolo tratto. Ogni tratto che nasce da una sorgente ha magnitudo 1. In corrispondenza di una confluenza, la magnitudo del tratto a valle è data dalla somma delle magnitudo dei due tratti confluenti. Il valore ottenuto rappresenta quindi, in termini topologici, il numero complessivo di sorgenti che contribuiscono al deflusso del tratto considerato.</source>
        <translation>A method based on the magnitude of the drainage basin of an individual stream segment. Each segment originating from a source has a magnitude of 1. At a confluence, the magnitude of the downstream segment is the sum of the magnitudes of the two converging segments. The resulting value thus represents, in topological terms, the total number of sources contributing to the flow of the segment in question.</translation>
    </message>
    <message>
        <source>Metodo gerarchico basato sulla struttura della rete idrografica. I tratti che partono dalle sorgenti hanno ordine 1. Quando due tratti dello stesso ordine k confluiscono, il tratto risultante assume ordine k+1. Quando invece confluiscono tratti di ordine diverso, il tratto a valle mantiene l&apos;ordine maggiore. In questo modo l&apos;ordine aumenta solo quando si incontrano due rami di pari importanza gerarchica.</source>
        <translation>A hierarchical method based on the structure of the drainage network. Stream segments originating at the sources are assigned order 1. When two segments of the same order *k* join, the resulting segment takes on order *k*+1. Conversely, when segments of different orders join, the downstream segment retains the higher order. Thus, the order increases only when two branches of equal hierarchical importance meet.</translation>
    </message>
    <message>
        <source>Metodo gerarchico derivato dalla classificazione di Strahler, con particolare attenzione all&apos;individuazione dell&apos;asta principale. L&apos;asta principale conserva il valore dell&apos;ordine più elevato raggiunto lungo la rete fino alla sorgente, mentre i rami secondari vengono classificati in funzione della loro posizione gerarchica rispetto all&apos;asta principale. È utile per descrivere la struttura gerarchica del reticolo distinguendo il corso principale dagli affluenti.</source>
        <translation>A hierarchical method derived from the Strahler classification, focusing specifically on identifying the main stem. The main stem retains the highest order value reached within the network all the way to the source, while secondary branches are classified according to their hierarchical position relative to the main stem. It is useful for describing the hierarchical structure of the drainage network by distinguishing the main course from its tributaries.</translation>
    </message>
    <message>
        <source>Metodo:</source>
        <translation>Method:</translation>
    </message>
    <message>
        <source>Modello di direzione del deflusso</source>
        <translation>Flow-direction model</translation>
    </message>
    <message>
        <source>Modello digitale del terreno</source>
        <translation>Digital terrain model</translation>
    </message>
    <message>
        <source>Naturale - gaussiana + spline (consigliato)</source>
        <translation>Natural - Gaussian + spline (recommended)</translation>
    </message>
    <message>
        <source>Nessun raster (GDAL) disponibile nel progetto.</source>
        <translation>No (GDAL) raster available in the project.</translation>
    </message>
    <message>
        <source>Nessun raster selezionato.</source>
        <translation>No raster selected.</translation>
    </message>
    <message>
        <source>Nessuna (percorso D8 grezzo)</source>
        <translation>None (raw D8 path)</translation>
    </message>
    <message>
        <source>Nome del layer:</source>
        <translation>Layer name:</translation>
    </message>
    <message>
        <source>Nota: l&apos;area drenata è espressa in km² e deriva dalla flow accumulation moltiplicata per l&apos;area della cella. Nei metodi a flusso frazionato (D∞, MD∞, MFD e DEMON) l&apos;accumulo può assumere valori decimali perché il flusso di una cella può essere distribuito tra più direzioni.</source>
        <translation>Note: The drainage area is expressed in km² and is derived from the flow accumulation multiplied by the cell area. In fractional flow methods (D∞, MD∞, MFD, and DEMON), accumulation can take decimal values ​​because the flow from a cell can be distributed across multiple directions.</translation>
    </message>
    <message>
        <source>Ordinamento</source>
        <translation>Ordering</translation>
    </message>
    <message>
        <source>Ordinamento da usare:</source>
        <translation>Ordering to use:</translation>
    </message>
    <message>
        <source>Ordinamento gerarchico</source>
        <translation>Hierarchical ordering</translation>
    </message>
    <message>
        <source>Ordine %s: da %d a %d.</source>
        <translation>Order %s: from %d to %d.</translation>
    </message>
    <message>
        <source>Ordine determinato esclusivamente dalla posizione topologica del tratto all&apos;interno della rete rispetto allo sbocco finale. Il segmento che raggiunge direttamente la foce ha valore 1; procedendo verso monte, il valore aumenta di uno per ogni tratto che separa il segmento dalla foce. Il metodo non considera la dimensione del bacino, la portata o l&apos;importanza idrologica del ramo, ma esclusivamente il numero di collegamenti necessari per raggiungere lo sbocco.</source>
        <translation>Order determined exclusively by the topological position of the section within the network with respect to the final outlet. The segment that directly reaches the mouth has a value of 1; proceeding upstream, the value increases by one for each stretch that separates the segment from the mouth. The method does not consider the size of the basin, the flow rate or the hydrological importance of the branch, but only the number of connections necessary to reach the outlet.</translation>
    </message>
    <message>
        <source>Output</source>
        <translation>Output</translation>
    </message>
    <message>
        <source>Parametri</source>
        <translation>Parameters</translation>
    </message>
    <message>
        <source>Pendenza–area: il canale viene avviato quando a^n·S^m supera la soglia, con a area contribuente specifica, S = sin(β), e n,m esponenti. È una forma standard della relazione topografica di channel initiation; i parametri vanno calibrati sul contesto locale.</source>
        <translation>Slope-area criterion: a channel is initiated when a^n · S^m exceeds the threshold, where a is specific contributing area, S = sin(beta), and n and m are exponents. Parameters should be calibrated for the local geomorphic setting.</translation>
    </message>
    <message>
        <source>Per l&apos;area drenata la soglia è espressa in km². Gli altri criteri sono indici adimensionali o con unità proprie e vengono applicati direttamente al raster derivato; la descrizione mostra esattamente il significato della soglia.</source>
        <translation>For contributing area the threshold is expressed in km². Other criteria use the units of their mathematical formulation and are applied directly to the derived raster; the description shows the meaning of each threshold.</translation>
    </message>
    <message>
        <source>Per ogni segmento vengono salvati, quando disponibili, identificativo, segmento a valle, numero di aste confluenti, lunghezza, area drenata, quota a monte, quota a valle, pendenza media e algoritmo di routing utilizzato.</source>
        <translation>For each segment, the following are saved—when available: identifier, downstream segment, number of converging reaches, length, drainage area, upstream elevation, downstream elevation, average slope, and the routing algorithm used.</translation>
    </message>
    <message>
        <source>Prodotti aggiuntivi</source>
        <translation>Additional outputs</translation>
    </message>
    <message>
        <source>Raster DTM/DEM:</source>
        <translation>DTM/DEM raster:</translation>
    </message>
    <message>
        <source>Relazione pendenza–area (Montgomery–Dietrich)</source>
        <translation>Slope-area relationship (Montgomery-Dietrich)</translation>
    </message>
    <message>
        <source>Reticolo idrografico</source>
        <translation>Hydrographic network</translation>
    </message>
    <message>
        <source>Reticolo idrografico da DTM</source>
        <translation>Hydrographic network from DTM</translation>
    </message>
    <message>
        <source>Rho8 (Fairfield &amp; Leymarie, 1991) mantiene un solo ricevitore, ma sceglie casualmente fra i vicini a quota inferiore con probabilità proporzionale alla pendenza locale. Il 100% del flusso segue il vicino estratto. Il seed rende la realizzazione riproducibile; non viene usata una potenza arbitraria della pendenza. Il metodo è pensato per ridurre il bias direzionale del reticolo mantenendo un routing convergente a singolo flusso. Una volta effettuata la selezione, il 100% del flusso viene indirizzato verso il vicino scelto, esattamente come nel D8. Rispetto al D8 deterministico, la componente casuale permette di evitare che la scelta sistematica della massima pendenza produca sempre gli stessi percorsi fortemente allineati alla griglia, soprattutto su superfici poco inclinate o caratterizzate da molte direzioni possibili. Il parametro seed controlla il generatore pseudo-casuale: utilizzando lo stesso seed si ottiene la stessa sequenza di scelte e quindi un risultato riproducibile; cambiando il seed si ottiene invece una diversa realizzazione del reticolo di drenaggio. Il seed non modifica le quote del DEM né le pendenze calcolate, ma determina esclusivamente quale delle direzioni ammissibili viene estratta casualmente.</source>
        <translation>Rho8 (Fairfield &amp; Leymarie, 1991) maintains a single receiver but randomly selects from among the lower-elevation neighbors with a probability proportional to the local slope. The entire flow (100%) follows the selected neighbor. The seed ensures the realization is reproducible; no arbitrary power of the slope is used. The method is designed to reduce grid-induced directional bias while maintaining single-flow convergent routing. Once the selection is made, 100% of the flow is directed toward the chosen neighbor, exactly as in the D8 method. Compared to the deterministic D8, the random component prevents the systematic selection of the steepest slope from consistently producing the same grid-aligned paths—particularly on surfaces with low gradients or those offering multiple possible flow directions. The seed parameter controls the pseudo-random number generator: using the same seed yields the same sequence of choices—and thus a reproducible result—whereas changing the seed produces a different realization of the drainage network. The seed does not alter the DEM elevations or the calculated slopes; it solely determines which of the permissible directions is randomly selected.</translation>
    </message>
    <message>
        <source>Rho8 - Fairfield &amp; Leymarie (stocastico)</source>
        <translation>Rho8 - Fairfield &amp; Leymarie (stochastic)</translation>
    </message>
    <message>
        <source>Riduce l&apos;effetto a gradini tipico delle geometrie raster e rende le aste del reticolo più fluide. La smussatura viene applicata alla geometria delle polilinee dopo l&apos;estrazione del reticolo e non modifica il DTM, le direzioni di deflusso o il calcolo dell&apos;accumulo.</source>
        <translation>It reduces the jagged effect typical of raster geometries and makes the network segments smoother. Smoothing is applied to the polyline geometry after the network is extracted and does not alter the DTM, flow directions, or the accumulation calculation.</translation>
    </message>
    <message>
        <source>SPI (Stream Power Index): usa la potenziale concentrazione del deflusso, SPI = a·tan(β), dove a è l&apos;area contribuente specifica e β la pendenza. Valori elevati identificano zone dove contributo e pendenza favoriscono la concentrazione del flusso.</source>
        <translation>SPI (Stream Power Index): utilizes the potential concentration of runoff; SPI = a·tan(β), where a is the specific contributing area and β is the slope. High values ​​identify areas where the contributing area and slope favor flow concentration.</translation>
    </message>
    <message>
        <source>SPI - Stream Power Index</source>
        <translation>SPI - Stream Power Index</translation>
    </message>
    <message>
        <source>Salva il DEM depresso riempito (GeoTIFF)</source>
        <translation>Save the filled (depressionless) DEM (GeoTIFF)</translation>
    </message>
    <message>
        <source>Salva il raster di flow accumulation (GeoTIFF)</source>
        <translation>Save the flow accumulation raster (GeoTIFF)</translation>
    </message>
    <message>
        <source>Scegli uno o piu&apos; metodi: ognuno genera un campo dedicato nella tabella.</source>
        <translation>Choose one or more methods: each one generates its own field in the attribute table.</translation>
    </message>
    <message>
        <source>Seed casuale (Rho8):</source>
        <translation>Random seed (Rho8):</translation>
    </message>
    <message>
        <source>Seleziona almeno un metodo di ordinamento.</source>
        <translation>Select at least one ordering method.</translation>
    </message>
    <message>
        <source>Seleziona il modello digitale del terreno (DTM/DEM) caricato nel progetto.</source>
        <translation>Select the digital terrain model (DTM/DEM) loaded in the project.</translation>
    </message>
    <message>
        <source>Seleziona un DTM/DEM di input.</source>
        <translation>Select an input DTM/DEM.</translation>
    </message>
    <message>
        <source>Sfoglia…</source>
        <translation>Browse…</translation>
    </message>
    <message>
        <source>Shreve (magnitudo)</source>
        <translation>Shreve (magnitude)</translation>
    </message>
    <message>
        <source>Smussatura</source>
        <translation>Smoothing</translation>
    </message>
    <message>
        <source>Smussatura del reticolo</source>
        <translation>Network smoothing</translation>
    </message>
    <message>
        <source>Soglia di innesco dei canali</source>
        <translation>Channel initiation threshold</translation>
    </message>
    <message>
        <source>Soglia principale:</source>
        <translation>Main threshold:</translation>
    </message>
    <message>
        <source>Spessore (e colore) delle linee proporzionali all&apos;ordine gerarchico.</source>
        <translation>Line width (and colour) proportional to the hierarchical order.</translation>
    </message>
    <message>
        <source>Spessore ordine massimo:</source>
        <translation>Width at maximum order:</translation>
    </message>
    <message>
        <source>Spessore ordine minimo:</source>
        <translation>Width at minimum order:</translation>
    </message>
    <message>
        <source>Spline Catmull-Rom</source>
        <translation>Catmull-Rom spline</translation>
    </message>
    <message>
        <source>Stile</source>
        <translation>Style</translation>
    </message>
    <message>
        <source>Stile %s sul campo &apos;%s&apos;.</source>
        <translation>%s style on field &apos;%s&apos;.</translation>
    </message>
    <message>
        <source>Stile automatico</source>
        <translation>Automatic styling</translation>
    </message>
    <message>
        <source>Stile del nuovo reticolo</source>
        <translation>Style of the new network</translation>
    </message>
    <message>
        <source>Strahler</source>
        <translation>Strahler</translation>
    </message>
    <message>
        <source>TWI (Topographic Wetness Index): TWI = ln(a/tan(β)). È un indice di potenziale saturazione/accumulo idrico, non una legge universale di incisione dei canali; valori elevati selezionano le zone topograficamente più umide.</source>
        <translation>TWI (Topographic Wetness Index): TWI = ln(a / tan(beta)). It is an index of potential wetness/saturation rather than a universal channel-incision law; high values identify topographically wetter areas.</translation>
    </message>
    <message>
        <source>TWI - Topographic Wetness Index</source>
        <translation>TWI - Topographic Wetness Index</translation>
    </message>
    <message>
        <source>Topologico (distanza dalla foce)</source>
        <translation>Topological (distance from the outlet)</translation>
    </message>
    <message>
        <source>Una smussatura più intensa produce linee più morbide ma può allontanare maggiormente la geometria dalla traccia raster originale. Per una rappresentazione cartografica naturale sono generalmente preferibili valori moderati.</source>
        <translation>More intense smoothing produces softer lines but can cause the geometry to deviate further from the original raster trace. Moderate values ​​are generally preferable for a natural cartographic representation.</translation>
    </message>
    <message>
        <source>Verifica che il DTM abbia una risoluzione adeguata alla scala dell&apos;analisi e che il valore NoData sia correttamente identificato. Depressioni, artefatti, ponti, strade e discontinuità del modello del terreno possono influenzare le direzioni di deflusso e l&apos;accumulo. Il modello applica un riempimento delle depressioni prima del calcolo del routing.</source>
        <translation>Ensure that the DTM has a resolution appropriate for the scale of the analysis and that the NoData value is correctly identified. Depressions, artifacts, bridges, roads, and discontinuities in the terrain model can influence flow directions and accumulation. The model fills depressions prior to calculating flow routing.</translation>
    </message>
    <message>
        <source>≈ %.3f celle equivalenti</source>
        <translation>≈ %.3f equivalent cells</translation>
    </message>
</context>
<context>
    <name>HydroNetStyler</name>
    <message>
        <source>Campo &apos;%s&apos; non trovato.</source>
        <translation>Field &apos;%s&apos; not found.</translation>
    </message>
    <message>
        <source>Il campo &apos;%s&apos; non contiene valori.</source>
        <translation>Field &apos;%s&apos; contains no values.</translation>
    </message>
    <message>
        <source>Ordine %s</source>
        <translation>Order %s</translation>
    </message>
    <message>
        <source>categorizzato (%d classi)</source>
        <translation>categorized (%d classes)</translation>
    </message>
    <message>
        <source>graduato (%d classi, scala geometrica)</source>
        <translation>graduated (%d classes, geometric scale)</translation>
    </message>
</context>
<context>
    <name>HydroWorker</name>
    <message>
        <source>Calcolo degli ordinamenti gerarchici…</source>
        <translation>Computing hierarchical orderings…</translation>
    </message>
    <message>
        <source>Calcolo del criterio di innesco: %s…</source>
        <translation>Calculation of the triggering criterion: %s…</translation>
    </message>
    <message>
        <source>Celle che soddisfano il criterio: %d.</source>
        <translation>Cells that meet the criterion: %d.</translation>
    </message>
    <message>
        <source>Celle riempite: %d.</source>
        <translation>Filled cells: %d.</translation>
    </message>
    <message>
        <source>DEM: %d × %d celle, risoluzione %.2f × %.2f m, %d celle valide.</source>
        <translation>DEM: %d × %d cells, resolution %.2f × %.2f m, %d valid cells.</translation>
    </message>
    <message>
        <source>Dimensioni del blocco raster inattese.</source>
        <translation>Unexpected raster block size.</translation>
    </message>
    <message>
        <source>Estrazione del reticolo…</source>
        <translation>Extracting the network…</translation>
    </message>
    <message>
        <source>Flow accumulation (%s)…</source>
        <translation>Flow accumulation (%s)…</translation>
    </message>
    <message>
        <source>Il DEM non contiene abbastanza celle valide.</source>
        <translation>The DEM does not contain enough valid cells.</translation>
    </message>
    <message>
        <source>Impossibile creare &apos;%s&apos;.</source>
        <translation>Could not create &apos;%s&apos;.</translation>
    </message>
    <message>
        <source>Impossibile leggere il raster in ingresso.</source>
        <translation>Could not read the input raster.</translation>
    </message>
    <message>
        <source>Impossibile sovrascrivere &apos;%s&apos; (file in uso?).</source>
        <translation>Could not overwrite &apos;%s&apos; (file in use?).</translation>
    </message>
    <message>
        <source>La soglia di innesco deve essere maggiore di zero.</source>
        <translation>The trigger threshold must be greater than zero.</translation>
    </message>
    <message>
        <source>Lettura del DEM…</source>
        <translation>Reading the DEM…</translation>
    </message>
    <message>
        <source>Nessun canale estratto con la soglia impostata: riduci l&apos;area minima drenata.</source>
        <translation>No channel extracted with the current threshold: lower the minimum drainage area.</translation>
    </message>
    <message>
        <source>Riempimento depressioni e direzioni di drenaggio (%s)…</source>
        <translation>Depression filling and flow directions (%s)…</translation>
    </message>
    <message>
        <source>Scrittura del GeoPackage…</source>
        <translation>Writing the GeoPackage…</translation>
    </message>
    <message>
        <source>Segmenti estratti: %d (sbocchi: %d).</source>
        <translation>Segments extracted: %d (outlets: %d).</translation>
    </message>
    <message>
        <source>Smussatura delle linee (%s)…</source>
        <translation>Smoothing the lines (%s)…</translation>
    </message>
    <message>
        <source>Soglia SPI: %.6g.</source>
        <translation>SPI threshold: %.6g.</translation>
    </message>
    <message>
        <source>Soglia TWI: %.6g.</source>
        <translation>TWI threshold: %.6g.</translation>
    </message>
    <message>
        <source>Soglia di area drenata: %.6f km² (%.3f celle equivalenti).</source>
        <translation>Drained area threshold: %.6f km² (%.3f equivalent cells).</translation>
    </message>
    <message>
        <source>Soglia pendenza–area: a^%.2f · S^%.2f ≥ %.6g.</source>
        <translation>Slope-area threshold: a^%.2f · S^%.2f ≥ %.6g.</translation>
    </message>
    <message>
        <source>Tipo di dato raster non supportato.</source>
        <translation>Unsupported raster data type.</translation>
    </message>
</context>
</TS>
