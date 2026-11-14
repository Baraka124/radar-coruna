# RADAR-CORUÑA v0.27 — Concordancia de CRD y formularios electrónicos

- Formulario de inclusión: ayuda al responder (R016), diagnóstico alternativo (R017), comorbilidad grave descompensada (R019), ensayo interferente (R020), consentimiento firmado/no/retirado (R021) y fecha del consentimiento (R022).
- Basal: otras comorbilidades (R043), Charlson opcional (R044), vacunación antigripal (R051) y neumocócica (R052).
- Desenlaces: fecha de última información de estado vital.
- V0/V1/V2: evaluador R065 almacenado en cada visita; sin modificar las reglas de puntuación RADAR.
- R107: NR/ND/NP/NA, código R001–R106 opcional y preservación de las categorías históricas.
- CRD complementario: ocultas entradas históricas que podrían duplicar R048 o dar a R055/R056 un significado incorrecto. Las observaciones ya registradas no se borran.
- Exportación: columnas añadidas a PARTICIPANTES y VISITAS; plantilla vacía regenerada.
- API: GET /api/study/concordance, con trazabilidad de los 107 códigos.
- Modelo de almacenamiento: se amplían campos JSON de Patient/Visit; no se destruyen registros existentes ni se modifica el esquema SQLite.

**Pendientes identificados, no convertidos en supuestos:** ventana de IANUS; homologación conceptual del catálogo antiguo R055/R056; R049–R052 longitudinales; reconciliación de registros auxiliares duplicados; motivos de ausencia por episodio; vínculo R065↔R005; decisión definitiva sobre catálogo de comorbilidades.
