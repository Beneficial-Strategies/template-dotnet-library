#!/usr/bin/env bash
# Packs the package, then builds and runs every example against that package and compares its output with the
# expected-output.txt kept beside it. Exit code 1 if an example fails to build, exits with an error, or differs.
# With --update, writes the output of each example to its expected-output.txt instead of comparing.
set -euo pipefail
cd "$(dirname "$0")/.."

update=false
[ "${1:-}" = "--update" ] && update=true

rm -rf artifacts/packages
for project in src/*/*.csproj; do
  dotnet pack "$project" -c Release -o artifacts/packages --nologo -v q
done

# A time limit where the system has `timeout` (Linux, CI); macOS has none.
limit=""
command -v timeout >/dev/null && limit="timeout 120"

status=0
for dir in examples/[0-9][0-9]-*/; do
  name=$(basename "$dir")
  out=$(mktemp)
  if ! (cd "$dir" && $limit dotnet run -c Release --nologo > "$out"); then
    echo "FAIL  $name: did not build or exited with an error"
    status=1
  elif $update; then
    cp "$out" "$dir/expected-output.txt"
    echo "wrote $name/expected-output.txt"
  elif diff -u "$dir/expected-output.txt" "$out"; then
    echo "ok    $name"
  else
    echo "FAIL  $name: output differs from expected-output.txt"
    status=1
  fi
  rm -f "$out"
done
exit $status
