#!/usr/bin/env bash
# Creates the labels the workflows and the release script use, in the repository the current directory belongs to (needs gh, logged in).
# GitHub does not copy labels from a template repository. Safe to run again: an existing label is left as it is.
set -uo pipefail
while IFS='|' read -r name description; do
  gh label create "$name" --description "$description" 2>&1 | sed "s/^/$name: /" | grep -v "already exists" || true
done <<'LABELS'
redesign|A redesign of the package: raises the first part of the version
breaking-change|Changes the public API or behaviour: raises the second part of the version
tightens|Refuses input the package used to accept: breaking, raises the second part of the version
loosens|Accepts input the package used to refuse: compatible unless also breaking-change
changes-output|Writes different text for the same value: breaking, raises the second part of the version
ci|Build, test, publish and repository automation
tech-debt|Cleanup that does not change behaviour
needs-test|A bug without a test that reproduces it yet
needs-triage|New and not yet looked at
no-issue|A pull request that needs no issue (typo, generated file); skips the issue-link check
no-release-notes|Leave this out of the changelog (and of the version bump)
maintainer-wanted|An area where a co-maintainer or sponsor would make the difference
release|Blocks or is part of a release
LABELS
