
def test_check_key_cors(client):
    res = client.options('/upload/check_key')
    assert res.headers["Access-Control-Allow-Origin"] == "*"

def test_check_key_no_key(client):
    res = client.get('/upload/check_key')
    assert res.status_code == 401

def test_check_key_invalid_key(client, device):
    res = client.get('/upload/check_key?key=asdf')
    assert res.status_code == 401

def test_check_key_valid_key(client, device):
    res = client.get('/upload/check_key?key='+device.upload_key)
    assert res.status_code == 200


def test_check_manifest_user(admin_client):
    res = admin_client.post('/upload/check_manifest', json={
        "deviceName": "testDevice",
        "night": "2026-01-01",
        "files": {}
    })
    assert res.status_code == 200
    
def test_check_manifest(client, device):
    res = client.post('/upload/check_manifest?key='+device.upload_key, json={
        "deviceName": "testDevice",
        "night": "2026-01-01",
        "files": {}
    })
    assert res.status_code == 200
    
