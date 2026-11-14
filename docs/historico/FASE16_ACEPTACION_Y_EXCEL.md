# RADAR-CORUÑA · Fase 16

## Alcance

Refinamiento del recorrido de trabajo clínico y de los resultados de investigación exportables; continúa la especificación del estudio existente. No se crean nuevos campos clínicos ni se añaden pacientes de demostración al inicio.

## Interfaz de consulta

- El resumen incluye «Próximas acciones por participante», derivado de los registros ya guardados.
- La acción **Continuar** conduce directamente al cribado o a la visita V0/V1/V2 correspondiente.
- Un RADAR de **0/8** es válido si están respondidas las cuatro preguntas; los campos vacíos siguen vacíos.
- Las visitas V1 y V2 no se declaran atrasadas porque no exista todavía registro. Las fechas de seguimiento se regirán por el protocolo que aprueben los investigadores.
- Los cribados clasificados «No elegible» quedan fuera de las tareas automáticas de inclusión.
- Una visita «No realizada» permanece visible para revisión, sin crear una segunda visita.

## Excel generado desde la base de datos

Además de las hojas existentes, se incorporan tres tablas planas:

1. **ANALISIS_LONG_V16**: una fila por visita guardada, cuatro respuestas RADAR, score calculado solo si procede, CAT, mMRC, actuación y principales datos basales.
2. **COHORTE_LONGITUD_V16**: una fila por participante, observaciones V0/V1/V2, cambios V2−V0 calculados solo con ambas mediciones presentes y recuentos brutos diferenciados de episodios, urgencias e ingresos.
3. **PENDIENTES_V16**: trabajo pendiente por participante, sin asumir vencimientos ni decisiones clínicas.

En **RESUMEN** se añaden el número de pares RADAR V0–V2 completos y el número de evaluaciones V0 con RADAR clasificado. Un score 0 debe contar en ambos denominadores aplicables.

Se mantienen los formularios originales, los resultados por intervalo, el diccionario y las hojas de correcciones previas. La exportación utiliza únicamente registros accesibles al usuario que realiza la descarga.

## Verificaciones

- 61 pruebas automatizadas `pytest` superadas, incluidas cuatro pruebas de la fase 16.
- Prueba interactiva Chromium con transporte a FastAPI: base vacía → alta de participante ficticio → acción V0 → RADAR 0/8 → recomendación de preparar V1.
- Excel vacío exportado y abierto con un lector independiente; 36 hojas en el perfil administrador, sin errores detectados de fórmula.
- Los registros de prueba se crean en bases temporales; la versión distribuida comienza sin participantes.

## Puntos de definición científica

Se mantienen las definiciones en revisión del protocolo, incluida la interpretación de algunos seguimientos y variables complementarias. Esta fase valida coherencia funcional y analítica del piloto; no reemplaza el acuerdo metodológico de los investigadores.
