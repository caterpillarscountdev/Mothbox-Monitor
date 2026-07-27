import os
import pytest
from datetime import datetime
from mothmonitor.models import db, Device, User, Night
from mothmonitor import antenna

api_base = "http://api.test/api/v2"


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("ANTENNA_URL", "http://api.test/")
    monkeypatch.setenv("ANTENNA_PROJECT_ID", "1")
    monkeypatch.setenv("ANTENNA_API_TOKEN", "abcd")

def test_antenna_build_url():
    a = antenna.AntennaAPI()

    assert a.build_url("/deployments/1") == "http://api.test/api/v2/deployments/1"

def test_antenna_build_url_no_api():
    a = antenna.AntennaAPI()

    assert a.build_url("/project/1", api=False) == "http://test/project/1"
    

def test_antenna_client_deployments(requests_mock):
    a = antenna.AntennaAPI()

    requests_mock.get(f"{api_base}/deployments/?project_id=1", json={"count": 2, "results": [{"id": 1}]})

    r = a.deployments()

    assert requests_mock.called
    assert requests_mock.request_history[0].url == f"{api_base}/deployments/?project_id=1"
    assert requests_mock.request_history[0].headers["Authorization"] == "Token abcd"

    assert r == [{"id": 1}]

def test_antenna_client_get_deployment(requests_mock):
    a = antenna.AntennaAPI()

    requests_mock.get(f"{api_base}/deployments/1/", json={"id": 1})

    r = a.deployment(1)

    assert requests_mock.called
    assert requests_mock.request_history[0].url == f"{api_base}/deployments/1/"

    assert r == {"id": 1}

def test_antenna_client_events(requests_mock):
    a = antenna.AntennaAPI()

    requests_mock.get(f"{api_base}/events/?deployment=1", json={"count": 2, "results": [{"id": 1}]})

    r = a.events(1)

    assert requests_mock.called
    assert requests_mock.request_history[0].url == f"{api_base}/events/?deployment=1"
    assert requests_mock.request_history[0].headers["Authorization"] == "Token abcd"

    assert r == [{"id": 1}]

def test_antenna_client_get_event(requests_mock):
    a = antenna.AntennaAPI()

    requests_mock.get(f"{api_base}/events/1/", json={"id": 1})

    r = a.event(1)

    assert requests_mock.called
    assert requests_mock.request_history[0].url == f"{api_base}/events/1/"

    assert r == {"id": 1}

def test_stale_deployments(requests_mock, device, device_2, device_3):
    # has no sync date
    device.antenna_deployment = 1
    device.last_seen = datetime(2026, 5, 1)
    device.antenna_last_synced = None

    # has sync date later than seen
    device_2.antenna_deployment = 2
    device_2.last_seen = datetime(2026, 5, 1)
    device_2.antenna_last_synced = datetime(2026, 5, 2)

    # device 3 has no antenna deployment
    
    r = list(antenna.stale_deployments())

    assert len(r) == 1
    assert device in r

def test_sync_stale_deployments(requests_mock, device, device_2):
    device.antenna_deployment = 1
    device.last_seen = datetime(2026, 5, 5)
    device.antenna_last_synced = datetime(2026, 5, 1)

    requests_mock.post(f"{api_base}/deployments/1/sync/", json={})

    r = antenna.sync_stale_deployments()

    assert requests_mock.call_count == 1
    assert requests_mock.request_history[0].url == f"{api_base}/deployments/1/sync/"
    assert requests_mock.request_history[0].method == "POST"

    assert r[0].antenna_last_synced > r[0].last_seen
    

def test_device_edit_lists_deployments(admin_client, device, requests_mock):
    a_url = f"{api_base}/deployments/?project_id=1"
    requests_mock.get(a_url, json={
        "count": 1,
        "results": [
        {
            "id": 1,
            "name": "Default Station",
            "events": "http://localhost:8000/api/v2/events/?deployment=1",
            "project": {
                "id": 1,
                "name": "Test Project c1c3e748",
                "image": None,
                "details": "http://localhost:8000/api/v2/projects/1/",
                "user_permissions": []
            },
            "created_at": "2026-05-08T08:59:10.409483",
            "updated_at": "2026-05-15T11:09:33.500405",
            "device": {},
            "research_site": {},
            "jobs": [],
            "user_permissions": []
        }
        ],
        "user_permissions": []
    })
    res = admin_client.get(f'/devices/edit/{device.id}')
    assert res.status_code < 300
    assert requests_mock.called
    assert requests_mock.request_history[0].url == a_url
    assert "<option value=\"1\">Default Station" in res.text
