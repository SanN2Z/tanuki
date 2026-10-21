#!/usr/bin/env python3
"""Read-only local evidence for Japan-region environment consistency."""
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

import argparse
import datetime as dt
import json
import locale
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import urllib.parse
import urllib.request

ERRORS = []
ENV_NAMES = {"http_proxy", "https_proxy", "all_proxy", "no_proxy", "tz", "lang",
             "language", "node_extra_ca_certs", "ssl_cert_file", "requests_ca_bundle"}
SECRET_NAME = re.compile(r"token|secret|password|api.?key|auth|cookie|headers", re.I)


def path_label(path):
    return str(path).replace(str(Path.home()), "~").replace("\\", "/")


def endpoint(value):
    value = str(value)
    parsed = urllib.parse.urlsplit(value if "://" in value else "//" + value)
    return {"scheme": parsed.scheme, "host": parsed.hostname, "port": parsed.port,
            "credentials_present": bool(parsed.username or parsed.password),
            "query_present": bool(parsed.query)}


def env_summary(values):
    result = {}
    for key, value in values.items():
        low = key.lower()
        if not (low in ENV_NAMES or low.startswith(("anthropic", "claude", "lc_"))):
            continue
        if SECRET_NAME.search(key):
            result[key] = "[set]" if value else "[empty]"
        elif ("proxy" in low and low != "no_proxy") or low.endswith(("_url", "_endpoint")):
            try:
                result[key] = endpoint(value) if value else "[empty]"
            except ValueError:
                result[key] = "[invalid endpoint]"
        else:
            result[key] = value
    return result


def fail(label, exc):
    item = {"source": label, "error": type(exc).__name__}
    code = getattr(exc, "code", None) or getattr(exc, "errno", None)
    if code is not None:
        item["code"] = code
    ERRORS.append(item)
    print("[fail] " + label + ": " + item["error"] +
          (" (" + str(code) + ")" if code is not None else ""), file=sys.stderr)


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        fail(path_label(path), exc)
        return None


def command(label, args):
    try:
        proc = subprocess.run(args, capture_output=True, encoding="utf-8",
                              errors="replace", timeout=12, check=True)
        return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError) as exc:
        fail(label, exc)
        return None


def registry_fields(hive, key_path, names):
    import winreg
    try:
        key = winreg.OpenKey(hive, key_path)
    except FileNotFoundError:
        return {}
    except OSError as exc:
        fail("registry:" + key_path, exc)
        return {}
    result = {}
    with key:
        for name in names:
            try:
                value, _ = winreg.QueryValueEx(key, name)
                result[name] = value
            except FileNotFoundError:
                result[name] = None
            except OSError as exc:
                fail("registry:" + key_path + ":" + name, exc)
    return result


def windows_system():
    import winreg as reg
    local = registry_fields(reg.HKEY_CURRENT_USER, r"Control Panel\International",
                            ["LocaleName", "sCountry", "sShortDate", "sShortTime"])
    zone = registry_fields(reg.HKEY_LOCAL_MACHINE,
                           r"SYSTEM\CurrentControlSet\Control\TimeZoneInformation",
                           ["TimeZoneKeyName"])
    languages = registry_fields(reg.HKEY_CURRENT_USER,
                                r"Control Panel\International\User Profile", ["Languages"])
    home = registry_fields(reg.HKEY_CURRENT_USER, r"Control Panel\International\Geo",
                           ["Nation", "Name"])
    result = {"timezone_id": zone.get("TimeZoneKeyName"), "regional": local,
              "languages": languages.get("Languages"), "home_region": home}
    proxy = registry_fields(reg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
                            ["ProxyEnable", "ProxyServer", "AutoConfigURL", "AutoDetect"])
    if proxy.get("AutoConfigURL"):
        proxy["AutoConfigURL"] = endpoint(proxy["AutoConfigURL"])
    if proxy.get("ProxyServer"):
        # Windows supports semicolon-separated, per-protocol proxy assignments.
        entries = proxy["ProxyServer"].split(";")
        proxy["ProxyServer"] = [
            {"protocol": s.split("=", 1)[0] if "=" in s else "all",
             "endpoint": endpoint(s.split("=", 1)[-1])}
            for s in entries if s.strip()
        ]
    result["internet_settings"] = proxy
    persistent = {}
    for hive, key_path, label in [
        (reg.HKEY_CURRENT_USER, "Environment", "user"),
        (reg.HKEY_LOCAL_MACHINE,
         r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "machine"),
    ]:
        try:
            with reg.OpenKey(hive, key_path) as key:
                values = dict(reg.EnumValue(key, i)[:2]
                              for i in range(reg.QueryInfoKey(key)[1]))
            persistent[label] = env_summary(values)
        except OSError as exc:
            fail("persistent_environment:" + label, exc)
    result["persistent_environment"] = persistent
    return result


