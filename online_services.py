"""Optional online adapter. Local saves and gameplay never depend on this client."""
from dataclasses import dataclass
import json
import os
from queue import Queue, Empty
from threading import Thread
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

DEFAULT_ENDPOINT="https://atelier-api.reqlabs.co.uk"
MAX_RESPONSE_BYTES=65536
SUPPORTED_ROUTES={"health":"/api/v1/health","capabilities":"/api/v1/capabilities"}

@dataclass(frozen=True)
class ServiceConfig:
    enabled: bool=False
    endpoint: str=DEFAULT_ENDPOINT
    timeout: float=3.

    def validate(self):
        url=urlsplit(self.endpoint)
        if url.scheme!="https" or not url.hostname or url.username or url.password or url.query or url.fragment or url.path not in ("","/"):
            raise ValueError("Service endpoint must be an HTTPS origin")
        if not 0<self.timeout<=10:raise ValueError("Service timeout must be between zero and ten seconds")

class ServiceClient:
    """Single bounded daemon request; completion is polled on the Tk thread.

    No game state, account identifiers, save files, or telemetry are transmitted.
    There is no retry loop. Failure always leaves offline play available.
    """
    def __init__(self,config=None,transport=None):
        self.config=config or ServiceConfig()
        self.config.validate()
        self.transport=transport or self._request
        self.results=Queue(maxsize=1)
        self.pending=False
        self.closed=False
        self.last_result=None

    @classmethod
    def from_environment(cls):
        enabled=os.environ.get("ATELIER_ONLINE_ENABLED","").lower() in ("1","true","yes")
        try:return cls(ServiceConfig(enabled,os.environ.get("ATELIER_API_URL",DEFAULT_ENDPOINT)))
        except ValueError:
            client=cls()
            client.last_result={"ok":False,"error":"Invalid service configuration; offline mode remains active."}
            return client

    @staticmethod
    def _request(url,timeout):
        request=Request(url,headers={"Accept":"application/json","User-Agent":"StarstruckAtelier/1"})
        with urlopen(request,timeout=timeout) as response:
            body=response.read(MAX_RESPONSE_BYTES+1)
            if len(body)>MAX_RESPONSE_BYTES:raise ValueError("Service response is too large")
            if response.status!=200:raise ValueError("Service is unavailable")
        payload=json.loads(body)
        if not isinstance(payload,dict) or payload.get("api_version")!=1:raise ValueError("Unsupported service response")
        return payload

    def request(self,operation="health"):
        if self.closed or not self.config.enabled or self.pending or operation not in SUPPORTED_ROUTES:return False
        self.pending=True
        def work():
            try:
                payload=self.transport(self.config.endpoint.rstrip("/")+SUPPORTED_ROUTES[operation],self.config.timeout)
                result={"ok":True,"operation":operation,"data":payload}
            except Exception:
                result={"ok":False,"operation":operation,"error":"Service unavailable; offline play is unaffected."}
            self.results.put_nowait(result)
        Thread(target=work,name="atelier-service",daemon=True).start()
        return True

    def poll(self):
        if self.closed:return None
        try:result=self.results.get_nowait()
        except Empty:return None
        self.pending=False;self.last_result=result
        return result

    def close(self):
        self.closed=True
