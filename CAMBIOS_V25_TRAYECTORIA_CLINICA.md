# RADAR-CORUÑA v0.25 · Trayectoria clínica

## Alcance

- Pestañas horizontales discretas para saltar entre apartados de inclusión y V0/V1/V2.
- Agrupación explícita de los campos iniciales del formulario, sin alterar sus identificadores.
- Contexto de participante y fase en la cabecera de la evaluación.
- Enlace de retorno a la ficha, incluyendo apertura de visitas preexistentes desde el listado general.
- Ajustes de densidad, tipografía, foco y visualización móvil de secciones clínicas.

## Compatibilidad

Sin modificaciones de servidor, modelos, base de datos, reglas RADAR ni fórmulas. Los campos conservan sus IDs y la ruta de envío existente. Los datos de evaluación se mantienen al cambiar entre apartados del mismo formulario; siguen guardándose exclusivamente mediante el botón Guardar.
