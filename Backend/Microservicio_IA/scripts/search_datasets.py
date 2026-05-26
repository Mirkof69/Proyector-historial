# -*- coding: utf-8 -*-
"""Busca datasets fetales en Zenodo, Mendeley y GitHub."""
import requests, json, time

def search_zenodo(query, size=8):
    url = "https://zenodo.org/api/records"
    params = {"q": query, "type": "dataset", "sort": "mostrecent", "size": size}
    try:
        r = requests.get(url, params=params, timeout=20)
        if r.status_code == 200:
            return r.json().get("hits", {}).get("hits", [])
    except Exception as e:
        print(f"  Error Zenodo: {e}")
    return []

queries = [
    "fetal ultrasound anomaly",
    "fetal ultrasound spina bifida",
    "fetal ultrasound cleft lip",
    "fetal ultrasound placenta",
    "fetal ultrasound twin pregnancy",
    "obstetric ultrasound pathology",
    "prenatal diagnosis ultrasound",
    "fetal ultrasound oligohydramnios",
    "fetal ultrasound atresia",
]

found = {}
for q in queries:
    hits = search_zenodo(q, 6)
    for h in hits:
        zid = str(h.get("id", ""))
        if not zid or zid in found:
            continue
        meta = h.get("metadata", {})
        title = meta.get("title", "")
        access = meta.get("access_right", "")
        files = [f.get("key", "") for f in h.get("files", [])[:4]]
        desc = meta.get("description", "")[:120]
        found[zid] = {
            "title": title,
            "access": access,
            "files": files,
            "url": f"https://zenodo.org/records/{zid}",
            "query": q,
            "desc": desc,
        }
    time.sleep(0.5)

print(f"Datasets encontrados en Zenodo: {len(found)}")
print("=" * 70)
open_access = []
for zid, d in found.items():
    is_open = d["access"] == "open"
    has_img = any(
        f.lower().endswith((".zip", ".tar", ".gz", ".rar"))
        for f in d["files"]
    )
    marker = "[OPEN]" if is_open else "[CLOSED]"
    print(f"{marker} {d['title'][:60]}")
    print(f"  URL: {d['url']}")
    print(f"  Archivos: {d['files']}")
    print()
    if is_open and has_img:
        open_access.append(d)

print(f"\nDatasets abiertos con archivos descargables: {len(open_access)}")
for d in open_access:
    print(f"  => {d['url']}")
    print(f"     {d['title']}")
