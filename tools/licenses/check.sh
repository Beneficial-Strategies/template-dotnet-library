#!/usr/bin/env bash
# Fails if a package that any published project depends on (directly or not) has a license outside the allowed list,
# or none that can be determined. Run from the repository root. See tools/licenses/README.md.
set -euo pipefail

TOOL_VERSION=4.0.18
ALLOWED="MIT;Apache-2.0;BSD-2-Clause;BSD-3-Clause;ISC;0BSD"

if ! command -v nuget-license >/dev/null 2>&1; then
  dotnet tool install --global nuget-license --version "$TOOL_VERSION"
  export PATH="$PATH:$HOME/.dotnet/tools"
fi

projects=$(mktemp)
printf '[' > "$projects"
sep=""
for project in src/*/*.csproj; do printf '%s"%s"' "$sep" "$project" >> "$projects"; sep=","; done
printf ']' >> "$projects"

nuget-license \
  -ji "$projects" \
  -t \
  -a "$ALLOWED" \
  -mapping tools/licenses/license-url-mappings.json \
  -o Table
