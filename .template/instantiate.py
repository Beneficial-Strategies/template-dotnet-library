#!/usr/bin/env python3
"""Turns this template into a package repository: replaces the placeholders, renames what is named after them, and removes
the template's own files. Run it once, in the new repository, before anything else.

  python3 .template/instantiate.py --repo iso-20022-messages --package-id BeneficialStrategies.Iso20022.Messages \\
      --description "One sentence that says what the package is and does."

  --repo            the repository name, as registered (STD-NAM-REPO), lowercase with hyphens
  --package-id      the package id and assembly name: BeneficialStrategies. and the repository name in PascalCase
  --description     one sentence; it becomes the first line of the README, the package description and the repository About text
  --workspace-path  where the repository is cloned in a workspace (default iso-20022/<repo>)
  --short           the folder name of the package under src/ (default: the package id without BeneficialStrategies.Iso20022.)

What it replaces is listed in .template/placeholders.md.
"""
import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "bin", "obj", "artifacts", ".template"}
TEXT_SUFFIXES_SKIPPED = {".png", ".jpg", ".ico", ".nupkg", ".dll"}

TOKEN_REPO = "iso-20022-example"
TOKEN_PATH = "iso-20022/iso-20022-example"
TOKEN_PACKAGE = "BeneficialStrategies.Iso20022.Example"
TOKEN_SHORT = "ExamplePackage"
TOKEN_DESCRIPTION = "TEMPLATE_DESCRIPTION"


def files():
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        if path.is_file() and not (set(rel.parts) & SKIP_DIRS) and path.suffix.lower() not in TEXT_SUFFIXES_SKIPPED:
            yield path


def replace_text(replacements):
    for path in files():
        try:
            with open(path, encoding="utf-8", newline="") as f:
                text = f.read()
        except UnicodeDecodeError:
            continue
        new = text
        for old, value in replacements:
            new = new.replace(old, value)
        if new != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(new)


def rename_paths(renames):
    """Deepest paths first, so a renamed folder does not hide what is inside it."""
    paths = sorted((p for p in ROOT.rglob("*") if not (set(p.relative_to(ROOT).parts) & SKIP_DIRS)),
                   key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        name = path.name
        for old, value in renames:
            name = name.replace(old, value)
        if name != path.name:
            path.rename(path.with_name(name))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--package-id", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--workspace-path")
    ap.add_argument("--short")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.repo):
        sys.exit("--repo: lowercase letters, digits and hyphens only")
    if not re.fullmatch(r"BeneficialStrategies(\.[A-Z][A-Za-z0-9]*)+", args.package_id):
        sys.exit("--package-id: BeneficialStrategies. followed by PascalCase names separated by dots")
    if not args.description.strip().endswith("."):
        sys.exit("--description: one sentence that ends with a full stop")
    path = args.workspace_path or f"iso-20022/{args.repo}"
    short = args.short or args.package_id.removeprefix("BeneficialStrategies.Iso20022.")
    if not re.fullmatch(r"[A-Za-z0-9.]+", short):
        sys.exit("--short: letters, digits and dots only")
    if (ROOT / ".template").exists() is False:
        sys.exit("This is not a template checkout: .template/ is missing (already instantiated?).")

    # the longest tokens first, so that none is replaced inside another
    replace_text([
        (TOKEN_PATH, path),
        (TOKEN_PACKAGE, args.package_id),
        (TOKEN_REPO, args.repo),
        (TOKEN_SHORT, short),
        (TOKEN_DESCRIPTION, args.description.strip()),
        ("YYYY-MM-DD", date.today().isoformat()),
        ("YYYY", str(date.today().year)),
    ])
    readme = ROOT / "README.md"
    readme.write_text(re.sub(r"<!-- template-notice -->.*?<!-- /template-notice -->\n\n", "", readme.read_text(encoding="utf-8"), flags=re.S), encoding="utf-8", newline="\n")
    rename_paths([(TOKEN_PACKAGE, args.package_id), (TOKEN_REPO, args.repo), (TOKEN_SHORT, short)])

    shutil.rmtree(ROOT / ".template")
    workflow = ROOT / ".github" / "workflows" / "template-check.yml"
    if workflow.exists():
        workflow.unlink()

    print(f"""Instantiated {args.repo} ({args.package_id}).

Next:
  1. Replace src/{short}/Greeting.cs, its test and examples/01-hello with the real package, its tests and its first example.
  2. Set the repository's About text to the description; run tools/labels.sh to create the labels; set the repository variable NUGET_USER.
  3. python3 tools/sync-readme.py, then dotnet build -c Release, dotnet test -c Release --no-build and tools/run-examples.sh.
  4. Before the first release, the package owner creates the trusted publishing policy on nuget.org for this repository and publish.yml.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
