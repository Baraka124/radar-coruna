# RADAR-CORUÑA · v0.38 — Red multicéntrica y gestión de colaboradores

**Versión de partida:** v0.37. **Fecha:** 12/11/2026. **Tipo:** candidato de simulación local, sin datos clínicos reales, sin despliegue remoto.

## 1. Implementación

Esta versión añade una capa real de colaboración a la API y a la interfaz, sobre el modelo clínico conservado:

1. **Red de centros:** sección «Red de centros» en navegación lateral, con actividad resumida por centro y estado de cuentas. La coordinación general ve las tres sedes sintéticas; un investigador o revisor asignado sólo ve la suya.
2. **Invitación desde administración:** elección de centro y rol (`investigator` o `reviewer`), enlace de activación mediante secreto aleatorio de un solo uso, caducidad a las 72 horas y revocación mientras siga pendiente. Sólo el administrador global emite invitaciones.
3. **Alta personal:** el invitado elige nombre de usuario y contraseña (mínimo 12 caracteres). El centro y el rol vienen del servidor y no son editables en el alta. La contraseña se guarda como hash Argon2. La invitación se consume transaccionalmente.
4. **Cuentas y ciclo de vida:** el administrador puede suspender y reactivar cuentas no administradoras. Suspender borra las sesiones activas e impide nuevos inicios de sesión; no elimina registros históricos.
5. **Separación multicéntrica:** participantes, visitas, CRD, listas de trabajo, cuadros de calidad y Excel permanecen filtrados en la API; los metadatos de centros del Excel se restringen también al centro autorizado. Los revisores carecen de permisos de edición.

## 2. Controles de seguridad aplicados

- `invitations.token_hash`: SHA-256 del secreto; nunca se guarda la URL de invitación en texto claro.
- Enlace de cliente en fragmento `#invite=` para evitar que el secreto forme parte de la ruta HTTP.
- El enlace se presenta sólo en la respuesta inicial de creación; no se devuelve en los listados administrativos y la interfaz descarta su copia al abandonar la sección o cerrar sesión.
- El servidor verifica el rol para toda mutación administrativa y CSRF para solicitudes autenticadas.
- Para el alta sin sesión previa se comprueba el origen del navegador y el tipo de contenido JSON. El secreto aleatorio debe ser válido, no usado, no revocado y no caducado.
- Las nuevas cuentas se asignan a **un único centro**; no pueden elegir centro en una petición posterior.
- Las sesiones se vuelven inválidas tras la suspensión. No se permite desactivar la propia cuenta administrativa desde este módulo.
- Se mantiene el registro de auditoría con eventos `INVITE`, `ACCEPT`, `REVOKE`, `ACTIVATE` y `DEACTIVATE`.
- Migración SQLite no destructiva: añade `users.active` y crea `invitations` conservando cuentas anteriores.

## 3. Rutas API nuevas

| Método y ruta | Autoridad |
|---|---|
| `GET /api/collaboration` | Cualquier sesión; resultados filtrados por centro. Administración global ve cuentas e invitaciones |
| `POST /api/collaboration/invitations` | Administrador global |
| `POST /api/collaboration/invitations/{id}/revoke` | Administrador global |
| `POST /api/collaboration/accept` | Usuario sin autenticar, con secreto válido de un solo uso |
| `PATCH /api/collaboration/accounts/{id}` | Administrador global, excepto su propia cuenta |

## 4. Verificación concluida

- **9/9 pruebas específicas v0.38**, incluidas invitación, uso único, caducidad, revocación, acceso de revisor, bloqueo por centro, suspensión, dos sesiones simultáneas y comprobación de XML exportado a Excel.
- **36/36 pruebas focalizadas** del conjunto v0.38 + fiabilidad v0.29 + inteligencia clínica v0.32/v0.33.
- **Navegador v0.38:** 5 anchuras (320, 390, 768, 1057, 1440 px), creación y aceptación de invitación, acceso con nueva cuenta, visibilidad de una sola sede, diseño sin desbordamiento horizontal, sin excepciones JavaScript.
- **Navegador histórico v0.37:** 5 anchuras, evaluación longitudinal, reutilización explícita, protección de borradores y guardado hacia CRD; todo correcto.
- **Regresión histórica Python:** 93 casos en 19 archivos llegaron a completarse con resultado positivo de forma individual antes de un nuevo atasco del lanzador; no se ha certificado la ejecución agregada de toda la suite. Consulte `RESULTADOS_PRUEBAS_V38.txt`.

## 5. Lo que NO significa esta versión

El servidor sigue restringido a **localhost** y sólo admite centros/códigos sintéticos. La activación por enlace existe y está probada en un mismo servidor local, pero los investigadores de otros centros **no pueden acceder remotamente a este ZIP**. No hay correo saliente, dominio público, MFA, recuperación de contraseña, alta de centros reales ni pruebas de concurrencia distribuida/de despliegue de larga duración. Son requisitos posteriores de infraestructura y operación. No se debe usar este paquete como servicio clínico en producción.

No se han alterado las fórmulas RADAR, la estructura de V0–V2, las reglas de elegibilidad, las revisiones longitudinales ni el CRD. **v0.37 y anteriores permanecen intactas.**
