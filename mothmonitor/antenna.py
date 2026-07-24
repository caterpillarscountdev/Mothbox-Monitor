import os
import requests
from datetime import datetime
from .models import db, Device

class APIError(Exception):
    pass

class AntennaAPI(object):

    def __init__(self):
        self.antenna_url = os.environ.get("ANTENNA_URL", "https://antenna.insectai.org/")
        self.api_path = os.environ.get("ANTENNA_API_PATH", "api/v2")
        self.project_id = os.environ.get("ANTENNA_PROJECT_ID", "")
        self.auth_token = os.environ.get("ANTENNA_API_TOKEN", "")

    def build_url(self, path, api=True):
        antenna = self.antenna_url
        api_path = self.api_path
        if not api:
            antenna = antenna.replace("api.", "")
            api_path = ""
            if path[0] == '/':
                path = path[1:]
        return f"{antenna}{api_path}{path}"

    def _request(self, path, params=None, body=None, method="get"):
        method = method.lower()
        try:
            check = getattr(requests, method)(self.build_url(path),
                                              params=params,
                                              json=body,
                                              headers={"Authorization": f"Token {self.auth_token}"}
                                              )
        except requests.exceptions.RequestException as e:
            raise APIError(f"Antenna Request Error: {e}") from e
        if check.ok:
            return check.json()
        raise APIError(f"Antenna API Error: {check.status_code} {check.text}")
    
    def deployments(self):
        return self._request("/deployments/", params={"project_id": self.project_id})["results"]
    
    def deployment(self, pk):
        return self._request(f"/deployments/{pk}/")

    def sync_deployment(self, pk):
        return self._request(f"/deployments/{pk}/sync/", method="post")

    def events(self, deployment):
        return self._request("/events/", params={"deployment": deployment})["results"]
    
    def event(self, pk):
        return self._request(f"/events/{pk}/")

    def event_url(self, pk):
        return self.build_url(f"/projects/{self.project_id}/session/{pk}", api=False)

    def station_url(self, pk):
        return self.build_url(f"/projects/{self.project_id}/deployments/{pk}", api=False)


def stale_deployments():
    select = db.select(Device).where(
        ((Device.antenna_deployment != None) & (Device.antenna_deployment != '')) &
        ((Device.last_seen>Device.antenna_last_synced ) | (Device.antenna_last_synced == None))
    )
    return db.session.execute(select).scalars()

def sync_stale_deployments():
    api = AntennaAPI()
    ds = list(stale_deployments())
    for d in ds:
        api.sync_deployment(d.antenna_deployment)
        d.antenna_last_synced = datetime.now()
    db.session.commit()
    return ds

def station_url(pk):
    api = AntennaAPI()
    return api.station_url(pk)
