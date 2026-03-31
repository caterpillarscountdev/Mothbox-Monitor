from mothmonitor.models import Device, db

def test_devices_list_no_auth(client, device):
    res = client.get('/devices/list')
    assert res.status_code == 302
    assert res.headers["Location"].startswith("/auth/login")


def test_devices_list(admin_client, device):
    res = admin_client.get('/devices/list')
    assert res.status_code < 300
    assert device.label
    assert f'<td>{device.label}' in res.text


def test_device_create_key_new(admin_client):
    res = admin_client.post('/devices/create_key')
    assert res.status_code < 300
    d = list(db.session.execute(db.select(Device)).scalars())
    assert len(d) == 1
    assert d[0].upload_key != ''

def test_device_check_config(client, device):
    res = client.post(f"/devices/check_config?key={device.upload_key}", json={
        "config": {"metadata": {"SiteName": "Test Site"}}
    })
    assert res.status_code < 300
    assert res.json["received"] == "config"
    
    assert "metadata" in device.remote_config
    assert device.remote_config["metadata"]["SiteName"] == "Test Site"
