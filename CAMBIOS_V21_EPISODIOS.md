# RADAR-CORUÑA · v0.21 · Identificación de episodios y contactos (R074)

**Alcance**: prototipo local con datos ficticios. Se parte del paquete íntegro v0.20; no se habilita información clínica real.

- Un episodio recibe **número R074 consecutivo por participante** (01, 02, 03…). Lo genera el servidor al guardar, no el clínico; el ID interno se conserva independiente.
- Se incorpora R076: `agudizacion` u `otro` con `no_aplica` para gravedad en «otro evento».
- Migración no destructiva: registros sintéticos previos sin R074 reciben número estable en orden histórico de inserción, con registro `MIGRATE` en trazabilidad. Identificadores y vínculos previos se mantienen.
- Contactos de Urgencias e ingreso se vinculan mediante identificador interno al episodio del **mismo participante**. UI muestra el R074, no el ID técnico. Acceso rápido «+ Contacto» desde el episodio.
- Dos contactos pueden compartir fecha y tipo; no se descartan automáticamente si son encuentros diferentes. Se mantiene auditoría y revisión científica de posibles duplicados.
- Exportación: nuevas columnas `episodeNo`, `kind` y `relatedEpisodeNo` sin desplazar las columnas previas. El total de episodios no se incrementa por cada contacto asociado.
- Los datos históricos anteriores siguen válidos; fechas, clasificación del evento y atribución a EPOC siguen sujetos a validación científica.

- La pestaña «CRD complementario» habilita la recogida de las diez actuaciones R090–R099 (Sí/No/No aplica/No consta), con visita V0/V1/V2, permisos y auditoría. Los campos de actuaciones previos del MVP se conservan para compatibilidad histórica y no se convierten silenciosamente.
- Se registran centro asistencial y fecha de alta **opcionales** en contactos simulados, con validación temporal básica.
- Los indicadores descriptivos de agudizaciones excluyen los eventos de tipo «otro» (sin eliminar esos eventos de la relación de episodios).
- El panel de episodios y el de contactos ocupan toda la anchura disponible para evitar columnas recortadas; acceso directo «+ Contacto» desde el episodio.

**Límites explícitos**: el CRD R081/R082 permite Sí/No/NC para cada episodio; esta versión aún registra contactos constatados, no estados negativos/NC por cada uno. El catálogo ya referencia R074 como Episode.episodeNo, y R090–R099 como observaciones por visita; no implica todavía concordancia plena de las 107 variables.

**Pendiente**: reconciliar los campos restantes de CRD y 107 variables, validar reglas finales de eventos, completar la codificación de actuaciones clínicas, revisar permisos/seguridad institucional antes de producción y terminar el protocolo IANUS. No usar datos reales.
