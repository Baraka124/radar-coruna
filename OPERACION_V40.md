# RADAR-CORUÑA v0.40 — Preparación operacional y prueba multicéntrica sintética

**Estado:** candidato técnico de *staging sintético de una sola instancia*. **No desplegado por este paquete.** No es una aplicación autorizada ni técnicamente certificada para datos de pacientes reales. `RADAR_MODE=production` se rechaza expresamente.

## 1. Alcance de v0.40

Conserva la interfaz y API clínica/analítica v0.39; añade una configuración separada para comprobación remota **solo sintética**, medidas de seguridad de acceso, registros operativos sin datos clínicos, prueba de simultaneidad por centro, verificación de copias y bloqueo de segunda instancia sobre el mismo fichero SQLite.

- **Local demo:** `RADAR_MODE=local_demo` (por defecto), `python start_local.py`, sólo 127.0.0.1; cuentas de demostración históricas en bases recién creadas.
- **Staging sintético remoto:** `RADAR_MODE=synthetic_staging`, dominio de origen HTTPS y volumen persistente explícitos; **no** genera usuarios de demostración. Crea una cuenta administrativa inicial con contraseña segura, individual y suministrada como secreto. La sesión usa cookie `HttpOnly`, `Secure`, `SameSite=Strict`; escrituras requieren CSRF y origen esperado. Aplica límite de fallos de inicio de sesión. Devuelve `X-Request-ID` y logs con plantilla de ruta sin códigos clínicos ni URL original.
- **Producción clínica:** no implementada. El sistema rechaza cualquier modo de producción; no se puede sustituir mediante renombrar una variable de entorno.

## 2. Configuración de staging (ejemplo Railway u otro proveedor de contenedores Linux)

1. Crear un servicio **nuevo e independiente**. **No reutilizar** los proyectos neumDESK, neumuacFQ ni una base existente. No introducir datos reales.
2. Construir desde `Dockerfile`; en un servicio Railway nuevo, configurar build, health check y réplica **desde el panel o el nuevo sistema IaC** (los archivos `railway.json` heredados ya no sirven para nuevos servicios en noviembre de 2026). Una sola réplica, un solo worker y ninguna estrategia de escalado horizontal. Asignar volumen persistente **dedicado** montado en `/data`; la cuenta del contenedor (`UID 10001`) debe disponer de lectura/escritura en el volumen. En plataformas que no garantizan esa propiedad, ajustar permisos antes de arrancar.
3. Configurar TLS en el proxy de entrada y un dominio exclusivo. Añadir las variables de `.env.synthetic-staging.example` mediante secretos del proveedor, con `RADAR_PUBLIC_ORIGIN=https://dominio-exacto`; nunca publicar el ejemplo con la contraseña de marcador de posición. No utilizar credenciales demo ni copiar a staging una base local existente que las contenga.
4. Configurar el health check `GET /api/ready` (comprueba SQLite y existencia de cuentas). Se acepta `Host: healthcheck.railway.app` **solo** para esa ruta de lectura, ya que Railway usa ese hostname en sus sondas de despliegue. Railway no supervisa continuamente el health check después de activar el despliegue; usar una sonda externa. Con volumen montado puede haber una breve interrupción durante la sustitución del despliegue. `GET /api/health` devuelve la versión y el tipo de entorno. El servidor deniega cualquier `Host` distinto del dominio configurado y cualquier escritura sin el `Origin` esperado.
5. Verificar manualmente inicio de sesión, invitación de un investigador por centro, aislamiento al consultar ID ajeno, exportación por centro, suspensión de cuenta y consistencia del libro Excel. Registrar la URL de staging y la revisión Git en acta de prueba.
6. No activar un segundo servicio, contenedor, worker o réplica apuntando al mismo fichero. La protección POSIX solo evita duplicaciones **en el mismo host**; no sustituye bloqueo distribuido ni base transaccional de servidor.

**Ejemplo de comprobación sin credenciales:** `curl -fsS https://DOMINIO/api/ready` (solo después del despliegue voluntario). `RADAR_PUBLIC_ORIGIN` exige HTTPS y no admite rutas, query ni credenciales.

## 3. Copia, restauración y rollback

