#!/bin/bash
# Build a SQLite database from git history of tracked CSV files
# Uses https://github.com/simonw/git-history
#
# Usage: ./build-db.sh [output.db]

DB="${1:-data/prometeu.db}"

# Custom CSV converter that filters out malformed rows with None keys
# (common in scraped data with unescaped commas in free text fields)
SAFE_CSV_CONVERT='
import csv, io
text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
reader = csv.DictReader(io.StringIO(text))
return [row for row in reader if all(k is not None for k in row.keys())]
'

# Helper function to run git-history with safe CSV parsing
run_git_history() {
  local file="$1"
  local namespace="$2"
  shift 2
  # remaining args are extra flags like --id

  echo "  -> $file"
  if git-history file "$DB" "$file" \
    --repo . \
    --namespace "$namespace" \
    --convert "$SAFE_CSV_CONVERT" \
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
  trafic_frontiere \
  --id Denumire --id "Tip vehicul" --id Sens

run_git_history data/politia-de-frontiera/trafic-frontiere-map.csv \
  trafic_frontiere_map \
  --id Denumire --id "Tip vehicul" --id Sens

# === CMTEB heating system (zone + coordinates as composite key) ===
run_git_history data/cmteb/status-sistem-termoficare-bucuresti.csv \
  cmteb \
  --id denumire --id Lat --id Long

# === Bear interventions ===
run_git_history data/interventii-urs/interventii-urs.csv \
  interventii_urs \
  --id "Nr. Crt." \
  --ignore-duplicate-ids

# === Air quality ===
run_git_history data/local/B/aerlive-bucuresti.csv \
  aerlive_bucuresti

run_git_history data/local/IS/calitate-aer-is.csv \
  calitate_aer_iasi

# === Currency exchange rates ===
run_git_history data/financiar/curs-valutar.csv \
  curs_valutar

# === Brasov citizen reports ===
# run_git_history data/local/BV/sesizari-BV.csv \
#   sesizari_bv \
#   --id IncidentId \
#   --ignore-duplicate-ids

# === Brasov ski slopes ===
for f in data/local/BV/stare-partii/*.csv; do
  if [ -f "$f" ]; then
    name=$(basename "$f" .csv)
    run_git_history "$f" "partii_bv_${name//-/_}"
  fi
done

# === Energy distribution ===
for f in data/distributie-energie/*.csv; do
  if [ -f "$f" ]; then
    name=$(basename "$f" .csv)
    run_git_history "$f" "energie_${name//-/_}"
  fi
done

# === ANDNET road conditions ===
for f in data/andnet/csv/*.csv; do
  if [ -f "$f" ]; then
    name=$(basename "$f" .csv)
    run_git_history "$f" "andnet_${name//-/_}"
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
