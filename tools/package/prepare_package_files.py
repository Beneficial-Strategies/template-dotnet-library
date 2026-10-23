#!/usr/bin/env python3
"""Writes the two files that go into the package, into artifacts/package/:

  README.md        README.md of the repository up to the line '<!-- end of package readme -->', without the snippet markers,
                   with the links to this repository's main branch pinned to the tag of the version
  release-notes.txt  the entry of CHANGELOG.md for the version, as plain text

and fails if the packed README would not render on nuget.org: a relative link or image, an image from a domain nuget.org
does not allow, raw HTML, or text still in {{braces}}.

  python3 tools/package/prepare_package_files.py --version 1.0.0-alpha
  python3 tools/package/prepare_package_files.py --check          (the version of Directory.Build.props; for CI)
"""
import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent.parent
END_MARKER = "<!-- end of package readme -->"
# https://learn.microsoft.com/nuget/nuget-org/package-readme-on-nuget-org (read 2026-10-22)
IMAGE_HOSTS = {
    "api.codacy.com", "api.codeclimate.com", "api.dependabot.com", "api.reuse.software", "api.travis-ci.com", "app.codacy.com",
    "app.deepsource.com", "avatars.githubusercontent.com", "badgen.net", "badges.gitter.im", "camo.githubusercontent.com",
    "caniuse.bitsofco.de", "cdn.jsdelivr.net", "cdn.syncfusion.com", "ci.appveyor.com", "circleci.com", "cloudback.it",
    "codecov.io", "codefactor.io", "coveralls.io", "dev.azure.com", "devpod.sh", "flat.badgen.net", "gitlab.com", "i.imgur.com",
    "img.shields.io", "infragistics.com", "isitmaintained.com", "media.githubusercontent.com", "opencollective.com",
    "raw.github.com", "raw.githubusercontent.com", "snyk.io", "sonarcloud.io", "travis-ci.com", "travis-ci.org",
    "user-images.githubusercontent.com",
}


def repository():
    """owner/name of the repository, from RepositoryUrl in Directory.Build.props."""
    url = re.search(r"<RepositoryUrl>https://github.com/([^<]+)</RepositoryUrl>", (ROOT / "Directory.Build.props").read_text())[1]
    return url.removesuffix(".git")


def package_readme(text, version, repository=None):
    """The packed part of the README, pinned to the tag of the version."""
    if END_MARKER not in text:
        raise SystemExit(f"README.md has no line {END_MARKER}")
    packed = text.split(END_MARKER, 1)[0]
    packed = re.sub(r"<!-- template-notice -->.*?<!-- /template-notice -->\n*", "", packed, flags=re.S)   # only in the template itself
    packed = re.sub(r"^<!-- /?snippet[^\n]*-->\n", "", packed, flags=re.MULTILINE)
    tag = f"v{version}"
    repository = repository or globals()["repository"]()
    packed = packed.replace(f"raw.githubusercontent.com/{repository}/main/", f"raw.githubusercontent.com/{repository}/{tag}/")
    packed = packed.replace(f"github.com/{repository}/tree/main/", f"github.com/{repository}/tree/{tag}/")
    packed = packed.replace(f"github.com/{repository}/blob/main/", f"github.com/{repository}/blob/{tag}/")
    return packed.rstrip("\n") + "\n"


def problems(packed):
    """What nuget.org would not render. Code blocks are not read."""
    found = []
    prose = re.sub(r"```.*?```", "", packed, flags=re.S)
    prose = re.sub(r"`[^`\n]*`", "", prose)
    for m in re.finditer(r"(!?)\[[^\]]*\]\(([^)\s]+)[^)]*\)", prose):
        image, target = m.group(1) == "!", m.group(2)
        url = urlparse(target)
        if url.scheme not in ("http", "https") and not target.startswith("#"):
            found.append(f"relative link or image: {target}")
        elif image and url.hostname not in IMAGE_HOSTS:
            found.append(f"image from a domain nuget.org does not allow: {target}")
    for m in re.finditer(r"</?[A-Za-z][^>]*>", prose):
        found.append(f"raw HTML: {m.group(0)}")
    if "{{" in prose:
        found.append("text in {{braces}} left in the README")
    if "/main/" in prose or "/tree/main" in prose or "/blob/main" in prose:
        found.append("a link to the main branch is not pinned to the tag")
    return found


def changelog_entry(changelog, version):
    """The entry of the version as plain text: its lines without the heading."""
    m = re.search(rf"^## {re.escape(version)}\b[^\n]*\n(.*?)(?=^## |\Z)", changelog, re.S | re.M)
    if not m:
        raise SystemExit(f"CHANGELOG.md has no entry for {version}")
    body = m.group(1).strip("\n")
    return re.sub(r"^\* ", "", body, flags=re.M).strip() + "\n"


def version_of_props():
    return re.search(r"<Version>([^<]+)</Version>", (ROOT / "Directory.Build.props").read_text())[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version")
    ap.add_argument("--check", action="store_true", help="use the version of Directory.Build.props and write nothing")
    args = ap.parse_args()
    version = args.version or version_of_props()

    packed = package_readme((ROOT / "README.md").read_text(encoding="utf-8"), version)
    found = problems(packed)
    notes = changelog_entry((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    if found:
        print("The packed README would not render on nuget.org:")
        for f in found:
            print(f"  {f}")
        return 1
    if args.check:
        print(f"The README and the changelog entry of {version} are ready to pack")
        return 0
    out = ROOT / "artifacts" / "package"
    out.mkdir(parents=True, exist_ok=True)
    (out / "README.md").write_text(packed, encoding="utf-8", newline="\n")
    (out / "release-notes.txt").write_text(notes, encoding="utf-8", newline="\n")
    print(f"Wrote {out / 'README.md'} and {out / 'release-notes.txt'} for {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
