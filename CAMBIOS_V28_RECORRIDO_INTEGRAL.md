# RADAR-CORUÑA · v0.28 · Revisión longitudinal integral

## Alcance

- Incorpora una **revisión longitudinal de lectura** en la ficha del participante: V0/V1/V2, RADAR calculable, CAT, mMRC, recuento de observaciones complementarias y registros de ausencia R107.
- Presenta separadamente los episodios de agudización EPOC y otros eventos, los contactos asociados a episodios, los contactos sin enlace y el estado vital conocido.
- Cuando existen RADAR completos en V0 y V2 calcula y muestra V2−V0; **0 es un resultado válido**, no un dato ausente.
- Informa de algunas inconsistencias detectables en los datos históricos (orden temporal de visitas, contactos EPOC con respuesta R081/R082 no positiva, IANUS incoherente); son observaciones para revisar, no correcciones automáticas.
- Añade el endpoint de solo lectura `GET /api/study/participant-journey/{pid}`, restringido a los centros autorizados y construido mediante una única instantánea de base de datos.
- Mantiene los registros, rutas y funciones anteriores. **Sin cambio de tablas, esquema ni modificación masiva de datos**.

## Verificación

- Prueba de extremo a extremo mediante API: paciente → V0/V1/V2 → R074 → Urgencias + ingreso vinculados → otro evento → CRD complementario → R107 → desenlace → Excel → reinicio.
- Escenarios separados de ausencia de respuestas: ningún contacto no significa «No»; evento de otro tipo no cuenta como agudización EPOC.
- Revisión de acceso por centro.
- Aceptación del navegador de escritorio (1440 px) y móvil (390 px), sin errores de JavaScript ni desbordamiento horizontal.
- Regresión: lote de 34 pruebas superadas y segundo lote de 27 pruebas superadas; los lotes comparten 2 pruebas de v0.28 (59 pruebas distintas seleccionadas).
- No se afirma una ejecución unificada de todo el historial de pruebas.

## Cuestiones fuera de este incremento

La matriz de 107 variables conserva las decisiones científicas pendientes: definición del periodo de consulta IANUS, concordancia histórica de adherencia y opciones longitudinales de vacunación y tratamiento. La revisión v0.28 muestra el estado registrado sin inventar estas reglas.
