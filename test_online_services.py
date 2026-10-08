import json
import os
import threading
import time
import unittest
from unittest.mock import patch,MagicMock
from online_services import ServiceClient,ServiceConfig,MAX_RESPONSE_BYTES
from online_service.server import response_for

class OnlineFrameworkTests(unittest.TestCase):
    def test_disabled_by_default_no_transport(self):
        transport=MagicMock()
        client=ServiceClient(transport=transport)
        self.assertFalse(client.request());transport.assert_not_called()
        self.assertIsNone(client.poll())

    def test_background_request_is_bounded_and_completion_is_polled(self):
        entered=threading.Event();release=threading.Event()
        def transport(url,timeout):
            self.assertEqual(url,"https://atelier-api.reqlabs.co.uk/api/v1/health")
            self.assertEqual(timeout,3)
            entered.set();release.wait(1)
            return {"api_version":1,"status":"ok"}
        client=ServiceClient(ServiceConfig(enabled=True),transport)
        try:
            self.assertTrue(client.request());self.assertTrue(entered.wait(1))
            self.assertFalse(client.request());self.assertIsNone(client.poll())
            release.set()
            deadline=time.monotonic()+1
            result=None
            while result is None and time.monotonic()<deadline:
                result=client.poll();time.sleep(.001)
            self.assertTrue(result["ok"]);self.assertFalse(client.pending)
        finally:release.set();client.close()
        self.assertFalse(client.request())

    def test_errors_do_not_escape_or_retry(self):
        def fail(url,timeout):raise TimeoutError()
        client=ServiceClient(ServiceConfig(enabled=True),fail)
        self.assertTrue(client.request())
        deadline=time.monotonic()+1;result=None
        while result is None and time.monotonic()<deadline:
            result=client.poll();time.sleep(.001)
        self.assertFalse(result["ok"]);self.assertIn("offline",result["error"])
        self.assertFalse(client.request("upload_save"));client.close()

    def test_invalid_configuration_falls_back_to_offline(self):
        for endpoint in ("http://example.com","https://user:pass@example.com","https://example.com/path","https://example.com?token=secret"):
            with self.assertRaises(ValueError):ServiceClient(ServiceConfig(True,endpoint))
        with patch.dict(os.environ,{"ATELIER_ONLINE_ENABLED":"true","ATELIER_API_URL":"invalid"}):
            client=ServiceClient.from_environment()
            self.assertFalse(client.config.enabled)
        with self.assertRaises(ValueError):ServiceClient(ServiceConfig(timeout=0))

    def test_response_size_json_and_version_validation(self):
        for payload in (b"x"*(MAX_RESPONSE_BYTES+1),b"not json",b"[]",b'{"api_version":2}'):
            response=MagicMock();response.status=200;response.read.return_value=payload
            response.__enter__.return_value=response
            with patch("online_services.urlopen",return_value=response):
                with self.assertRaises(ValueError):ServiceClient._request("https://example.com/api/v1/health",3)
        response.read.return_value=b'{"api_version":1,"status":"ok"}'
        with patch("online_services.urlopen",return_value=response):
            self.assertEqual(ServiceClient._request("https://example.com/api/v1/health",3)["status"],"ok")

    def test_versioned_read_only_server_routes(self):
        self.assertEqual(response_for("/api/v1/health")[0],200)
        status,capabilities=response_for("/api/v1/capabilities")
        self.assertEqual(status,200);self.assertEqual(capabilities["features"],[])
        self.assertTrue(capabilities["local_saves_authoritative"])
        self.assertEqual(response_for("/save")[0],404)

if __name__=="__main__":unittest.main()
