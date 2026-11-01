"""Download a pinned NAB subset; subsequent runs verify recorded SHA-256 hashes."""
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "COEN6314-course-project"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()

def main():
    manifest_path = ROOT / "config/data_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    else:
        sha = json.loads(fetch("https://api.github.com/repos/numenta/NAB/commits/master"))["sha"]
        listing = json.loads(fetch(f"https://api.github.com/repos/numenta/NAB/contents/data/realAWSCloudwatch?ref={sha}"))
        paths = sorted(x["path"] for x in listing if x["name"].endswith(".csv"))
        paths += ["labels/combined_windows.json", "LICENSE.txt", "data/README.md"]
        manifest = {"repository": "https://github.com/numenta/NAB", "commit": sha, "files": [{"path": p} for p in paths]}
    for item in manifest["files"]:
        destination = ROOT / "data/raw" / item["path"]
        content = destination.read_bytes() if destination.exists() and "sha256" in item else fetch(
            f"https://raw.githubusercontent.com/numenta/NAB/{manifest['commit']}/{item['path']}")
        digest = hashlib.sha256(content).hexdigest()
        if "sha256" in item and digest != item["sha256"]:
            raise ValueError(f"Checksum mismatch: {item['path']}")
        item["sha256"] = digest
        item["bytes"] = len(content)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Verified {len(manifest['files'])} files at {manifest['commit']}")

if __name__ == "__main__":
    main()
