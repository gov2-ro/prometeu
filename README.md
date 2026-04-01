gov.ro open data curator

# _Grebla lu' Prometeu_

Arhivare automată de date publice din România, folosind [Git scraping](https://simonwillison.net/2020/Oct/9/git-scraping/).

Datele se colectează la fiecare 6 ore prin GitHub Actions și se commitează direct pe `main`. Istoricul modificărilor e vizibil în git.

[flatgithub.com/gov2-ro/prometeu](https://flatgithub.com/gov2-ro/prometeu) (Flat Data viewer)

---

## Surse de date

| Sursă | Date | Frecvență |
|-------|------|-----------|
| [ANDNET](https://dispecerat.andnet.ro/) | Situația drumurilor — meteo, temperatură, lucrări, circulație | 6h |
| [Poliția de Frontieră](https://www.politiadefrontiera.ro/ro/traficonline) | Timp așteptare puncte trecere frontieră | 6h |
| [MMAP](https://interventiiurs.mmap.ro/centralizator/) | Intervenții urs — alungare, relocare, eutanasiere, împușcare | 6h |
| [BNR](https://www.bnr.ro) | Curs valutar | 6h |
| [CMTEB](https://www.cmteb.ro/) | Stare sistem termoficare București | 6h |
| [InfoAer PMB](https://infoaer.pmb.ro/) | Calitate aer București (senzori) | 6h |
| [Iași Open Data](https://opendata.oras.digital/) | Calitate aer Iași | 6h |
| [e-distribuție / Enel](https://www.e-distributie.com/ro/intreruperi-curent.html) | Întreruperi distribuție energie | 6h |
| [Brașov City](https://starepartii.brasovcity.ro/) | Stare pârtii + instalații Poiana Brașov | 6h |
| [Brașov Sesizări](https://sesizari.brasovcity.ro/) | Sesizări cetățeni Brașov | 6h |
| [PMB Avarii](https://www.pmb.ro/) | Avarii apă/termoficare București | 6h |
| [Inspectorul Pădurii](https://inspectorulpadurii.ro/) | SUMAL — avize transport material lemnos | săptămânal |

### Inactive / probleme server

- **aerlive-bucuresti.py**, **aerlive-cj.py** — certificat SSL expirat pe server
- **deer-incidente.py**, **deer-intreruperi.py** — API modificat
- **posturi.gov.ro** — dezactivat temporar
- **turism-structuri-autorizate.py** — descarcă fișiere Excel/PDF de pe turism.gov.ro

---

## Vizualizare

Datele se pot vizualiza cu [Datasette](https://datasette.io/) + [datasette-dashboards](https://github.com/rclement/datasette-dashboards):

```bash
./build-db.sh                # construiește baza SQLite din istoricul git
datasette data/prometeu.db --metadata utils/datasette/metadata.json
```

Dashboard-uri disponibile: trafic frontieră, termoficare, calitate aer, curs valutar, intervenții urs, SUMAL, sesizări Brașov.

---

## Rulare locală

```bash
pip install -r requirements.txt
bash run-all-scrapers.sh      # rulează toate scraperele, log în data/_reports/
```
