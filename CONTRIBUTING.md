# Contributing

Thank you for looking. This package is free (MIT) and is kept current by a small team. A bug report, a failing test, a fix or a question are all welcome.

## Reporting a bug

Use the **Bug** form. The fastest fix starts from a **unit test that fails today**: add it in a branch or a pull request and link it in the issue. The pull request that fixes the bug makes that test pass and says `Closes #<the issue>`.

## Pull requests

- Every pull request is linked to an issue: write `Closes #123` (or `Refs #123` for a tracking issue) in the description. A check enforces it; a typo or generated file can take the `no-issue` label from a maintainer.
- A bug fix includes a test that failed before the fix, named in the pull request.
- Add a `Release note:` line if the issue title would not tell a consumer what changed. It goes into the changelog and the NuGet release notes.
- The build treats warnings as errors and every target framework is built and tested. Before you push:

  ```
  dotnet build -c Release
  dotnet test -c Release --no-build
  tools/run-examples.sh              # builds and runs every example against the packed package
  python3 tools/sync-readme.py       # fills the README's code blocks from the examples
  ```

- The code in the README is taken from the examples (`// <snippet name>` regions); change the example, not the README block.

## Versions and releases

A version has three parts, `design.breaking.compatible`. It is written like a Semantic Versioning number but is **not** one: the first part changes with a redesign, the second with a change that breaks existing users, the third with every other change. The labels on closed issues choose it (`redesign`, `breaking-change`, anything else), and the same issues write the entry of `CHANGELOG.md`.

Three labels say what a change does to the data a package accepts and writes, so the version follows without anyone having to remember it: `tightens` (the type refuses input it used to accept: a wrong check digit, a stricter pattern), `changes-output` (the same value is written differently) and `loosens` (the type accepts input it used to refuse). The first two count as breaking. `loosens` is compatible for people who read messages, but add `breaking-change` too if code downstream relies on the old limit (a validator that assumes the pattern, a sample generator). When in doubt about a change to a type, label it; a maintainer can remove the label.

The entry also ends with the **known issues**: the issues still open when the version is released, one `Known issue:` line each, so a consumer sees what is not done yet. A `Known issue:` line in the issue (like `Release note:`) replaces the title. Issues labelled `enhancement`, `documentation`, `tech-debt`, `ci`, `release`, `question`, `needs-triage` or `no-release-notes` are left out.

A release is two steps. The **Prepare release** workflow (dry run first) pushes a `release/vX.Y.Z` branch with the version and the changelog entry, and a pull request is opened. After it is merged, a maintainer tags the merge commit `vX.Y.Z`; the **Publish to NuGet** workflow does the rest. Publishing cannot be taken back, so the tag is deliberate.
