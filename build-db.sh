#!/bin/bash
# Build a SQLite database from git history of tracked CSV files
# Uses https://github.com/simonw/git-history
#
# Usage: ./build-db.sh [output.db]

DB="${1:-data/prometeu.db}"

# Remove existing DB to rebuild from scratch
rm -f "$DB"

echo "Building $DB from git history..."
echo ""

# Border crossing wait times (composite key: crossing + vehicle type + direction)
echo "  → trafic-frontiere.csv"
if git-history file "$DB" data/politia-de-frontiera/trafic-frontiere.csv \
  --repo . \
  --id Denumire --id "Tip vehicul" --id Sens \
  --namespace trafic_frontiere \
  --csv --full-versions; then
  echo "    ✓ done"
else
  echo "    ✗ failed"
fi

echo "  → trafic-frontiere-map.csv"
if git-history file "$DB" data/politia-de-frontiera/trafic-frontiere-map.csv \
  --repo . \
  --id Denumire --id "Tip vehicul" --id Sens \
  --namespace trafic_frontiere_map \
  --csv --full-versions; then
  echo "    ✓ done"
else
  echo "    ✗ failed"
fi

# Brașov citizen reports - skipped for now
# The CSV has malformed rows (unescaped commas in free text fields)
# that cause column shifting. Needs CSV cleanup before git-history can process it.

# CMTEB heating system (zone + coordinates as composite key)
echo "  → status-sistem-termoficare-bucuresti.csv"
if git-history file "$DB" data/cmteb/status-sistem-termoficare-bucuresti.csv \
  --repo . \
  --id denumire --id Lat --id Long \
  --namespace cmteb \
  --csv --full-versions; then
  echo "    ✓ done"
else
  echo "    ✗ failed"
fi

# ANDNET road conditions - process all CSV files that have history
for f in data/andnet/csv/*.csv; do
  count=$(git log --oneline --follow "$f" 2>/dev/null | wc -l)
  if [ "$count" -gt 0 ]; then
    name=$(basename "$f" .csv)
    echo "  → andnet/$name.csv ($count versions)"
    if git-history file "$DB" "$f" \
      --repo . \
      --namespace "andnet_${name//-/_}" \
      --csv --full-versions 2>&1; then
      echo "    ✓ done"
    else
      echo "    ✗ skipped"
    fi
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
