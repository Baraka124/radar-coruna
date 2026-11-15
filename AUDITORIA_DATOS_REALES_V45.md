# RADAR-CORUÑA · Auditoría de datos reales, valores fijos y simulación (v0.45)

**Fecha de corte:** 15-11-2026. **Base revisada:** `main` @ `bbe30f2` (v0.44), desplegada en Railway staging con estado SUCCESS. **Ámbito:** código frontend, API FastAPI, catálogo CRD, persistencia PostgreSQL/Supabase y tablas de staging. Esta revisión no valida el uso de datos clínicos reales; la autorización ética y la gobernanza de datos siguen siendo condiciones previas.

## Regla de verdad del sistema

**Nunca se debe presentar como observado o registrado lo que únicamente figure definido en el código.** Distinguimos:

1. **Dato de investigación:** introducido por una persona autorizada, validado y persistido; nunca rellenado como ejemplo ni simulado por pantalla.
2. **Configuración operativa:** centros participantes, cuentas, roles asignados, invitaciones y calendario; modificable por usuario autorizado y persistida, salvo los roles y restricciones de seguridad.
3. **Definición científica:** valores permitidos de CRD (V0/V1/V2, Sí/No/NC, escalas y límites, criterios acordados), que sí requieren codificación estricta y versionada.
4. **Fixture de ensayo:** reservado a pruebas automatizadas/locales; no debe aparecer en estadísticas ni invitaciones reales de staging.

## Fotografía de base de datos observada

Supabase `radar-coruna-staging` (`radar` schema), consulta del 15-11-2026:
- `users`: **1**; `invitations`: **3**; `sessions`: **7**; `audit`: **3**.
- `patients`, `visits`, `episodes`, `contacts`, `study_observations`, `missing_data`, `phase14_records`, `audit_field_changes`: **0** cada una.
- **No existe una tabla de centros** en las 13 tablas observadas. Los tres centros del sistema proceden del código, no de registros de alta.
- Las 13 tablas figuran con RLS deshabilitado. Una comprobación adicional de privilegios confirmó que `anon` y `authenticated` no tienen `USAGE` del esquema privado `radar` ni concesiones directas de tabla. Por tanto, no está demostrada la exposición directa mediante Data API; aun así, debe revisarse la estrategia de RLS, concesiones y permisos antes de datos reales. No habilitar políticas genéricas ni RLS masivo sin validar el acceso del backend.

## Hallazgos y acciones verificables

| ID | Severidad | Hallazgo confirmado | Referencia | Corrección / aceptación |
|---|---|---|---|---|
| D01 | P0 | El catálogo `CENTRES` contiene tres centros ficticios inmutables. | `server.py:46-51` | Tabla `centres` + alta/edición/estado desde administración; 0 centros si nadie los ha registrado. |
| D02 | P0 | `Patient.center` e `InvitationCreate.centre` usan `Literal` con los tres códigos. | `server.py:73-76,888-891` | Validar centro activo existente en BD, con aislamiento autorizado. |
| D03 | P0 | `/api/state`, resumen multicéntrico, estudios e informes usan `CENTRES` fijo. | `server.py:926-935,1015-1029,1217-1233,1445-1478,1605` | Misma tabla de centros para desplegables, permisos, métricas y exportación. Ningún contador de centros ficticio. |
| D04 | P0 | Claves de CRD se restringen al patrón `SIM-CS0[1-3]`. | `phase14_completion.py:106-112` | Patrón configurable + comprobación de existencia; validación coherente para centros, profesionales e implementación. |
| D05 | P1 | Existen 4 cuentas de demostración con contraseñas conocidas en el modo local. | `server.py:544-552` | Mantener exclusivamente en tests/local; la creación de usuarios de staging debe proceder de bootstrap seguro e invitación. |
| D06 | P1 | Hay fixtures de 3 participantes, 4 visitas, 1 episodio y 1 contacto, activados con `RADAR_SEED_DEMO=1`. | `server.py:553-574` | Conservar en pruebas controladas; nunca precargar estadísticas compartidas. **Verificado:** `operational_v40.py:34-35` ya prohíbe ese flag cuando `RADAR_MODE=synthetic_staging`. |
| D07 | P1 | El ID de participante utiliza un prefijo SIM y generación temporal en el formulario. | `static/index.html:2047`; `server.py:46,119-124` | Mantener IDs ficticios para staging; implementar numeración gestionada o política de códigos del estudio cuando proceda. No inventar identidad ni participantes. |
| D08 | P1 | Mes complementario fijado en `2026-10`. | `static/index.html:2370` | **Corregido en esta rama**: mes local de la sesión, editable. |
| D09 | P1 | Metadatos exportados llaman “demo” a usuarios y códigos. | `export_research.py:17,25,61,70` | **Corregido parcialmente en esta rama**: encabezados neutrales, conservando avisos sobre datos ficticios donde corresponden. |
| D10 | P1 | La carga de algunos módulos auxiliares falla de forma silenciosa en la interfaz; el detalle queda en consola. | `static/index.html:1793-1840` | Estados visibles de carga/error/reintento; evitar mostrar una métrica previa o un cero como si fuese una carga completa. |
| D11 | P2 | Hay claves/funciones antiguas de estado local que ya no participan en la persistencia. | `static/index.html:1779,1938` | **Corregido en esta rama**: retirar `KEY` y `addAudit` no usados; mantener la auditoría exclusivamente del backend. |
| D12 | P2 | Se expone una pequeña API global de test en el documento de staging. | `static/index.html:2690` | Conservar para regresiones automatizadas por ahora; mover a un bundle de pruebas antes de producción. No crea datos. |
| D13 | P2 | Varias pantallas y salidas describen explícitamente un entorno de prueba. | `static/index.html:1943,1962-1978`; `export_research.py` | Normalizar tono visual de **staging de validación**, sin prometer que es un sistema clínico autorizado. |
| D14 | P1 | No hay integración automática de historias clínicas/IANUS acreditada por la lectura del servidor. | API de registro y `/api/study/*` en `server.py` | Distinguir “registro del investigador” de “dato integrado” y exigir procedencia documentada por campo; evitar fingir verificación externa. |
| D15 | P1 | RLS deshabilitado en las 13 tablas privadas de staging. | Supabase `radar` (inspección 15-11-2026) | Revisión de privilegios y acceso de servicio; implementar controles adecuados antes de cualquier exposición de datos reales. |

