#!/bin/bash
# Build a SQLite database from git history of tracked CSV files
# Uses https://github.com/simonw/git-history
#
# Usage: ./build-db.sh [output.db]

set -e

DB="${1:-prometeu.db}"

# Remove existing DB to rebuild from scratch
rm -f "$DB"

echo "Building $DB from git history..."

# Border crossing wait times (composite key: crossing + vehicle type + direction)
echo "  → trafic-frontiere.csv"
git-history file "$DB" data/politia-de-frontiera/trafic-frontiere.csv \
  --repo . \
  --id Denumire --id "Tip vehicul" --id Sens \
  --namespace trafic_frontiere \
  --csv --full-versions

echo "  → trafic-frontiere-map.csv"
git-history file "$DB" data/politia-de-frontiera/trafic-frontiere-map.csv \
  --repo . \
  --id Denumire --id "Tip vehicul" --id Sens \
  --namespace trafic_frontiere_map \
  --csv --full-versions

# Brașov citizen reports - skipped for now
# The CSV has malformed rows (unescaped commas in free text fields)
# that cause column shifting. Needs CSV cleanup before git-history can process it.
# echo "  → sesizari-BV.csv"
# git-history file "$DB" data/local/BV/sesizari-BV.csv \
#   --repo . \
#   --id IncidentId \
#   --namespace sesizari_bv \
#   --csv --full-versions \
#   --ignore-duplicate-ids

# CMTEB heating system (zone as key)
echo "  → status-sistem-termoficare-bucuresti.csv"
git-history file "$DB" data/cmteb/status-sistem-termoficare-bucuresti.csv \
  --repo . \
  --id denumire --id Lat --id Long \
  --namespace cmteb \
  --csv --full-versions

# ANDNET road conditions - process all CSV files that have history
for f in data/andnet/csv/*.csv; do
  count=$(git log --oneline --follow "$f" 2>/dev/null | wc -l)
  if [ "$count" -gt 0 ]; then
    name=$(basename "$f" .csv)
    echo "  → andnet/$name.csv ($count versions)"
    git-history file "$DB" "$f" \
      --repo . \
      --namespace "andnet_${name//-/_}" \
      --csv --full-versions 2>&1 || echo "    (skipped - no suitable ID column)"
  fi
done

echo ""
echo "Done! Database: $DB"
echo "Tables:"
sqlite-utils tables "$DB" --table
echo ""
echo "Run with: datasette $DB --metadata utils/datasette/metadata.json"
