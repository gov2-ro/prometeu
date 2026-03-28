#!/usr/bin/env bash
# Run all active scrapers and log output + status
# Usage: bash run-all-scrapers.sh
# Log saved to: data/_reports/scraper-run-YYYYMMDD-HHMMSS.log

mkdir -p data/_reports
LOG="data/_reports/scraper-run.log"

PASS=0
FAIL=0

# Parallel arrays instead of associative array (bash 3 compatible)
RESULT_NAMES=()
RESULT_STATUS=()

run_scraper() {
    local name="$1"
    local script="$2"
    printf "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    printf "▶  %s\n" "$name"
    printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    output=$(python $script 2>&1)
    status=$?
    echo "$output"
    RESULT_NAMES+=("$name")
    if [ $status -eq 0 ]; then
        RESULT_STATUS+=("OK")
        ((PASS++))
    else
        RESULT_STATUS+=("FAILED (exit $status)")
        ((FAIL++))
    fi
}

{
    echo "===== Scraper run: $(date) ====="

    run_scraper "CMTEB Termoficare București"         cmteb.py
    run_scraper "ANDNET Situație Drumuri map"          andnet-harta.py
    run_scraper "ANDNET Situație Drumuri list"         andnet-tables.py
    run_scraper "Sesizări BV"                          brasov-sesizari.py
    run_scraper "Pârtii BV"                            stare-partii-bv.py
    run_scraper "Instalații BV"                        instalatii-partie-bv.py
    run_scraper "Avarii PMB"                           pmb-avarii.py
    run_scraper "Iași calitate aer"                    iasi-calitate-aer.py
    run_scraper "Infoaer PMB București"                infoaer-bucuresti.py
    run_scraper "Aerlive București"                    aerlive-bucuresti.py
    run_scraper "Aerlive Cluj"                         aerlive-cj.py
    run_scraper "Curs valutar BNR"                     curs-valutar.py
    run_scraper "Trafic Frontieră map"                 trafic-frontiere-markers.py
    run_scraper "Trafic Frontieră list"                trafic-frontiere-list.py
    run_scraper "Intervenții Urs (Bear Interventions)" interventii-urs.py
    run_scraper "Normalise bear interventions CSV"     utils/normalise-urs.py
    run_scraper "Enel întreruperi"                     enel-intreruperi.py

    printf "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    printf "SUMMARY\n"
    printf "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    for i in "${!RESULT_NAMES[@]}"; do
        status="${RESULT_STATUS[$i]}"
        icon="✅"
        [ "$status" != "OK" ] && icon="❌"
        printf "  %s  %-45s %s\n" "$icon" "${RESULT_NAMES[$i]}" "$status"
    done
    printf "\n  Passed: %d  Failed: %d\n" "$PASS" "$FAIL"
    echo "===== Done: $(date) ====="

} 2>&1 | tee -a "$LOG"

echo ""
echo "Log saved to: $LOG"