En una instancia de staging autorizada a tal fin, montar un **segundo volumen/almacenamiento de copias** distinto del directorio de datos. Ejecutar bajo acceso de operador (no desde endpoints públicos):

```bash
python backup_manager.py backup --db /data/radar_synthetic.sqlite3 --out /backups
python backup_manager.py verify /backups/RADAR_CORUNA_backup_<FECHA>.json
python backup_manager.py restore-new /backups/RADAR_CORUNA_backup_<FECHA>.json --target /data_restore/radar_synthetic.sqlite3
```

`restore-new` se niega a reemplazar una base existente y verifica `PRAGMA integrity_check`, los totales seleccionados y el SHA-256. **Nunca cambiar el fichero activo durante una sesión.** Para rollback, detener el servicio, comprobar instantánea y respaldo de datos/migraciones, restaurar en ubicación nueva y efectuar conmutación controlada; verificar sesión, centro, export y auditoría antes de reabrir. Proteger las copias porque incluyen hashes de credenciales, sesiones y auditoría. No basta con guardar las copias en el mismo volumen de la aplicación. Confirmar retención, cifrado, replicación y periodicidad en el entorno elegido.

## 4. Monitoreo y respuesta operativa

- Verificar `/api/ready` y recibir alertas externas por errores 5xx/estado no disponible; la API no envía alertas autónomas.
- Observar tiempo de respuesta, reinicios y errores mediante los logs JSON `radar_http` (método, plantilla de ruta, estado, duración, ID). **No** se registran pacientes, URL solicitadas, cuerpos, cookies, tokens ni IP.
- Cada actualización requiere copia verificada previa, pruebas dirigidas, comprobación de versión `0.40.0`, verificación de centro de investigación y plan de reversión.
- Probar recuperación periódicamente en base separada y registrar resultados. Una copia verificada en local no prueba recuperación ante caída de región o proveedor.

## 5. Pruebas reproducibles

```bash
python -m pytest -q tests/test_phase40_operations.py
python -m pytest -q tests/test_phase38_multicentre.py tests/test_phase39_intelligence.py
python scripts/v40_regression.py --group operational_and_recent --timeout 60
python scripts/v40_regression.py --group clinical_core --timeout 60
python scripts/v40_regression.py --group historical_workflows --timeout 60
python scripts/v40_regression.py --group concordance_portability --timeout 60
```

Ejecute **una tanda por proceso**, no todas las tandas en paralelo. En esta sesión el orquestador conjunto volvió a bloquearse, mientras las cuatro tandas ejecutadas por separado terminaron correctamente. La suite nueva prueba inicio seguro, cookies, CSRF/origen, invitaciones, aislamiento, limitación de intentos, rechazo de la base demo, sesiones, 12 usuarios concurrentes sobre una instancia, respaldo, restauración y detección de alteración del backup. El informe de pruebas indica qué regresiones históricas pudieron finalizar; no confundir tiempos locales con capacidad productiva.

## 6. Condiciones pendientes para producción clínica multicéntrica

- Persistencia en **PostgreSQL transaccional** con migración comprobada de todas las tablas, campos JSON y auditoría. El backend actual está implementado con sentencias y operadores SQLite; no se considera migrado simplemente aportando una URL `DATABASE_URL`.
- Políticas de identidad institucional: MFA, recuperación de cuenta, gestión de secretos, sesiones, bloqueo de accesos y trazabilidad operativa bajo la arquitectura elegida.
- Infraestructura con TLS, almacenamiento y backups cifrados, supervisión, retención, pruebas de caída y restauración, SLA/SLO acordados y automatización de despliegue.
- Ensayo de carga en la infraestructura final: múltiples centros, escrituras y conflictos concurrentes, exportaciones, latencia, reinicios y volumen de datos previsto. Las pruebas locales no sustituyen este ensayo.
- Conciliación final de 107 variables, criterios de elegibilidad pendientes y definición IANUS con dirección científica, así como aceptación formal de investigadores. La validación científica y ética es una decisión adicional, no una funcionalidad del software.

**Resultado técnico defendible:** v0.40 es un candidato de staging sintético controlado; **no** equivale a producción clínica ni a un despliegue que se haya realizado.

Referencias para configurar Railway (consultadas en noviembre de 2026): https://docs.railway.com/config-as-code y https://docs.railway.com/deployments/healthchecks .
