#!/bin/bash
# rename_journals.sh
# Normalize Elite Dangerous journal filenames:
# - remove "CAPI" if present
# - insert "20" after "Journal." only for short numeric dates
# - skip files already in ISO 8601 format

shopt -s nullglob

for f in *Journal.*.log; do
  # skip ISO-style timestamps (contain '-' or 'T')
  [[ "$f" =~ -|T ]] && continue

  # strip CAPI if present
  base="${f/CAPI/}"

  # insert "20" after "Journal."
  new="${base/Journal./Journal.20}"

  # rename only if actually changed
  if [[ "$f" != "$new" ]]; then
    echo "Renaming: $f → $new"
    mv -i -- "$f" "$new"
  fi
done
