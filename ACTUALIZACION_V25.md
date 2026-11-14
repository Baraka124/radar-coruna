# Actualización a RADAR-CORUÑA v0.25

1. Descomprimir el ZIP.
2. Para conservar registros anteriores, detener la aplicación y realizar una copia de seguridad de la base de datos.
3. Copiar la base de datos anterior `radar_synthetic.sqlite3` a la carpeta de la v0.25 **antes de iniciar**, si se utiliza esa ruta; si se usa `RADAR_DB`, conservar la misma configuración.
4. Ejecutar `py -m pip install -r requirements.txt` y `py start_local.py`.
5. Abrir `http://127.0.0.1:8878/`.

La versión v0.25 se limita a la presentación y navegación. No altera los datos persistidos ni los cálculos.
