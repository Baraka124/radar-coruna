# Actualización a RADAR-CORUÑA v0.24

1. Extrae el paquete `RADAR_CORUNA_MVP_v24` en una nueva carpeta.
2. Para conservar los registros introducidos en una versión anterior, detén ambas instancias, haz copia de seguridad y copia el archivo `radar_synthetic.sqlite3` desde la carpeta anterior a la nueva **antes de iniciar v0.24**. No incluyas este archivo en paquetes públicos.
3. Ejecuta `py -m pip install -r requirements.txt` y `py start_local.py`.
4. Abre `http://127.0.0.1:8878/`.

La v0.24 actualiza únicamente la interfaz y metadatos de versión. No cambia las tablas de datos ni reglas de cálculo. Si trabajas con otra ruta de SQLite definida por `RADAR_DB`, mantén esa configuración.

**Evaluación visual:** Resumen, Participantes, Visitas, Análisis y móvil. **Pruebas:** `python tests/browser_phase24_workspace.py` y `python -m pytest -q tests/test_phase20_crd_alignment.py tests/test_phase21_episodes_actions.py tests/test_phase22_episode_care.py tests/test_phase16_usability.py tests/test_phase19_release.py tests/test_phase14_completion.py tests/test_phase18_reporting.py`.
