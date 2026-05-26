# -*- coding: utf-8 -*-
import requests, json
from pathlib import Path

GC_TOKEN = "35fbda9a0a6d73bd19442cd49d14314f6ec89c7b0f1993a18ea92c877ecc9060"
HEADERS  = {"Authorization": f"Token {GC_TOKEN}"}
TMP      = Path("datasets/_tmp_download/grand_challenge")
TMP.mkdir(parents=True, exist_ok=True)

def check(url, label=""):
    r = requests.get(url, headers=HEADERS, timeout=15)
    print(f"HTTP {r.status_code} [{label}]: {url}")
    if r.status_code == 200:
        try:
            d = r.json()
            cnt = d.get("count", len(d.get("results", [])))
            print(f"  -> count={cnt}")
            if d.get("results"):
                print(f"  -> first: {str(d['results'][0])[:300]}")
            return d
        except Exception:
            print(f"  -> text: {r.text[:200]}")
    return None

# Intentar acceder a imagenes de los challenges fetales
print("=== BUSCANDO DATOS DESCARGABLES ===\n")

# 1. PS-FH-AOP-2023 - Fetal Head ultrasound (ultrasonido pubico + cabeza fetal)
check("https://grand-challenge.org/api/v1/archives/limit=50", "All archives")
print()

# 2. Buscar reader studies con datos fetales
check("https://grand-challenge.org/api/v1/reader-studies/limit=20", "Reader studies")
print()

# 3. Ver imagenes del challenge ACOUSLIC directamente
r = requests.get("https://grand-challenge.org/api/v1/challenges/ACOUSLIC-AI/", headers=HEADERS, timeout=15)
if r.status_code == 200:
    data = r.json()
    print("ACOUSLIC-AI challenge data:")
    print(json.dumps(data, indent=2)[:1000])
