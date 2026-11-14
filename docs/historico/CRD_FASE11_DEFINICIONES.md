# RADAR-CORUÑA · CRD estructurado v0.11

**Borrador científico y técnico para revisión del equipo investigador.** Ningún campo, umbral ni ventana propuesta constituye una decisión clínica aprobada. Aplicación exclusivamente sintética.

## 1. Modelo longitudinal

Cada participante se identifica mediante un código de simulación; no se almacena identidad civil en el piloto. El centro constituye el ámbito de acceso. Los datos se organizan como:

- **Cribado / paciente**: elegibilidad, consentimiento, antecedentes y caracterización basal.
- **Visita V0 / V1 / V2**: cuatro respuestas RADAR, CAT, mMRC y plan/actuación. Una visita `no_realizada` documenta motivo, no simula medidas.
- **CRD complementario**: variables categóricas y actuaciones descritas en el catálogo propuesto, sin duplicar el cálculo RADAR.
- **Episodios**: cada agudización registrada como unidad independiente.
- **Contactos**: urgencias o ingreso, opcionalmente asociados a un episodio. Un contacto no suma automáticamente otra agudización.
- **Auditoría**: el valor vigente está en la tabla correspondiente; una corrección posterior registra responsable, motivo y antiguo/nuevo valor.

## 2. Mínimo técnico para una visita cumplimentada

Las siete observaciones propuestas son rescate, agudización reciente, disnea, actividad, CAT total, mMRC exacto y actuación documentada. El sistema calcula RADAR como 3 + 2 + 2 + 1 solo cuando están las cuatro respuestas completas. El cero es un resultado válido. `No consta` o una casilla sin responder son valores ausentes.

Una visita completa a efectos del formulario **no equivale** a aprobación del CRD definitivo ni a garantía de elegibilidad.

## 3. Basal y seguimiento

V0: confirmar consentimiento y criterios de cribado, registrar espirometría, antecedentes y las cuatro respuestas RADAR. Los campos basales del nuevo seguimiento son **propuestos**; la ausencia genera alerta, no exclusión automática. Los paquetes-año son condicionales al antecedente de tabaquismo actual o previo.

V1 y V2: recoger RADAR, CAT, mMRC y actuaciones, actualizar eventos de seguimiento mediante tablas independientes. Ventanas de 6±1 y 12±1 meses son *orientativas*, pendientes de acuerdo.

## 4. Casos que exigen acuerdo metodológico

1. Resultado principal: prevalencia basal de mal control frente a cambio longitudinal, y si la implantación constituye objetivo separado.
2. Confirmar RADAR versión adaptada a AP y sus derechos de uso/reproducción.
3. Estabilidad clínica: 4 frente a 4–8 semanas en los borradores; no bloquear en automático.
4. Medición de adherencia: instrumento o categorías reproducibles, y momentos de recogida.
5. Definición de agudización moderada/grave, fuente, deduplicación y relación con urgencias e ingresos.
6. Denominadores para indicadores de implantación (no deducibles exclusivamente de los casos inscritos).
7. Calendario: última inclusión frente a 12 meses individuales de observación.
8. Datos personales: base jurídica, decisiones CEIm, roles autorizados, seudonimización, custodia y entorno institucional.

## 5. Inspección en la aplicación

Abrir `CRD por visitas` para estado por participante; `Visitas V0–V2` para el núcleo; `CRD ampliado` para las mediciones adicionales; `Calidad de datos` para alertas; `Diccionario y decisiones` para catálogo completo. El Excel generado desde base de datos contiene `FLUJO_CRD_V11` y `GUIA_CRD_V11`, además de las hojas anteriores.

**Próxima aprobación:** revisión de PI, Neumología, médicos de Atención Primaria y metodología/estadística antes de congelar el CRD clínico; no habilitar uso real hasta autorización institucional.
