#!/usr/bin/env python3
"""
Holt die aktuellen Meldungen aus dem Ludwigshafener Maengelmelder und schreibt
sie als data.json neben die index.html.

Warum ueberhaupt ein Skript? Die API liefert JSON, aber keine CORS-Header --
ein Browser darf sie von github.io aus nicht direkt lesen. Also holt der
GitHub-Actions-Runner die Daten serverseitig und legt sie als statische Datei ab.

Zwei Endpunkte, die zusammengehoeren:
  /message/geojson  -> Koordinaten, aber max. 500 pro Seite
  /message          -> Text, Status, Kategorie, Datum
Gejoint wird ueber die Meldungs-ID.
"""

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://ludwigshafen.maengelmelder.de/api/v1/domain/156"
OUT = Path(__file__).resolve().parent.parent / "data.json"

GEO_PAGES = 6      # 6 x 500 = bis zu 3000 Punkte
MSG_PAGES = 8      # 8 x 200 = bis zu 1600 Meldungen mit Volltext
STATE = {"checked": 0, "solved": 1, "unsolvable": 2}


def get(path, tries=3):
    req = urllib.request.Request(
        BASE + path,
        headers={
            "User-Agent": "melde-lu/1.0 (statischer Mirror, github pages)",
            "Accept": "application/json",
        },
    )
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as exc:
            if attempt == tries - 1:
                raise
            print(f"  retry {path}: {exc}")
            time.sleep(3 * (attempt + 1))


def coordinates():
    """id -> [lng, lat]"""
    out = {}
    for page in range(1, GEO_PAGES + 1):
        data = get(f"/message/geojson?rows=500&page={page}&visible_map=1")
        feats = data.get("features") or []
        if not feats:
            break
        for f in feats:
            out[f["id"]] = f["geometry"]["coordinates"]
        print(f"  geojson Seite {page}: {len(feats)}")
        time.sleep(1)
    return out


def messages():
    out = {}
    for page in range(1, MSG_PAGES + 1):
        data = get(f"/message?rows=200&page={page}&sort=-created")
        rows = data.get("data") or []
        if not rows:
            break
        for m in rows:
            out[m["id"]] = m
        print(f"  messages Seite {page}: {len(rows)}")
        if len(rows) < 200:
            break
        time.sleep(1)
    return out


def main():
    print("Koordinaten holen ...")
    coords = coordinates()
    print("Meldungen holen ...")
    msgs = messages()

    items = []
    for m in msgs.values():
        c = coords.get(m["id"])
        if not c:
            continue          # ohne Koordinate hat die Meldung auf der Karte nichts verloren
        items.append({
            "id": m["id"],
            "st": STATE.get(m.get("state"), 0),
            "cat": (m.get("message_type") or {}).get("name", ""),
            "lat": round(c[1], 5),
            "lng": round(c[0], 5),
            "date": (m.get("created") or "")[:10],
            "text": " ".join((m.get("text") or "").split())[:2000],
            "resp": m.get("responsible_name") or "",
        })

    items.sort(key=lambda x: x["date"], reverse=True)
    if not items:
        raise SystemExit("Keine Meldungen bekommen -- data.json bleibt unveraendert.")

    payload = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": BASE,
        "items": items,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    offen = sum(1 for i in items if i["st"] == 0)
    print(f"{len(items)} Meldungen geschrieben, davon {offen} offen -> {OUT}")


if __name__ == "__main__":
    main()
