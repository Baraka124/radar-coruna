# RADAR-CORUÑA · Guía rápida v0.38 — Colaboración en simulación

## Coordinación del estudio

1. Abrir el servidor local `http://127.0.0.1:8878/` e iniciar sesión como administrador de prueba.
2. Entrar en **Red de centros**. La cabecera presenta actividad agregada de cada uno de los tres centros ficticios y, debajo, las cuentas activas.
3. En **Invitar a un colaborador**, elegir el centro, **Investigador** (edición) o **Revisor** (consulta), e indicar una referencia de prueba sin datos personales reales.
4. Pulsar **Crear invitación**. Copiar el enlace secreto inmediatamente; dejará de mostrarse al abandonar la pantalla o cerrar sesión. Caduca transcurridas 72 horas y sólo se puede utilizar una vez.
5. En la tabla de invitaciones se puede **Revocar** una invitación aún pendiente. En la tabla de cuentas se puede **Suspender** una cuenta (invalida sus sesiones) o **Reactivar**.

## Alta e investigador

1. En el **mismo servidor local**, abrir el enlace de activación. No funcionará en un equipo de otro centro sin una futura instalación central accesible.
2. Elegir nombre de usuario y contraseña de al menos 12 caracteres. El enlace fija rol y centro; el invitado no los puede ampliar.
3. Iniciar sesión normalmente. En **Red de centros** se muestra únicamente la sede asignada. Desde **Participantes**, **Visitas**, **CRD** y **Excel** se accede sólo a registros autorizados.
4. El rol **Revisor** puede consultar y exportar según permisos de lectura, pero no crear ni modificar información clínica.

## Comprobaciones útiles

- Intentar abrir el código de participante de otro centro debe devolver **403** en la API, incluso usando manualmente una URL.
- Una segunda activación con el mismo enlace devuelve **410**.
- Tras suspender una cuenta, sus sesiones dejan de ser válidas, y no puede volver a entrar hasta su reactivación.
- La exportación de un investigador de un centro no incluye participantes ni metadatos de otras sedes.

Los registros de este entorno son **exclusivamente sintéticos**. La instalación local es una prueba de los mecanismos de colaboración, no un despliegue multicéntrico accesible por Internet.
