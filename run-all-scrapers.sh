#!/bin/bash
# Run all active scrapers and log output + status
# Usage: ./run-all-scrapers.sh [logfile]
# Example: ./run-all-scrapers.sh scraper-run.log

LOG="${1:-scraper-run-$(date +%Y%m%d-%H%M%S).log}"
PASS=0
FAIL=0
SKIP=0

declare -A RESULTS

run_scraper() {
    local name="$1"
    local script="$2"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶  $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    output=$(python $script 2>&1)
    status=$?
    echo "$output"
    if [ $status -eq 0 ]; then
        RESULTS["$name"]="✅ OK"
        ((PASS++))
    else
        RESULTS["$name"]="❌ FAILED (exit $status)"
        ((FAIL++))
    fi
}

echo "Running all scrapers — $(date)"
echo "Log: $LOG"

{
    echo "===== Scraper run: $(date) ====="

    run_scraper "CMTEB Termoficare București"        cmteb.py
    run_scraper "ANDNET Situație Drumuri map"         andnet-harta.py
    run_scraper "ANDNET Situație Drumuri list"        andnet-tables.py
    run_scraper "Sesizări BV"                         brasov-sesizari.py
    run_scraper "Pârtii BV"                           stare-partii-bv.py
    run_scraper "Instalații BV"                       instalatii-partie-bv.py
    run_scraper "Avarii PMB"                          pmb-avarii.py
    run_scraper "Iași calitate aer"                   iasi-calitate-aer.py
    run_scraper "Infoaer PMB București"               infoaer-bucuresti.py
    run_scraper "Aerlive București"                   aerlive-bucuresti.py
    run_scraper "Aerlive Cluj"                        aerlive-cj.py
    run_scraper "Curs valutar BNR"                    curs-valutar.py
    run_scraper "Trafic Frontieră map"                trafic-frontiere-markers.py
    run_scraper "Trafic Frontieră list"               trafic-frontiere-list.py
    run_scraper "Intervenții Urs (Bear Interventions)" interventii-urs.py
    run_scraper "Normalise bear interventions CSV"    utils/normalise-urs.py
    run_scraper "Enel întreruperi"                    enel-intreruperi.py

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SUMMARY"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    for name in "${!RESULTS[@]}"; do
        printf "  %-45s %s\n" "$name" "${RESULTS[$name]}"
    done | sort
    echo ""
    echo "  Passed: $PASS  Failed: $FAIL"
    echo "===== Done: $(date) ====="

} 2>&1 | tee "$LOG"

echo ""
echo "Full log saved to: $LOG"