def system_evidence():
    current = dt.datetime.now().astimezone()
    result = {"os": platform.system(), "release": platform.release(),
              "runtime_locale": locale.getlocale(),
              "offset_minutes": int(current.utcoffset().total_seconds() / 60),
              "timezone_name": current.tzname(), "timezone_id": os.environ.get("TZ"),
              "runtime_context": {
                  "wsl": bool(os.environ.get("WSL_DISTRO_NAME")),
                  "ssh": bool(os.environ.get("SSH_CONNECTION")),
                  "container_marker": Path("/.dockerenv").exists(),
              }}
    if os.name == "nt":
        result.update(windows_system())
    else:
        tzfile = Path("/etc/localtime")
        try:
            resolved = str(tzfile.resolve(strict=True))
            if "/zoneinfo/" in resolved:
                result["timezone_id"] = resolved.split("/zoneinfo/", 1)[1]
        except OSError as exc:
            fail("/etc/localtime", exc)
        if platform.system() == "Darwin":
            result["apple_locale"] = command("AppleLocale", ["defaults", "read", "-g", "AppleLocale"])
            result["apple_languages"] = command("AppleLanguages", ["defaults", "read", "-g", "AppleLanguages"])
        elif Path("/etc/timezone").is_file():
            try:
                result["timezone_file"] = Path("/etc/timezone").read_text().strip()
                if not result["timezone_id"]:
                    result["timezone_id"] = result["timezone_file"]
            except OSError as exc:
                fail("/etc/timezone", exc)
    return result


def browser_roots():
    home = Path.home()
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", home / "AppData/Local"))
        roaming = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
        roots = [local / "Google/Chrome/User Data", local / "Microsoft/Edge/User Data",
                 local / "BraveSoftware/Brave-Browser/User Data", local / "Chromium/User Data"]
        firefox = roaming / "Mozilla/Firefox/Profiles"
    elif platform.system() == "Darwin":
        base = home / "Library/Application Support"
        roots = [base / "Google/Chrome", base / "Microsoft Edge",
                 base / "BraveSoftware/Brave-Browser", base / "Chromium"]
        firefox = base / "Firefox/Profiles"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
        roots = [base / "google-chrome", base / "microsoft-edge",
                 base / "BraveSoftware/Brave-Browser", base / "chromium"]
        firefox = home / ".mozilla/firefox"
    return roots, firefox


def browser_evidence():
    roots, firefox = browser_roots()
    output = []
    for root in roots:
        if not root.is_dir():
            continue
        candidates = [root / "Default/Preferences", *root.glob("Profile */Preferences")]
        for path in candidates:
            if not path.is_file():
                continue
            data = read_json(path)
            if not isinstance(data, dict):
                continue
            intl = data.get("intl", {})
            proxy = data.get("proxy", {})
            proxy_summary = {k: proxy[k] for k in ("mode",) if k in proxy}
            for key in ("server", "pac_url"):
                if proxy.get(key):
                    try:
                        proxy_summary[key] = endpoint(proxy[key])
                    except ValueError as exc:
                        fail(path_label(path) + ":proxy", exc)
            output.append({
                "source": path_label(path),
                "language_preferences": {k: intl[k] for k in
                                         ("accept_languages", "selected_languages") if k in intl},
                "webrtc": {k: v for k, v in data.get("webrtc", {}).items()
                           if k in ("ip_handling_policy", "multiple_routes_enabled",
                                    "nonproxied_udp_enabled")},
                "proxy_preferences": proxy_summary,
                "doh_mode": data.get("dns_over_https", {}).get("mode"),
                "geolocation_default": data.get("profile", {}).get(
                    "default_content_setting_values", {}).get("geolocation"),
                "evidence_type": "stored_preferences_not_runtime",
            })
    allowed = {"intl.accept_languages", "intl.locale.requested", "privacy.resistFingerprinting",
               "network.proxy.type", "network.proxy.http", "network.proxy.http_port",
               "network.proxy.ssl", "network.proxy.ssl_port", "network.proxy.socks",
               "network.proxy.socks_port", "network.proxy.socks_remote_dns",
               "network.proxy.no_proxies_on", "network.proxy.autoconfig_url",
               "network.trr.mode", "network.trr.uri", "media.peerconnection.ice.proxy_only",
               "media.peerconnection.ice.no_host", "media.peerconnection.enabled"}
    if firefox.is_dir():
        for path in firefox.glob("*/prefs.js"):
            try:
                text = path.read_text(encoding="utf-8")
                values = {}
                for key, raw in re.findall(r'user_pref\("([^"]+)",\s*(.*?)\);', text):
                    if key in allowed:
                        value = json.loads(raw)
                        if key.endswith(("_url", ".uri")) and value:
                            value = endpoint(value)
                        values[key] = value
                output.append({"source": path_label(path), "preferences": values,
                               "evidence_type": "stored_preferences_not_runtime"})
            except (OSError, ValueError) as exc:
                fail(path_label(path), exc)
    return output


