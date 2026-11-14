# RADAR-CORUÑA — Registro de aceptación parcial v0.20

**Fecha:** 10/11/2026  
**Procedencia:** release local v0.19 (27/10/2026) recuperada de archivo original.  
**Ámbito:** datos ficticios exclusivamente. Ninguna habilitación de uso clínico.

## Pruebas de esta iteración

- 18 pruebas automatizadas superadas, incluyendo 3 nuevas pruebas específicas de concordancia CRD, persistencia, errores IANUS, categorías inhaladas, auditoría y Excel.
- Recorrido browser v0.20 completo: alta sintética, fecha de nacimiento, recuentos moderadas/graves, visita V0, selección LAMA/LABA, roflumilast, rescate prescrito y verificación IANUS, persistencia comprobada.
- Recorrido de regresión browser v0.19 del flujo de seguimiento y análisis científico, superado.
- Recorrido de regresión browser de estructura responsive/navegación v0.19, superado.
- JavaScript validado sintácticamente con Node.
- Nueva plantilla Excel vacía v0.20: 41 hojas, con columnas clínicas añadidas sin desplazar las antiguas.

**Limitaciones:** la suite monolítica heredada contiene un bloqueo previo documentado en un test de backup y no se declara superada integralmente. Tampoco se ha realizado ensayo con datos reales, revisión de diseño por centros ni validación científica del mapeo definitivo.

## Próxima iteración

Conciliar secciones restantes del CRD: 1–13, numeración de episodios por participante, contactos, comorbilidades y actuaciones; armonizar diccionario y reglas digitales. Validación científica final pendiente. No desplegar en red institucional ni usar datos personales reales.
