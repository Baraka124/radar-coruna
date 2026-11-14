# RADAR-CORUÑA v0.40 · Guía de preproducción

La guía completa, verificable y mantenida junto al código se encuentra en `OPERACION_V40.md` dentro del ZIP.

El punto clave es que RADAR-CORUÑA se distribuirá **como aplicación independiente**, no dentro de neumDESK/neumuacFQ. La opción de staging puede ejecutarse en un contenedor Linux con un **único worker y una réplica**, un volumen persistente y un dominio HTTPS propio. La configuración separa tajantemente la simulación del despliegue clínico de datos reales.

## Pasos de puesta en marcha

1. Crear un servicio nuevo y un volumen dedicado, sin copiar los usuarios demo de la instalación local.
2. Configurar los secretos y rutas descritos en `.env.synthetic-staging.example` usando el gestor de secretos del proveedor. **No utilizar la contraseña de ejemplo.**
3. Desplegar desde `Dockerfile`. En Railway, establecer el health check `/api/ready` desde los ajustes del servicio o su infraestructura como código vigente. Los archivos `railway.json` de Config as Code están obsoletos para servicios nuevos.
4. Abrir la URL HTTPS elegida y probar invitación, acceso de investigador, aislamiento entre centros, edición, exportación, suspensión de acceso y restauración verificada.
5. Configurar supervisión externa continua y copias cifradas separadas del volumen activo.

Este paquete **no ha ejecutado el despliegue** ni se ha conectado a una infraestructura externa. La migración PostgreSQL y los ensayos en entorno final son tareas posteriores.

Documentación de referencia: https://docs.railway.com/deployments/healthchecks y https://docs.railway.com/config-as-code