def claude_evidence(project):
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")).expanduser()
    paths = [config / "settings.json", config / "settings.local.json",
             project / ".claude/settings.json", project / ".claude/settings.local.json"]
    output = []
    for path in dict.fromkeys(paths):
        if not path.is_file():
            continue
        data = read_json(path)
        if isinstance(data, dict):
            output.append({"source": path_label(path), "env": env_summary(data.get("env", {})),
                           "settings": {k: data[k] for k in
                                        ("model", "language", "autoUpdatesChannel", "forceLoginMethod")
                                        if k in data}})
    executable = shutil.which("claude")
    return {"executable": path_label(executable) if executable else None,
            "version": command("claude --version", [executable, "--version"]) if executable else None,
            "settings": output, "credential_files_read": False}


def proxy_config_candidates():
    home = Path.home()
    roaming = Path(os.environ.get("APPDATA", home / "AppData/Roaming"))
    paths = [home / ".config/mihomo/config.yaml", home / ".config/clash/config.yaml",
             roaming / "io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml",
             roaming / "io.github.clash-verge-rev.clash-verge-rev/verge.yaml"]
    return [path_label(path) for path in paths if path.is_file()]


def probe_network(proxy):
    explicit = {"http": proxy, "https": proxy} if proxy else None
    handler = urllib.request.ProxyHandler(explicit)
    opener = urllib.request.build_opener(handler)
    result = {"path": "explicit_proxy_requested" if proxy else "effective_collector_environment",
              "effective_proxy_configuration": env_summary(
                  {k + "_proxy": v for k, v in handler.proxies.items() if k in ("http", "https", "all", "no")}),
              "providers": []}
    for url in ("https://ipapi.co/json/", "https://ipinfo.io/json"):
        provider = {"source": url, "queried_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "no_proxy_bypass": urllib.request.proxy_bypass(urllib.parse.urlsplit(url).hostname)}
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "tanuki-environment-audit/1"})
            with opener.open(req, timeout=6) as response:
                data = json.load(response)
            country = data.get("country_code") or data.get("country")
            if data.get("error") or not country or not data.get("ip"):
                raise ValueError("Provider did not return IP and country")
            provider.update({"status": "measured", "ip": data["ip"], "country": country,
                             "timezone": data.get("timezone"), "asn": data.get("asn"),
                             "organization": data.get("org")})
        except (OSError, ValueError) as exc:
            fail(url, exc)
            provider.update({"status": "unverified", "error": type(exc).__name__})
        result["providers"].append(provider)
    return result


def observations(report):
    result = []
    system = report["system"]
    zone = system.get("timezone_id")
    offset = system["offset_minutes"]
    known_japan = zone in ("Asia/Tokyo", "Tokyo Standard Time", "Japan")
    result.append({"surface": "system_timezone",
                   "status": "aligned" if known_japan and offset == 540 else
                             "unverified" if not zone and offset == 540 else "different",
                   "actual": {"timezone_id": zone, "offset_minutes": offset}})
    runtime_tz = os.environ.get("TZ")
    if runtime_tz and runtime_tz != zone:
        result.append({"surface": "process_TZ", "status": "different",
                       "actual": runtime_tz, "note": "Process override differs from OS timezone evidence."})
    for source in report.get("network", {}).get("providers", []):
        result.append({"surface": source["source"], "status":
                       ("aligned" if source["country"] == "JP" else "different")
                       if source["status"] == "measured" else "unverified",
                       "country": source.get("country")})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write UTF-8 JSON evidence to this file.")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--network", action="store_true", help="Query two public IP information providers once.")
    parser.add_argument("--proxy", help="HTTP(S) proxy for the network comparison only.")
    parser.add_argument("--browser-report", type=Path, help="Attach JSON returned by the bundled browser probe.")
    args = parser.parse_args()
    if args.proxy and (not args.network or urllib.parse.urlsplit(args.proxy).scheme not in ("http", "https")):
        parser.error("--proxy requires --network and an http:// or https:// URL")
    report = {"kind": "tanuki-local-report",
              "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
              "target": {"country": "JP", "timezone": "Asia/Tokyo", "offset_minutes": 540},
              "system": system_evidence(), "process_environment": env_summary(os.environ),
              "browsers": browser_evidence(), "claude": claude_evidence(args.project_dir),
              "proxy_config_files": proxy_config_candidates()}
    local_error_count = len(ERRORS)
    if args.network:
        report["network"] = probe_network(args.proxy)
    if args.browser_report:
        browser = read_json(args.browser_report)
        if not isinstance(browser, dict) or browser.get("kind") != "tanuki-browser-report":
            parser.error("--browser-report is not a tanuki browser report")
        report["browser_runtime"] = browser
    report["observations"] = observations(report)
    report["errors"] = list(ERRORS)
    report["coverage"] = {
        "local_configuration": "collected_with_errors" if local_error_count else "collected",
        "network": "attempted" if args.network else "not_measured",
        "browser_runtime": "attached" if args.browser_report else "not_measured",
        "ipv4_ipv6_separate_paths": "not_measured",
        "dns_recursive_path": "not_measured",
        "target_application_routes": "not_measured",
        "server_side_account_history": "not_accessible",
    }
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
        print(str(args.output.resolve()))
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
