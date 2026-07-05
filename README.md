# OL-FS26 – Klimadaten Challenge

## Projektbeschreibung

Dieses Repository enthält die Datenpipeline, die Evaluation sowie das interaktive Dashboard des Projekts **Klimadaten Challenge**.

Ziel des Projekts ist es, die Auswirkungen des Klimawandels in der Schweiz anhand historischer Beobachtungsdaten und zukünftiger Klimaszenarien auf lokaler Ebene verständlich darzustellen. Das Dashboard kombiniert Scrollytelling-Elemente mit interaktiven Visualisierungen und ermöglicht die Untersuchung von Klimaprofilen für ausgewählte Schweizer Ortschaften.

Verwendete Datenquellen:

* E-OBS HOM (historische Temperaturdaten)
* CH2025 Klimaszenarien
* SwissNAMES3D
* swissALTIregio
* swissBOUNDARIES3D

---

## Architektur

```text
SwissNAMES3D
SwissALTIregio
SwissBOUNDARIES3D
E-OBS HOM
CH2025
        │
        ▼
Jupyter Notebooks
01 – 04
        │
        ▼
CSV / Parquet / NetCDF
        │
        ▼
src/
places.py
profiles.py
        │
        ▼
Dash Dashboard
(app.py)
```

---

## Repository-Struktur

```text
assets/          Styling, Bilder und SDG-Grafiken

data/
    raw/         Rohdaten
    processed/   CSV-Dateien für statische Visualisierungen

evaluation/
    01_evaluation_analysis.ipynb
    02_cronbachs_alpha.ipynb
    anonymised_results.xlsx

exports/         Voraggregierte Exportdateien

notebooks/
    01_prepare_places_from_swissnames.ipynb
    02_historical_eobs.ipynb
    03_future_ch2025.ipynb
    04_places_prototype.ipynb

src/
    places.py
    profiles.py

app.py
requirements.txt
```

---

## Python-Version

Entwickelt und getestet mit:

```text
Python 3.13
```

---

## Installation

Virtuelle Umgebung erstellen:

```bash
python -m venv .venv
```

Virtuelle Umgebung aktivieren:

```bash
.venv\Scripts\activate
```

Abhängigkeiten installieren:

```bash
pip install -r requirements.txt
```

---

## Externe Daten

Die Rohdaten und Exportdateien werden aufgrund ihrer Grösse über OneDrive bereitgestellt.

### Rohdaten

Download:

https://1drv.ms/f/c/3bbe1467cf26cf98/IgCsC7gZ0TguQrvmDyJ2zy1JARC-UxqIywmAYWbWqHLUxB0?e=f0MPja

Die Dateien sind nach dem Download im Ordner

```text
data
```

abzulegen.

Enthalten sind unter anderem im Unterordner
```text
raw
```

* E-OBS HOM
* CH2025 Klimaszenarien
* SwissNAMES3D
* swissALTIregio
* swissBOUNDARIES3D

sowie vearbeitete Daten im Unterordner
```text
processed
```

### Exportdateien

Download:

https://1drv.ms/f/c/3bbe1467cf26cf98/IgCulLKBpZfNR4Hkb7xeGkwqAd4Fe9h8wxUohU6d7K4zSF0?e=H35HO6

Die Dateien sind nach dem Download im Ordner

```text
exports
```

abzulegen.

Die Exportdateien sowie die verarbeiteten Dateien ermöglichen den direkten Start des Dashboards, ohne die vollständige Datenpipeline erneut ausführen zu müssen.

---

## Datenpipeline

Die Datenpipeline besteht aus vier Jupyter Notebooks.

### 1. Orte vorbereiten

```text
01_prepare_places_from_swissnames.ipynb
```

Verarbeitet:

* SwissNAMES3D
* swissALTIregio

Erzeugt:

```text
places_candidates.csv
```

---
Hinweis: Das erzeugte CSV diente nur als Basis für die Ortschaften im Dashboard. Diese wurden manuell ergänzt und als places.csv abgelegt. Es empfiehlt sich, das Dashboard mit den kuratierten Daten laufen zu lassen (Beschreibungen, zusätzliche Orte).
### 2. Historische Daten aufbereiten

```text
02_historical_eobs.ipynb
```

Verarbeitet:

* E-OBS HOM
* Höhenzonen

Erzeugt unter anderem:

```text
tg_ch.nc
tx_ch.nc
zone_tg.nc
zone_tx.nc
```

sowie die CSV-Dateien für die statischen Visualisierungen.

---

### 3. Zukunftsszenarien aufbereiten

```text
03_future_ch2025.ipynb
```

Verarbeitet:

* CH2025 Klimaszenarien

Erzeugt:

```text
ds_tas_all.nc
ds_tasmax_all.nc
zone_ch2025.nc
```

---

### 4. Klimaprofile erzeugen

```text
04_places_prototype.ipynb
```

Verknüpft:

* Orte
* historische Daten
* Zukunftsszenarien

Erzeugt:

```text
place_profiles_all.parquet
```

sowie die zugehörigen Lookup-Tabellen und Zwischentabellen.

Hinweis: Die Berechnung der Klimaprofile für CH2025 benötigt aufgrund der umfangreichen Datenbasis (mehrere Szenarien, hohe Grid-Auflösung) mehrere Stunden Laufzeit.

---

## Dashboard starten

Nach erfolgreicher Installation:

```bash
python app.py
```

Das Dashboard wurde mit Google Chrome getestet.

Bei Verwendung von PyCharm kann über das Kontextmenü festgelegt werden, welcher Browser für den Start verwendet werden soll.

---

## Evaluation

Die Evaluation der statischen Visualisierungen befindet sich im Ordner

```text
evaluation/
```

und umfasst:

* Fragebogenauswertung
* Cronbach's Alpha Analyse
* anonymisierte Resultate

Die Evaluation wird im Projektdokument im Kapitel 5 sowie in den Anhängen B und C dokumentiert.

---

## Bekannte Einschränkungen

* Niederschlag ist aktuell nicht Bestandteil der Datenpipeline.
* Die Integration von Bildern für Featured Places ist angedacht, jedoch noch nicht umgesetzt.
* Weitere Klimaparameter könnten in zukünftigen Versionen ergänzt werden.
* Die CH2025 Referenzszenarien werden in Teilen der Pipeline noch mitgeführt, obwohl sie im Dashboard nicht mehr verwendet werden.

---

## Lizenz

Dieses Repository wurde im Rahmen des Moduls **Klimadaten Challenge** erstellt.

Die verwendeten Datensätze unterliegen den Lizenzbedingungen der jeweiligen Datenanbieter.
