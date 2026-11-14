# Instalación y actualización a v0.28

1. Conserve una copia del paquete anterior y, si ya contiene registros, de la base SQLite usada en v0.27.
2. Extraiga `RADAR_CORUNA_MVP_v28` en una carpeta independiente. No sobreescriba sus archivos originales.
3. Para conservar los registros, copie su archivo `.sqlite3` anterior o mantenga la configuración existente de `RADAR_DB`. El esquema no cambia en v0.28.
4. Abra PowerShell dentro de esa carpeta e instale dependencias solo si es necesario: `py -m pip install -r requirements.txt`.
5. Ejecute `py start_local.py` y abra `http://127.0.0.1:8878/`.
6. Desde **Participantes**, abra una ficha: encontrará **Revisión longitudinal** debajo de **Recorrido del participante**. Compruebe una ficha con V0/V1/V2, episodios y contactos y después la descarga Excel.
7. Para repetir la aceptación técnica: `py -m pytest -q tests/test_phase28_journey.py` y `py tests/browser_phase28_journey.py` (navegador automatizado opcional).

La revisión es derivada y de solo lectura; no requiere migración ni convierte ausencias en respuestas «No».
