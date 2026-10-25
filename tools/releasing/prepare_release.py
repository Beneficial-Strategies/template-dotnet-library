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
       tightens         -> the second part  (the type refuses input it used to accept)
       changes-output   -> the second part  (the same value is written differently)
       loosens          -> the third part   (the type accepts more; add breaking-change if code depends on the old limit)
       anything else    -> the third part
  4. lists the issues still open as known issues (a "Known issue:" line in the issue, else its title); issues labelled
     enhancement, documentation, tech-debt, ci, release, question, needs-triage or no-release-notes are not known issues;
  5. writes <Version> in Directory.Build.props and puts an entry at the top of CHANGELOG.md.

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
BREAKING_LABELS = {"breaking-change", "tightens", "changes-output"}
ADDED_LABELS = {"enhancement"}
SKIP_LABELS = {"no-release-notes"}
# open issues with one of these labels are not something a consumer needs to know about
NOT_KNOWN_ISSUES = {"enhancement", "documentation", "tech-debt", "ci", "release", "question", "needs-triage", "duplicate", "invalid", "wontfix"} | SKIP_LABELS
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


def known_issue_note(issue):
    """A 'Known issue:' line in the issue, else its title."""
    m = re.search(r"^\s*known issue:[ \t]*(.+?)\s*$", issue.get("body") or "", re.IGNORECASE | re.MULTILINE)
    return m[1] if m and not m[1].startswith("<!--") else issue["title"].strip()


def build_known_issues(open_issues):
    """The open issues a consumer should know about when the version is released."""
    known = []
    for issue in open_issues:
        if {l["name"] for l in issue.get("labels", [])} & NOT_KNOWN_ISSUES:
            continue
        known.append({"number": issue["number"], "text": known_issue_note(issue)})
    return sorted(known, key=lambda k: k["number"])


def render_entry(version, entries, today, known=()):
    """One version's entry: a heading with the date, a line per issue grouped under the headings, then the known issues."""
    lines = [f"## {version} ({today})", ""]
    if not entries:
        lines.append("No changes.")
    for key, heading in CATEGORIES:
        for e in (x for x in entries if x["category"] == key):
            lines.append(f"* {heading}: {e['text'].rstrip('.')} (#{e['number']}).")
    for k in known:
        lines.append(f"* Known issue: {k['text'].rstrip('.')} (#{k['number']}).")
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


def find_package_id(root):
    """The NuGet id of the package, from the first <PackageId> under src/, or None."""
    for project in sorted((root / "src").rglob("*.csproj")):
        m = re.search(r"<PackageId>([^<]+)</PackageId>", project.read_text(encoding="utf-8"))
        if m:
            return m[1]
    return None


def next_steps(version, repo_url=None, package_id=None, workflow=False, dry_run=False):
    """The steps from the written files to a published package, each with the reason for it (a training aid).

    workflow: the Prepare release workflow pushes the branch itself, so the steps start at the pull request.
    """
    tag, branch = f"v{version}", f"release/v{version}"
    steps = []
    if not workflow:
        steps += [
            ("Put the release on its own branch.",
             "main stays untouched until someone has reviewed the version and the notes.",
             [f"git checkout -b {branch}"]),
            ("Check that only the version and the notes changed.",
             "A release commit should carry nothing else. Expect Directory.Build.props and CHANGELOG.md.",
             ["git status", "git diff"]),
            ("Commit the two files.",
             "This is the one commit that says 'this is version " + version + "'.",
             ["git add Directory.Build.props CHANGELOG.md", f'git commit -m "Release {version}: version and changelog"']),
            ("Push the branch.",
             "GitHub needs the branch before it can show a pull request.",
             [f"git push -u origin {branch}"]),
        ]
    steps += [
        ("Open a pull request from the release branch into main.",
         "The checks run on it and the changelog gets a last review. Branches named release/ need no linked issue. "
         f"Title: Release {version}. A one-line body is enough.",
         [f"{repo_url}/compare/main...{branch}?expand=1&title=Release%20{version}" if repo_url else "open it from the branch page on GitHub"]),
        ("Merge it when the checks are green.",
         "This puts the version and the notes on main. A squash or a regular merge both work, because the tag is placed afterwards. "
         "Merging publishes nothing.",
         []),
        ("Bring main up to date and look at the release commit.",
         "The tag must go on the commit that is now the tip of main; with a squash merge that is a new commit, not the one on your branch.",
         ["git checkout main", "git pull", "git log -1 --oneline", "grep '<Version>' Directory.Build.props"]),
        ("Tag that commit.",
         f"A tag is a permanent name for one commit. {tag} names the release, and the version in the package comes from the props file you just merged.",
         [f"git tag {tag}"]),
        ("Push the tag.",
         "Pushing a tag that starts with v is what tells GitHub to run Publish to NuGet. Nothing is uploaded until you do this, and a published version cannot be taken back.",
         [f"git push origin {tag}"]),
        ("Watch the publish and find the package.",
         "The workflow builds, tests and publishes. nuget.org can take several minutes to list the new version.",
         ([f"{repo_url}/actions" if repo_url else "the Actions tab of the repository"]
          + ([f"https://www.nuget.org/packages/{package_id}/{version}"] if package_id else []))),
    ]
    lines = ["What to do next (each step says why):", ""]
    if dry_run:
        lines += ["Nothing has been written yet; after the real run these are the steps.", ""]
    for i, (what, why, commands) in enumerate(steps, 1):
        lines += [f"{i}. {what}", f"   Why: {why}"]
        lines += [f"   $ {c}" if not c.startswith("http") and not c.startswith("the ") and not c.startswith("open ") else f"   {c}" for c in commands]
        lines.append("")
    return "\n".join(lines)


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


def fetch_open():
    return json.loads(run("gh", "issue", "list", "--state", "open", "--limit", "500", "--json", "number,title,labels,body"))


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
    known = build_known_issues(fetch_open())
    for k in known:
        print(f"  #{k['number']:<4} known issue {k['text']}")
    if known:
        print()
    entry = render_entry(version, entries, date.today().isoformat(), known)
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
    try:
        repo_url = run("gh", "repo", "view", "--json", "url", "--jq", ".url")
    except (subprocess.CalledProcessError, FileNotFoundError):
        repo_url = None
    print()
    print(next_steps(version, repo_url, find_package_id(root), workflow=bool(os.environ.get("GITHUB_ACTIONS")), dry_run=args.dry_run))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"version={version}\nbump={bump}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
