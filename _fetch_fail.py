import json
import urllib.request
import zipfile
import io
import re

ua = {"User-Agent": "cursor", "Accept": "application/vnd.github+json"}
run_id = "30630922989"


def get(url):
    req = urllib.request.Request(url, headers=ua)
    with urllib.request.urlopen(req) as r:
        return json.load(r)


jobs = get(f"https://api.github.com/repos/lotario71/UT_SalesAnalytics/actions/runs/{run_id}/jobs")
for j in jobs["jobs"]:
    print("JOB", j["id"], j["conclusion"], "minutes", round((j.get("completed_at") and 1) or 0))
    for s in j.get("steps", []):
        print(" ", s["number"], s["name"], s.get("conclusion"))

# artifacts
arts = get(f"https://api.github.com/repos/lotario71/UT_SalesAnalytics/actions/runs/{run_id}/artifacts")
print("ARTIFACTS", [(a["name"], a["id"], a["size_in_bytes"], a["expired"]) for a in arts.get("artifacts", [])])

for a in arts.get("artifacts", []):
    print("try download", a["name"], a["archive_download_url"])
    try:
        req = urllib.request.Request(a["archive_download_url"], headers=ua)
        raw = urllib.request.urlopen(req).read()
        z = zipfile.ZipFile(io.BytesIO(raw))
        print("zip names", z.namelist())
        for name in z.namelist():
            if name.endswith(".log") or "buildozer" in name.lower():
                text = z.read(name).decode("utf-8", "replace")
                print("===", name, "len", len(text))
                # find error lines
                lines = text.splitlines()
                keys = re.compile(r"error|exception|failed|traceback|stderr|not found|No module", re.I)
                hits = [ln for ln in lines if keys.search(ln)]
                print("--- HITS (last 40) ---")
                print("\n".join(hits[-40:]))
                print("--- LAST 50 ---")
                print("\n".join(lines[-50:]))
    except Exception as e:
        print("DL ERR", type(e).__name__, e)
