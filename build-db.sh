#!/bin/bash
# Build a SQLite database from git history of tracked CSV files
# Uses https://github.com/simonw/git-history
#
# Usage: ./build-db.sh [output.db]

DB="${1:-data/prometeu.db}"

# Base CSV converter: strips None keys, handles encoding and parse errors
BASE_CSV_CONVERT='
import csv, io
text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
try:
    reader = csv.DictReader(io.StringIO(text))
    return [{k: v for k, v in row.items() if k is not None} for row in reader]
except csv.Error:
    return []
'

# Converter for trafic-frontiere: normalizes old column names to current names
# Old format used: Level, tip_vehicol, sens
# New format uses: Status, Tip vehicul, Sens
TRAFIC_CONVERT='
import csv, io
RENAMES = {"Level": "Status", "tip_vehicol": "Tip vehicul", "sens": "Sens"}
text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
try:
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        r = {k: v for k, v in row.items() if k is not None}
        r = {RENAMES.get(k, k): v for k, v in r.items()}
        rows.append(r)
    return rows
except csv.Error:
    return []
'

# Converter for cmteb: normalizes old column names (latitudine/longitudine -> Lat/Long)
CMTEB_CONVERT='
import csv, io
RENAMES = {"latitudine": "Lat", "longitudine": "Long"}
text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
try:
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        r = {k: v for k, v in row.items() if k is not None}
        r = {RENAMES.get(k, k): v for k, v in r.items()}
        rows.append(r)
    return rows
except csv.Error:
    return []
'

# Converter for interventii_urs: normalizes old capitalized column names
# Old format: Judet, UAT, Echipa de interventie, Sex, Metoda de interventie...
# New format: judet, uat, echipa_interventie, sex_urs, metoda_interventie...
INTERVENTII_URS_CONVERT='
import csv, io
RENAMES = {
    "Judet": "judet", "UAT": "uat",
    "Echipa de interventie": "echipa_interventie",
    "Sex": "sex_urs",
    "Detalii referitoare la eveniment": "descriere_eveniment",
    "Metoda de interventie": "metoda_interventie",
    "Adaugat de": "adaugat_de",
}
text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
try:
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        r = {k: v for k, v in row.items() if k is not None}
        r = {RENAMES.get(k, k): v for k, v in r.items()}
        rows.append(r)
    return rows
except csv.Error:
    return []
'

# Helper function to run git-history with safe CSV parsing
run_git_history() {
  local file="$1"
  local namespace="$2"
  local converter="$3"
  shift 3
  # remaining args are extra flags like --id

  echo "  -> $file"
  if git-history file "$DB" "$file" \
    --repo . \
    --namespace "$namespace" \
    --convert "$converter" \
    --import csv --import io \
    --full-versions \
    "$@" 2>&1; then
    echo "    OK"
  else
    echo "    FAILED"
  fi
}

# Remove existing DB to rebuild from scratch
rm -f "$DB"

echo "Building $DB from git history..."
echo ""

# === Border crossings (Politia de Frontiera) ===
run_git_history data/politia-de-frontiera/trafic-frontiere.csv \
  trafic_frontiere "$TRAFIC_CONVERT" \
  --id Denumire --id "Tip vehicul" --id Sens

run_git_history data/politia-de-frontiera/trafic-frontiere-map.csv \
  trafic_frontiere_map "$TRAFIC_CONVERT" \
  --id Denumire --id "Tip vehicul" --id Sens

# === CMTEB heating system ===
run_git_history data/cmteb/status-sistem-termoficare-bucuresti.csv \
  cmteb "$CMTEB_CONVERT" \
  --id denumire --id Lat --id Long

# === Bear interventions ===
run_git_history data/interventii-urs/interventii-urs.csv \
  interventii_urs "$INTERVENTII_URS_CONVERT" \
  --id judet --id uat --id data_interventie \
  --ignore-duplicate-ids

# === Air quality ===
run_git_history data/local/B/aerlive-bucuresti.csv \
  aerlive_bucuresti "$BASE_CSV_CONVERT" \
  --id id --id name \
  --ignore-duplicate-ids

run_git_history data/local/IS/calitate-aer-is.csv \
  calitate_aer_iasi "$BASE_CSV_CONVERT"

# === Currency exchange rates ===
run_git_history data/financiar/curs-valutar.csv \
  curs_valutar "$BASE_CSV_CONVERT"

# === Brasov citizen reports ===
# Commented out — takes very long to build
# run_git_history data/local/BV/sesizari-BV.csv \
#   sesizari_bv "$BASE_CSV_CONVERT" \
#   --id IncidentId \
#   --ignore-duplicate-ids

# === Brasov ski slopes ===
for f in data/local/BV/stare-partii/*.csv; do
  if [ -f "$f" ]; then
    name=$(basename "$f" .csv)
    run_git_history "$f" "partii_bv_${name//-/_}" "$BASE_CSV_CONVERT"
  fi
done

# === Energy distribution ===
for f in data/distributie-energie/*.csv; do
  if [ -f "$f" ]; then
    name=$(basename "$f" .csv)
    run_git_history "$f" "energie_${name//-/_}" "$BASE_CSV_CONVERT"
  fi
done

# === ANDNET road conditions ===
for f in data/andnet/csv/*.csv; do
  if [ -f "$f" ]; then
    name=$(basename "$f" .csv)
    run_git_history "$f" "andnet_${name//-/_}" "$BASE_CSV_CONVERT"
  fi
done

echo ""
echo "Done! Database: $DB"
if command -v sqlite-utils &> /dev/null; then
  echo "Tables:"
  sqlite-utils tables "$DB" --counts --table
  echo ""
fi
echo "Run with: datasette $DB --metadata utils/datasette/metadata.json"
