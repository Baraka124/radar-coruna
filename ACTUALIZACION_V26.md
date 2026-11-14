# Actualización RADAR-CORUÑA v0.26

1. Detener la aplicación de la versión anterior.
2. Realizar una copia de seguridad de su archivo SQLite existente.
3. Descomprimir el paquete nuevo sin sobrescribir la copia de seguridad.
4. Si se utiliza `radar_synthetic.sqlite3`, copiar ese archivo a la carpeta nueva antes de iniciar; con `RADAR_DB`, mantener la ruta configurada.
5. Ejecutar `py -m pip install -r requirements.txt`, luego `py start_local.py`.
6. Abrir `http://127.0.0.1:8878/`.

Esta actualización no requiere migración de tablas. Los borradores de formulario se conservan solo mientras permanece abierta la página; hay que pulsar Guardar mediciones para confirmarlos.
