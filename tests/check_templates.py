"""Parse rendered fixture templates with the actual proxy cores, without networking."""
import sys

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

import argparse
import json
from pathlib import Path
import re
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[1]


def execute(args):
    result = subprocess.run(args, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=20)
    if result.returncode:
        raise RuntimeError(f"{Path(args[0]).name} failed ({result.returncode}): "
                           + result.stdout + result.stderr)
    return result.stdout.strip()


def render(name, values):
    source = (ROOT / "assets" / name).read_text(encoding="utf-8")

    def value(match):
        return json.dumps(values[match.group(1)], ensure_ascii=True)

    rendered = re.sub(r'"\{\{([A-Z_]+)\}\}"', value, source)
    if re.search(r"\{\{[A-Z_]+\}\}", rendered):
        raise ValueError("Unfilled template input: " + name)
    return rendered


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mihomo", required=True)
    parser.add_argument("--sing-box", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    versions = {"mihomo": execute([args.mihomo, "-v"]).splitlines()[0],
                "sing_box": execute([args.sing_box, "version"]).splitlines()[0]}
    key_output = execute([args.sing_box, "generate", "reality-keypair"])
    keys = {}
    for label in ("PrivateKey", "PublicKey"):
        match = re.search(rf"(?mi)^{label}:\s*(\S+)", key_output)
        if not match:
            raise ValueError("Unsupported reality-keypair output format")
        keys[label] = match.group(1)
    values = {
        "VPS_ADDRESS": "203.0.113.10",
        "HANDSHAKE_HOST": "example.com",
        "CLIENT_UUID": str(uuid.uuid4()),
        "REALITY_PRIVATE_KEY": keys["PrivateKey"],
        "REALITY_PUBLIC_KEY": keys["PublicKey"],
        "SHORT_ID": "a1b2c3d4",
        "BOOTSTRAP_DNS": "192.0.2.53",
        "RESIDENTIAL_HOST": "198.51.100.10",
        "RESIDENTIAL_USER": "fixture-user",
        "RESIDENTIAL_PASSWORD": "fixture-password",
    }
    server = out / "server.fixture.json"
    server.write_text(render("server-reality.template.json", values), encoding="utf-8")
    execute([args.sing_box, "check", "-c", str(server)])
    checks = {"server_reality": "passed"}
    for kind in ("reality", "residential"):
        directory = out / kind
        directory.mkdir(exist_ok=True)
        target = directory / "client.fixture.yaml"
        target.write_text(render(f"client-{kind}.template.yaml", values), encoding="utf-8")
        execute([args.mihomo, "-t", "-d", str(directory), "-f", str(target)])
        checks["client_" + kind] = "passed"
    result = {"kind": "tanuki-template-validation", "versions": versions,
              "checks": checks, "mode": "configuration_parse_only",
              "live_network_or_service_changes": False}
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print("[fail] " + str(exc), file=sys.stderr)
        raise SystemExit(1)
