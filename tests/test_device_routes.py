from mothmonitor.models import db, Device, User


def test_devices_list_no_auth(client, device):
    res = client.get('/devices/list')
    assert res.status_code == 302
    assert res.headers["Location"].startswith("/auth/login")


def test_devices_list(admin_client, device):
    res = admin_client.get('/devices/list')
    assert res.status_code < 300
    assert device.label
    assert f'<td>{device.label}' in res.text

def test_devices_show(admin_client, device):
    res = admin_client.get('/devices/show/1')
    assert res.status_code < 300
    assert device.label
    assert f'<td>{device.label}' in res.text
    
    
def test_devices_detail(admin_client, device):
    device.code_version = "Fw-0.1.8"
    res = admin_client.get('/devices/detail/1')
    assert res.status_code < 300
    assert device.code_version
    assert f'{device.code_version}' in res.text

def test_device_detail_with_config(admin_client, device):
    device.remote_config = {
        "metadata": {
            "SiteName": "Test Site"
        },
        "schedule": {
            "hour": "21;23;3",
            "weekday": "2;4;6",
            "minute": "0",
            "camera_interval": "10",
            "runtime": "59"
            
        }
    }
    res = admin_client.get('/devices/detail/1')
    assert res.status_code < 300
    assert f'{device.remote_config["schedule"]["runtime"]}</em> minutes' in res.text
    assert f'Tuesday, Thursday, Saturday' in res.text


def test_device_edit(admin_client, device):
    res = admin_client.post(f'/devices/edit/{device.id}', data={
        "label": "Green Giant"
    })
    assert res.status_code < 300
    d = db.session.execute(db.select(Device)).scalar()
    assert d.label == 'Green Giant'
    
def test_device_edit_users(admin_client, device, site_user):
    d = list(db.session.execute(db.select(User)).scalars())
    assert len(d) == 2
    assert len(device.site_users) == 0
    res = admin_client.post(f'/devices/edit/{device.id}', data={
        "label": "Green Chair",
        "site_users": [site_user.id],
    })
    assert res.status_code < 300
    d = db.session.execute(db.select(Device)).scalar()
    assert d.label == 'Green Chair'
    assert len(d.site_users) == 1

def test_device_edit_users_and_remove(admin_client, device, site_user):
    d = list(db.session.execute(db.select(User)).scalars())
    assert len(d) == 2
    assert len(device.site_users) == 0
    res = admin_client.post(f'/devices/edit/{device.id}', data={
        "site_users": [site_user.id],
    })
    assert res.status_code < 300
    d = db.session.execute(db.select(Device)).scalar()
    assert len(d.site_users) == 1
    res = admin_client.post(f'/devices/edit/{device.id}', data={
        "site_users": [],
    })
    assert res.status_code < 300
    d = db.session.execute(db.select(Device)).scalar()
    assert len(d.site_users) == 0
    
    
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

def test_device_check_config(client, device):
    res = client.post(f"/devices/check_config?key={device.upload_key}", json={
        "config": {"metadata": {"SiteName": "Test Site"}},
        "code_version": "test-123",
    })
    assert res.status_code < 300
    assert "config" in res.json["received"]
    assert "code_version" in res.json["received"]
    assert "updated_config" not in res.json
    
    assert "metadata" in device.remote_config
    assert device.remote_config["metadata"]["SiteName"] == "Test Site"
    assert device.code_version == "test-123"

def test_device_check_config_with_logs(client, device):
    res = client.post(f"/devices/check_config?key={device.upload_key}", json={
        "config": {"metadata": {"SiteName": "Test Site"}},
        "code_version": "test-123",
        "recent_logs": {"Scheduler": "text"}
    })
    assert res.status_code < 300
    assert "recent_logs" in res.json["received"]
    
    assert 'Scheduler' in device.recent_logs

def test_device_check_config_with_updates(client, device):
    device.updated_config = {"metadata": {"SiteCrew": "New Crew"}}
    res = client.post(f"/devices/check_config?key={device.upload_key}", json={
        "config": {"metadata": {"SiteName": "Test Site"}},
    })
    assert res.status_code < 300
    assert "config" in res.json["received"]
    assert "updated_config" in res.json
    assert res.json["updated_config"] == {"metadata": {"SiteCrew": "New Crew"}}
    
def test_device_check_config_with_updates_applied(client, device):
    device.updated_config = {"metadata": {"SiteCrew": "New Crew"}}
    res = client.post(f"/devices/check_config?key={device.upload_key}", json={
        "config": {"metadata": {"SiteName": "Test Site", "SiteCrew": "New Crew"}},
    })
    assert res.status_code < 300
    assert "config" in res.json["received"]
    assert "updated_config" not in res.json
    assert device.updated_config == None
    
