#!/usr/bin/env bash
# WC-2026-005 — local results summarizer.
# Parses ONLY the log file supplied by the user. Contacts nothing.
# Usage: ./collect-results.sh [path-to-results.log]
set -u

LOG="${1:-results.log}"
if [[ ! -f "$LOG" ]]; then
  echo "error: log file not found: $LOG" >&2
  echo "usage: $0 [path-to-results.log]" >&2
  exit 1
fi

echo "=== WC-2026-005 results summary ($LOG) ==="
echo

total=$(grep -c "VICTIM_REQ" "$LOG" || true)
cookie_yes=$(grep "VICTIM_REQ" "$LOG" | grep -c "test_cookie_present=yes" || true)
cookie_no=$(grep "VICTIM_REQ" "$LOG" | grep -c "test_cookie_present=no" || true)

echo "victim requests logged: $total"
echo "  with test cookie present: $cookie_yes"
echo "  without test cookie:     $cookie_no"
echo

echo "--- per-request detail ---"
grep "VICTIM_REQ" "$LOG" | sed 's/^/  /'
echo

echo "--- fixture messages (if any) ---"
grep "FIXTURE_MSG" "$LOG" | sed 's/^/  /' || true
echo

# Interpretation hints (local-only; no network).
echo "--- interpretation ---"
if [[ "$total" -eq 0 ]]; then
  echo "  No /victim requests logged. Did the popup open and fetch?"
  echo "  Check the browser console and the on-page status line."
elif [[ "$cookie_yes" -gt 0 && "$cookie_no" -gt 0 ]]; then
  echo "  Mixed results: some requests carried the test cookie, some did not."
  echo "  Correlate timestamps with the case being run (candidate vs controls)."
elif [[ "$cookie_yes" -gt 0 ]]; then
  echo "  All logged requests carried the test cookie."
  echo "  If this includes the candidate case AND Control 1/2, re-check controls."
else
  echo "  No logged request carried the test cookie."
  echo "  If this includes the candidate case, the candidate behavior was NOT observed."
fi
