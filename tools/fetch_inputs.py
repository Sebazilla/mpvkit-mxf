#!/usr/bin/env python3
"""Download only the recorded LGPL/permissive inputs from pinned GitHub assets."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request


class GitHubOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        validate(newurl)
        return super().redirect_request(request, fp, code, msg, headers, newurl)


def validate(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "github.com", "release-assets.githubusercontent.com", "objects.githubusercontent.com"
    }:
        raise SystemExit("STOP: asset URL leaves GitHub: " + str(parsed.hostname))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name("original-assets.json").read_text())
    opener = urllib.request.build_opener(GitHubOnly())
    args.destination.mkdir(parents=True, exist_ok=True)
    for name, item in manifest.items():
        validate(item["url"])
        archive = args.destination / (name + ".zip")
        if not archive.exists():
            with opener.open(item["url"], timeout=120) as response, archive.open("wb") as stream:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    stream.write(chunk)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != item["sha256"]:
            raise SystemExit("archive SHA256 mismatch: " + name)
        target = args.destination / name
        if not target.exists():
            subprocess.run(["/usr/bin/ditto", "-x", "-k", str(archive), str(target)], check=True)
        print("verified original GitHub asset", name, flush=True)


if __name__ == "__main__":
    main()
