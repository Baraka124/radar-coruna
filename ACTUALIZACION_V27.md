# Instalación/actualización a RADAR-CORUÑA v0.27

1. Conserve una copia íntegra de su instalación y base de datos anterior.
2. Extraiga el paquete nuevo `RADAR_CORUNA_MVP_v27` en una carpeta propia.
3. Si desea mantener los registros, copie únicamente su archivo SQLite de la instalación v0.26 al paquete nuevo. El arranque crea los nuevos campos opcionales al guardar, sin borrar los valores existentes. Use la misma configuración `RADAR_DB` si ya apunta a un archivo persistente.
4. Ejecute `py -m pip install -r requirements.txt` (si no dispone de dependencias) y `py start_local.py`.
5. Abra `http://127.0.0.1:8878/` y pruebe un participante y V0: inclusión, Charlson, vacunación, evaluador, R107 y exportación.
6. Compare el fichero JSON de concordancia con el protocolo y diccionario si va a introducir nuevos campos.

No sobrescriba una base de datos con un Excel: la plantilla es solo una exportación vacía y editable. La numeración de episodios y el historial de cambios se conservan.
