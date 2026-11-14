# RADAR-CORUÑA · v0.40
## Cierre de desarrollo de la hoja de ruta · Candidato de preproducción sintética

**Fecha:** 13 de noviembre de 2026  
**Base preservada:** v0.39 · Inteligencia de datos de investigación  
**Tipo de entrega:** código fuente y procedimientos operacionales, **sin desplegar** y **sin datos de pacientes reales**.

### Resultado implementado

La aplicación conserva todos los módulos clínicos y de colaboración de v0.39. La versión v0.40 introduce un modo explícito de preproducción **exclusivamente sintética**: dominio HTTPS declarado, comprobación de origen y host, cookies de sesión `HttpOnly`, `Secure` y `SameSite=Strict`, protección CSRF, limitación de intentos de inicio de sesión, cuenta inicial con contraseña individual proporcionada como secreto, denegación de las credenciales demo conocidas y exclusión de la siembra sintética de demostración. Rechaza configuraciones de producción clínica no soportadas.

También incorpora sonda de disponibilidad SQLite, identificador de solicitud, registros operativos con rutas normalizadas, limitación de la instancia SQLite a un proceso por bloqueo de fichero POSIX (no distribuido), empaquetado de contenedor, configuración de ejemplo y guía de puesta en marcha/recuperación. Los enlaces de invitación, la suspensión de cuentas, las reglas de centro, la captura longitudinal y el análisis siguen disponibles.

### Evidencia obtenida

| Prueba | Resultado |
|---|---|
| Regresión Python, cuatro tandas independientes | **150/150 pruebas, 26/26 ficheros** |
| Seguridad y operaciones, grupo ampliado | **47/47** |
| Núcleo clínico, CRD, episodios, exportaciones | **41/41** |
| Flujos históricos, aceptación y resultados | **20/20** |
| Concordancia, portabilidad, estudio | **42/42** |
| Navegador, interfaz general | 12 secciones × 5 anchuras, correcto |
| Navegador, clínica v0.37 | 5 anchuras, correcto |
| Navegador, invitaciones v0.38 | 5 anchuras, correcto |
| Navegador, analítica v0.39 | 5 anchuras, correcto |
| Simultaneidad sintética | 12 sesiones; 48 lecturas autorizadas; 10 altas concurrentes de dos centros, correctas |
| Escrituras en conflicto | Una aceptada, segunda rechazada con HTTP 409 por revisión antigua |
| Copia, restauración y alteración | SHA-256, integridad SQLite, restauración independiente y detección de alteración, correctas |

**Rigurosidad del reporte:** las 150 pruebas se completaron en cuatro tandas separadas; una reejecución conjunta se atascó y **no** se cuenta como éxito adicional. Dos expectativas históricas obsoletas fueron corregidas para el contrato vigente de v0.39–v0.40 (nombre del entorno y 44 hojas Excel para investigadores).

### Límites técnicos expresos

- **No se ha desplegado** un servidor público, ni se ha probado un dominio real con TLS. `Dockerfile` es una receta de despliegue **no construida ni probada en este entorno**.
- SQLite y el bloqueo POSIX hacen viable una demostración sintética de una sola instancia; **no** equivalen a una base de datos multicentro escalable. No existe migración PostgreSQL verificada.
- No se ha realizado una prueba de carga distribuida, resistencia prolongada ni recuperación de caída real de proveedor/región.
- No se ha implementado MFA, recuperación de cuenta institucional, gestión completa de secretos y auditoría operativa de un entorno de pacientes reales.
- Permanecen pendientes las decisiones científicas documentadas y la aceptación práctica por investigadores.

### Qué queda tras v0.40

**No quedan más fases de desarrollo dentro de la serie acordada v0.36–v0.40.** El trabajo restante son hitos de implantación y validación:

1. Desplegar un **staging sintético independiente** en una infraestructura y dominio elegidos; verificar HTTPS, volumen persistente, usuarios, rutas, exportaciones, copias y monitorización en ese servidor.
2. Para uso asistencial/investigador con datos reales, migrar completamente el backend a PostgreSQL o arquitectura institucional equivalente, incorporar identidad/MFA, continuidad y auditoría exigidas, y repetir pruebas de carga, recuperación, permisos y seguridad en la infraestructura definitiva.
3. Ejecutar la aceptación de investigadores con Manuel y Pedro, conciliar los asuntos metodológicos abiertos y completar las autorizaciones institucionales/científicas exigibles antes de la recogida real.

**Conclusión:** v0.40 completa el **desarrollo y la comprobación local** del plan; la plataforma es un candidato sólido de preproducción sintética, **no** una instalación clínica finalizada.