### Lo que NO es dato falso ni debe eliminarse

- Los valores fijos `V0/V1/V2`, roles `admin/investigator/reviewer`, categorías CRD, validaciones y escalas RADAR/CAT/mMRC, y los tratamientos normalizados corresponden a **reglas del dominio**, no a pacientes inventados. Cualquier cambio clínico exige aprobación/versionado de estudio.
- `/api/state`, `/api/collaboration`, `/api/study/participant-journey` y `/api/export/xlsx` leen registros persistidos y/o producen cálculos sobre ellos. No se detectó un bloque de estadísticas numéricas de participantes incrustado en el resumen principal: el problema principal son los centros estáticos y ciertos estados que no diferencian correctamente indisponibilidad y ausencia de datos.
- El formulario vacío de onboarding introduce un flujo de captura, **no** participantes. La persistencia usa peticiones al servidor; no se usa `localStorage` para simular guardados.
- La presencia de datos ficticios en fixtures de test no equivale a datos precargados en PostgreSQL staging.

## Siguiente implementación sin regresiones

1. **Centros reales (P0).** Crear tabla y CRUD de centros, lista vacía por defecto, validación de centro activo en todas las rutas; migración idempotente de referencias existentes de invitación sin inventar sedes. No desplegar frontend y backend de forma desincronizada.
2. **Identidad e invitaciones.** Alta de investigador con enlace de un solo uso, activación, suspensión, roles, centro asociado y auditoría persistida. Probar por cada centro y con revisor de sólo lectura.
3. **Veracidad del dato.** Revisar cada cuadro: `loading` / `empty` / `error` / `success`. Una API fallida nunca se convierte en “0 registrados” ni se conserva un resultado obsoleto como actual.
4. **Datos de prueba introducidos por usuario.** Flujo de extremo a extremo: centro nuevo → invitación → cuenta → participante SIM → V0/V1/V2 → episodio/contacto → CRD → indicadores → exportación → auditoría. Todos los cambios deben sobrevivir cierre de sesión y reinicio del proceso.
5. **Seguridad y rigor.** Verificar aislamiento real de centro, registro de consentimiento sintético, reversibilidad, RLS/permisos del esquema privado, procedimiento de datos y requisitos CEIC antes de uso clínico.

## Criterios de aceptación

- Un administrador puede crear un centro que **no exista en ningún array del frontend o backend**, y ese centro se ofrece inmediatamente en las invitaciones.
- Sin centros registrados, el panel indica **0 centros** con acción de alta, nunca tres sedes ficticias.
- Un investigador sólo ve participantes de su centro; un revisor no puede editar, incluso llamando a la API directamente.
- Ninguna fila de participante, visita, evento o resultado aparece sin su correspondiente registro persistido.
- Guardar, recargar y exportar reflejan exactamente los mismos valores, sin datos de muestra ocultos.
- Una respuesta fallida del backend presenta error recuperable, no cifras de cero ni información obsoleta.
- Los fixtures son exclusivamente locales/CI y la configuración de staging rechaza precarga automática.
- El catálogo clínico se mantiene intacto y versionado.
- El entorno permanece explícitamente **sintético** hasta que existan aprobaciones y medidas institucionales adecuadas.

> **Estado de este PR:** primera corrección segura de presentación y limpieza del frontend, junto a auditoría de fuentes. La sustitución de los centros ficticios y sus dependencias es el siguiente cambio estructural; no se declara implementada ni probada en esta rama.
