"""Safe localhost-only launcher for the synthetic research pilot."""
from __future__ import annotations
import os
import uvicorn

if __name__=='__main__':
    port=int(os.getenv('RADAR_PORT','8878'))
    if not 1024<=port<=65535:raise ValueError('Puerto no válido (1024-65535)')
    uvicorn.run('server:app',host='127.0.0.1',port=port,access_log=False,proxy_headers=False)
