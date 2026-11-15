"""Legacy test compatibility: load fictional centres in TEST DATABASES only.

Production/staging application startup never creates these centres.
The v0.45 registry tests are explicitly excluded to verify an empty registry.
"""
import pytest


@pytest.fixture(autouse=True)
def legacy_test_centre_registry(request, monkeypatch):
    if request.module.__name__.endswith('test_centres_v45'):
        yield
        return

    import server

    original_init = server.init_db

    def init_with_local_test_centres():
        original_init()
        if server.POSTGRES_MODE:
            return
        # All test clients use isolated temporary SQLite databases.
        with server.conn() as c:
            for code, name in (
                ('SIM-CS01', 'Centro de ensayo Costa'),
                ('SIM-CS02', 'Centro de ensayo Interior'),
                ('SIM-CS03', 'Centro de ensayo Urbano'),
            ):
                if not c.execute('SELECT 1 FROM centres WHERE code=?', (code,)).fetchone():
                    c.execute(
                        'INSERT INTO centres(code,name,active,created_at,updated_at,created_by) '
                        'VALUES (?,?,?,?,?,?)',
                        (code, name, True, server.now(), server.now(), 'pytest_fixture'),
                    )

    monkeypatch.setattr(server, 'init_db', init_with_local_test_centres)
    yield
