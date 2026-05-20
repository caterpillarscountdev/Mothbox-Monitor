import os
import pytest
from mothmonitor.models import db, Device, User, Night
from mothmonitor import antenna

api_base = "http://test/api/v2"


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("ANTENNA_URL", "http://test/")
    monkeypatch.setenv("ANTENNA_PROJECT_ID", "1")
    monkeypatch.setenv("ANTENNA_API_TOKEN", "abcd")


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
    print(res.text)
    assert "<option value=\"1\">Default Station" in res.text
