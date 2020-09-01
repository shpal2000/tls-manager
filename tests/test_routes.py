from functools import lru_cache
from fastapi.testclient import TestClient
from .. import main, config, crud

import pdb

client = TestClient(main.app)

@lru_cache
def get_settings():
    settings = config.Settings(db_file='tlspack_test.db')
    crud.create_tables (settings.db_file)
    return settings

main.app.dependency_overrides[main.get_settings] = get_settings 

def test_start_cps():
    response = client.post('/start_cps', json={"runid" : "cps_trial", "cipher" : "AES128_SHA", "cps" : 10 })
    assert response.status_code == 200
    assert response.json() == {"runid" : "cps_trial", "cipher" : "AES128_SHA", "cps" : 10 }

    response = client.get('/show_runs')
    assert response.status_code == 200
    assert response.json() == {'runs': [ {"id" : "cps_trial"} ]}

def test_stop():
    response = client.post('/stop', json={"runid" : "cps_trial"})
    assert response.status_code == 200
    assert response.json() ==  {"runid" : "cps_trial" }

    response = client.get('/show_runs')
    assert response.status_code == 200
    assert response.json() == {'runs': []}
