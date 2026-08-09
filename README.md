# Melde LU

Alternatives Frontend für den [Mängelmelder Ludwigshafen](https://ludwigshafen.maengelmelder.de).
Statische Seite, läuft auf GitHub Pages, aktualisiert sich stündlich von selbst.

**Was es besser macht**

- Karte zeigt standardmäßig nur offene Vorgänge. Erledigtes ist einen Tipp entfernt, nicht im Weg.
- Melden auf einem Screen statt im mehrstufigen Assistenten: Kategorie, Standort (kommt vom GPS), Text, fertig.
- Dublettenwarnung: offene Meldungen im 80-Meter-Umkreis erscheinen, bevor du absendest.
- Liste sortiert nach Entfernung, mit Liegezeit pro Vorgang.

---

## Deployen (ca. 5 Minuten)

1. **Repository anlegen** – öffentlich, Name egal, z. B. `melde-lu`.

2. **Dateien reinlegen** – dieser Ordner, Struktur so lassen:

   ```
   index.html
   data.json
   .nojekyll
   scripts/fetch_data.py
   .github/workflows/deploy.yml
   ```

3. **Pages auf Actions umstellen** – Repo → *Settings* → *Pages* → *Build and deployment* →
   *Source*: **GitHub Actions**. Nicht „Deploy from a branch“, sonst läuft der Job ins Leere.

4. **Pushen.** Der Workflow startet beim Push, holt frische Daten und veröffentlicht.
   Unter *Actions* siehst du den Lauf; die Adresse steht danach in *Settings* → *Pages*
   und lautet `https://<dein-name>.github.io/<repo>/`.

Das war's. Kein Server, kein Proxy, keine Kosten.

## Wie die Daten reinkommen

Der Mängelmelder liefert JSON unter `/api/v1/domain/156/…`, aber ohne CORS-Header –
ein Browser auf github.io darf die API nicht direkt lesen. Also holt der
GitHub-Actions-Runner sie serverseitig (`scripts/fetch_data.py`) und legt `data.json`
neben die `index.html`. Gleicher Origin, kein CORS-Problem.

Der Job läuft stündlich (`cron: "17 * * * *"`) und lässt sich unter *Actions* →
*Run workflow* jederzeit von Hand auslösen. Scheitert der Abruf, bleibt die alte
`data.json` liegen; fehlt sie ganz, zeigt die App den eingebauten Snapshot vom 09.08.2026.

Zwei Dinge, die dich sonst irgendwann überraschen:

- GitHub pausiert `schedule`-Workflows in Repos, in denen 60 Tage nichts passiert ist.
  Eine Mail kommt vorher; ein Klick auf *Enable workflow* reicht.
- Die API gehört einer kommunalen Anlage. Stündlich ist höflich, im Minutentakt nicht.
  Wenn du das Intervall änderst, bleib im Rahmen.

## Was noch fehlt

**Absenden** läuft weiter über das offizielle Formular. Die App sammelt alle Angaben,
kopiert sie in die Zwischenablage und öffnet `/bms/create` – einmal einfügen, abschicken.

Direktes Absenden wäre technisch möglich: der offizielle Assistent postet an
`POST /api/v1/domain/156/message`. Der Endpunkt ist aber nicht dokumentiert und nicht
für Fremdnutzung freigegeben. Der saubere Weg ist eine kurze Anfrage an die
Bürgerberatung Ludwigshafen bzw. die wer denkt was GmbH als Betreiber. Viele
Mängelmelder-Städte haben Open311/GeoReport v2 mit Schreib-Key; damit wären Absenden
und Statusabruf offiziell abgedeckt – und der Snapshot-Umweg könnte ganz entfallen.

## Anpassen

Oben in `index.html`:

```js
const DOMAIN_ID = 156;                                    // Ludwigshafen
const OFFICIAL  = "https://ludwigshafen.maengelmelder.de";
const FEED      = "./data.json";
```

Für eine andere Stadt: `DOMAIN_ID` und `OFFICIAL` tauschen, dieselben Werte in
`scripts/fetch_data.py` (`BASE`) eintragen. Die Kategorie-Kürzel und Kurznamen
stehen in den Objekten `ABBR` und `SHORT` und sind Ludwigshafen-spezifisch.

## Rechtliches

Die Daten sind die öffentlich einsehbaren Meldungen der Stadt Ludwigshafen; die Seite
zeigt sie nur anders an. Betreiber und Zuständigkeit bleiben bei der Stadt – ein Hinweis
darauf plus Link auf das Original gehört in den Footer, damit niemand die Seite für ein
Angebot der Stadt hält. Kartendaten: OpenStreetMap-Mitwirkende, Kacheln von CARTO.
