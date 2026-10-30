"""Behavior checks for evidence, redaction and offline operation."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.dont_write_bytecode = True
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location(
    "tanuki_collector", Path(__file__).resolve().parents[1] / "scripts/collect_environment.py")
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class JsonReply:
    def __init__(self, data):
        self.data = io.StringIO(json.dumps(data))

    def __enter__(self):
        return self.data

    def __exit__(self, *args):
        return False


class CollectorTests(unittest.TestCase):
    def setUp(self):
        collector.ERRORS.clear()

    def test_credentials_and_url_secrets_are_not_printed(self):
        secret = "PRIVATE_VALUE_FOR_TEST"
        result = collector.env_summary({
            "ANTHROPIC_API_KEY": secret,
            "ANTHROPIC_AUTH_TOKEN": secret,
            "ANTHROPIC_CUSTOM_HEADERS": "Authorization: " + secret,
            "HTTPS_PROXY": "http://user:" + secret + "@127.0.0.1:7890/?key=" + secret,
            "ANTHROPIC_BASE_URL": "https://example.invalid/" + secret + "?token=" + secret,
        })
        self.assertNotIn(secret, json.dumps(result))
        self.assertTrue(result["HTTPS_PROXY"]["credentials_present"])
        self.assertEqual(result["ANTHROPIC_API_KEY"], "[set]")

    def test_provider_failure_is_not_a_pass(self):
        provider = mock.Mock()
        provider.open.side_effect = [
            JsonReply({"ip": "203.0.113.10", "country_code": "JP", "timezone": "Asia/Tokyo"}),
            TimeoutError("fixture timeout"),
        ]
        with mock.patch.object(collector.urllib.request, "build_opener", return_value=provider), \
                contextlib.redirect_stderr(io.StringIO()):
            result = collector.probe_network(None)
        self.assertEqual(result["providers"][0]["country"], "JP")
        self.assertEqual(result["providers"][1]["status"], "unverified")
        self.assertEqual(len(collector.ERRORS), 1)

    def test_offset_alone_does_not_establish_tokyo(self):
        with mock.patch.object(collector.os, "environ", {}):
            for zone, offset, expected in [
                ("Asia/Tokyo", 540, "aligned"),
                ("Asia/Seoul", 540, "different"),
                (None, 540, "unverified"),
                ("Asia/Shanghai", 480, "different"),
            ]:
                with self.subTest(zone=zone):
                    report = {"target": {"country": "JP", "timezone": "Asia/Tokyo", "offset_minutes": 540},
                              "system": {"timezone_id": zone, "offset_minutes": offset}}
                    self.assertEqual(collector.observations(report)[0]["status"], expected)

    def test_assigned_us_exit_does_not_require_japan_or_tokyo(self):
        def measured(*args):
            return {"providers": [{"source": "fixture", "status": "measured", "country": "US"}]}
        report, probe = self.invoke_main(["--network", "--target-country", "US"], measured)
        probe.assert_called_once()
        self.assertEqual(report["target"]["country"], "US")
        self.assertIsNone(report["target"]["timezone"])
        self.assertEqual(report["observations"][0]["status"], "not_requested")
        self.assertEqual(report["observations"][-1]["status"], "aligned")

    def test_explicit_timezone_is_compared_with_the_os(self):
        report = {"target": {"country": "US", "timezone": "Pacific Standard Time", "offset_minutes": None},
                  "system": {"timezone_id": "Pacific Standard Time", "offset_minutes": -420}}
        with mock.patch.object(collector.os, "environ", {}):
            self.assertEqual(collector.observations(report)[0]["status"], "aligned")
            report["system"]["timezone_id"] = "Tokyo Standard Time"
            self.assertEqual(collector.observations(report)[0]["status"], "different")

    def invoke_main(self, argv, network):
        out = io.StringIO()
        with mock.patch.object(sys, "argv", ["collect_environment.py", *argv]), \
                mock.patch.object(collector, "system_evidence",
                                  return_value={"timezone_id": "Asia/Tokyo", "offset_minutes": 540}), \
                mock.patch.object(collector, "browser_evidence", return_value=[]), \
                mock.patch.object(collector, "claude_evidence", return_value={}), \
                mock.patch.object(collector, "proxy_config_candidates", return_value=[]), \
                mock.patch.object(collector, "probe_network", side_effect=network) as probe, \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(collector.main(), 0)
        return json.loads(out.getvalue()), probe

    def test_default_collection_does_not_query_network(self):
        def forbidden(*args):
            raise AssertionError("Unexpected external query")
        report, probe = self.invoke_main([], forbidden)
        probe.assert_not_called()
        self.assertEqual(report["coverage"]["network"], "not_measured")

    def test_network_errors_do_not_mark_local_collection_as_failed(self):
        def unavailable(*args):
            collector.fail("fixture_provider", TimeoutError())
            return {"providers": [{"source": "fixture", "status": "unverified"}]}
        report, probe = self.invoke_main(["--network"], unavailable)
        probe.assert_called_once()
        self.assertEqual(report["coverage"]["local_configuration"], "collected")
        self.assertEqual(report["observations"][-1]["status"], "unverified")
        self.assertEqual(len(report["errors"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
