#!/usr/bin/env python3
"""Prepare the next release: pick the version from labels, write the entry of CHANGELOG.md from the issues resolved.

The version has three parts, design.breaking.compatible. It is written like a Semantic Versioning number but is not one:
the first part changes with a redesign, the second with a change that breaks existing users, the third with every other change.

What it does, in order:
  1. finds the last release tag (v*) and its date;
  2. lists the issues closed as completed since then, and the merged pull requests that closed them;
  3. chooses the bump from the labels of those issues (highest wins):
       redesign         -> the first part   (the others reset)
       breaking-change  -> the second part  (the third resets)
       anything else    -> the third part
  4. writes <Version> in Directory.Build.props and puts an entry at the top of CHANGELOG.md.

Nothing is committed, tagged or published here. The workflow pushes a release/vX.Y.Z branch for review; the tag that
publishes stays a deliberate, manual act (see CONTRIBUTING.md).

Run locally:  python3 tools/releasing/prepare_release.py --dry-run
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

DESIGN_LABELS = {"redesign"}
BREAKING_LABELS = {"breaking-change"}
ADDED_LABELS = {"enhancement"}
SKIP_LABELS = {"no-release-notes"}
PROPS = "Directory.Build.props"
CHANGELOG = "CHANGELOG.md"
CATEGORIES = [("breaking", "Breaking change"), ("added", "Added"), ("fixed", "Fixed"), ("changed", "Changed")]
BUMP_ORDER = {"compatible": 0, "breaking": 1, "design": 2}


def category(labels):
    """The heading an entry goes under."""
    if labels & (DESIGN_LABELS | BREAKING_LABELS):
        return "breaking"
    if labels & ADDED_LABELS:
        return "added"
    if "bug" in labels:
        return "fixed"
    return "changed"


def bump_for(labels):
    if labels & DESIGN_LABELS:
        return "design"
    if labels & BREAKING_LABELS:
        return "breaking"
    return "compatible"


def choose_bump(entries):
    return max((e["bump"] for e in entries), key=BUMP_ORDER.get)


def parse_version(text):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(-[0-9A-Za-z.-]+)?", text.strip())
    if not m:
        raise ValueError(f"not a version: {text!r}")
    return int(m[1]), int(m[2]), int(m[3]), m[4] or ""


def next_version(current, bump):
    """Raise one part and reset the parts after it, keeping the suffix (-alpha): removing it is the owner's decision."""
    design, breaking, compatible, suffix = parse_version(current)
    if bump == "design":
        return f"{design + 1}.0.0{suffix}"
    if bump == "breaking":
        return f"{design}.{breaking + 1}.0{suffix}"
    return f"{design}.{breaking}.{compatible + 1}{suffix}"


def release_note(issue, pr_bodies):
    """A 'Release note:' line in a closing pull request, then in the issue, else the issue title."""
    pattern = re.compile(r"^\s*release note:[ \t]*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
    for body in [*pr_bodies, issue.get("body") or ""]:
        m = pattern.search(body)
        if m and m[1] and not m[1].startswith("<!--"):
            return m[1]
    return issue["title"].strip()


def build_entries(issues, prs_by_issue):
    entries = []
    for issue in issues:
        labels = {l["name"] for l in issue.get("labels", [])}
        if labels & SKIP_LABELS:
            continue
        if issue.get("stateReason") not in (None, "COMPLETED"):      # closed as not planned or duplicate: nothing was done
            continue
        entries.append({
            "number": issue["number"],
            "text": release_note(issue, prs_by_issue.get(issue["number"], [])),
            "category": category(labels),
            "bump": bump_for(labels),
        })
    return sorted(entries, key=lambda e: e["number"])


def render_entry(version, entries, today):
    """One version's entry: a heading with the date, then a line per issue grouped under the headings."""
    lines = [f"## {version} ({today})", ""]
    if not entries:
        lines.append("No changes.")
    for key, heading in CATEGORIES:
        for e in (x for x in entries if x["category"] == key):
            lines.append(f"* {heading}: {e['text'].rstrip('.')} (#{e['number']}).")
    return "\n".join(lines) + "\n"


def add_entry(changelog, entry):
    """Put the entry above the previous one, below the introduction."""
    m = re.search(r"^## ", changelog, re.MULTILINE)
    if not m:
        return changelog.rstrip("\n") + "\n\n" + entry
    return changelog[: m.start()] + entry + "\n" + changelog[m.start():]


def set_version(props_text, new):
    out, n = re.subn(r"(<Version>)[^<]+(</Version>)", rf"\g<1>{new}\g<2>", props_text, count=1)
    if n != 1:
        raise SystemExit("could not find <Version> in Directory.Build.props")
    return out


# ---- GitHub and git ----

def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def last_tag():
    tags = run("git", "tag", "--list", "v*", "--sort=-v:refname").split()
    return tags[0] if tags else None


def fetch(since_iso):
    issues = json.loads(run(
        "gh", "issue", "list", "--state", "closed", "--limit", "500", "--search", f"closed:>{since_iso}",
        "--json", "number,title,labels,body,stateReason,closedAt"))
    prs = json.loads(run(
        "gh", "pr", "list", "--state", "merged", "--limit", "500", "--search", f"merged:>{since_iso}",
        "--json", "number,body,closingIssuesReferences"))
    by_issue = {}
    for pr in prs:
        for ref in pr.get("closingIssuesReferences", []):
            by_issue.setdefault(ref["number"], []).append(pr.get("body") or "")
    return issues, by_issue


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bump", choices=["auto", "design", "breaking", "compatible"], default="auto")
    ap.add_argument("--since", help="tag to release since (default: the newest v* tag)")
    ap.add_argument("--suffix", help="replace the pre-release suffix, for example -beta; '' removes it (the owner's decision)")
    ap.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")
    args = ap.parse_args()

    root = Path(run("git", "rev-parse", "--show-toplevel"))
    tag = args.since or last_tag()
    since = run("git", "log", "-1", "--format=%cI", tag) if tag else "1970-01-01T00:00:00Z"
    issues, prs_by_issue = fetch(since)
    entries = build_entries(issues, prs_by_issue)
    if not entries:
        print(f"Nothing to release: no issue closed as completed since {tag or 'the start'} ({since}) carries release notes.")
        return 0

    props = (root / PROPS).read_text()
    current = re.search(r"<Version>([^<]+)</Version>", props)[1]
    bump = choose_bump(entries) if args.bump == "auto" else args.bump
    version = next_version(current, bump)
    if args.suffix is not None:
        version = re.sub(r"-.*$", "", version) + args.suffix

    print(f"Last release: {tag} ({since})\nCurrent version: {current}\nBump: {bump}  ->  {version}\n")
    for e in entries:
        print(f"  #{e['number']:<4} {e['bump']:<11} {e['category']:<9} {e['text']}")
    print()
    entry = render_entry(version, entries, date.today().isoformat())
    writes = {
        PROPS: set_version(props, version),
        CHANGELOG: add_entry((root / CHANGELOG).read_text(), entry),
    }
    print(f"--- {CHANGELOG}\n{entry}")
    if args.dry_run:
        print("Dry run: nothing written.")
    else:
        for path, text in writes.items():
            (root / path).write_text(text)
        print(f"Wrote {len(writes)} files.")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"version={version}\nbump={bump}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
