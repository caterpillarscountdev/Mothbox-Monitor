import os
import requests

class APIError(Exception):
    pass

class AntennaAPI(object):

    antenna_url = os.environ.get("ANTENNA_URL", "https://antenna.insectai.org/")
    api_path = os.environ.get("ANTENNA_API_PATH", "api/v2")
    project_id = os.environ.get("ANTENNA_PROJECT_ID", "")
    auth_token = os.environ.get("ANTENNA_API_TOKEN", "")

    def build_url(self, path, api=True):
        api_path = self.api_path
        if not api:
            api_path = ""
        return f"{self.antenna_url}{api_path}{path}"

    def _request(self, path, params=None, body=None, method="get"):
        method = method.lower()
        check = getattr(requests, method)(self.build_url(path),
                                          params=params,
                                          json=body,
                                          headers={"Authorization": f"Token {self.auth_token}"},
                                          )
        if check.status_code < 400:
            return check.json()
        raise APIError(f"Antenna API Error: {cehck.status_code} {check.text}")
    
    def deployments(self):
        return self._request("/deployments/", params={"project_id": self.project_id})["results"]
    
    def deployment(self, pk):
        return self._request(f"/deployments/{pk}/")

    def sync_deployment(self, pk):
        return self._request(f"/deployments/{pk}/sync", method="post")

    def events(self, deployment):
        return self._request("/events/", params={"deployment": deployment})["results"]
    
    def event(self, pk):
        return self._request(f"/events/{pk}/")

    def event_url(self, pk):
        return self.build_url(f"/projects/{self.project_id}/session/{pk}", api=False)
