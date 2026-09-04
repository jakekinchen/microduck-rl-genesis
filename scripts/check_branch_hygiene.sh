#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

DIFF_BASE="${1:-}"
if [[ -z "$DIFF_BASE" || "$DIFF_BASE" =~ ^0+$ ]]; then
    if git rev-parse --verify HEAD^ >/dev/null 2>&1; then
        DIFF_BASE="HEAD^"
    else
        DIFF_BASE="HEAD"
    fi
fi
git rev-parse --verify "$DIFF_BASE^{commit}" >/dev/null

manifest_count=0
while IFS= read -r manifest; do
    receipt_root="$(dirname "$manifest")"
    if command -v sha256sum >/dev/null 2>&1; then
        (cd "$receipt_root" && sha256sum -c SHA256SUMS >/dev/null)
    else
        (cd "$receipt_root" && shasum -a 256 -c SHA256SUMS >/dev/null)
    fi
    manifest_count=$((manifest_count + 1))
done < <(git ls-files 'receipts/**/SHA256SUMS' | sort)

log_count=0
while IFS= read -r receipt_log; do
    receipt_root="$(dirname "$receipt_log")"
    while [[ "$receipt_root" != "." && ! -f "$receipt_root/SHA256SUMS" ]]; do
        receipt_root="$(dirname "$receipt_root")"
    done
    if [[ "$receipt_root" == "." ]]; then
        echo "Raw receipt log has no containing SHA256SUMS: $receipt_log" >&2
        exit 1
    fi
    relative_log="${receipt_log#"$receipt_root/"}"
    manifest="$receipt_root/SHA256SUMS"
    if ! grep -Fq "  $relative_log" "$manifest" \
        && ! grep -Fq "  ./$relative_log" "$manifest"; then
        echo "Raw receipt log is not manifest-bound: $receipt_log" >&2
        exit 1
    fi
    whitespace_attr="$(git check-attr whitespace -- "$receipt_log" | sed 's/^.*: whitespace: //')"
    if [[ "$whitespace_attr" != "-trailing-space,-space-before-tab" ]]; then
        echo "Unexpected whitespace policy for $receipt_log: $whitespace_attr" >&2
        exit 1
    fi
    log_count=$((log_count + 1))
done < <(git ls-files 'receipts/**/*.log' | sort)

git diff --check "$DIFF_BASE"...HEAD
echo "Branch hygiene passed: base=$DIFF_BASE manifests=$manifest_count immutable_logs=$log_count"
