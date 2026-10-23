# This repository

TEMPLATE_DESCRIPTION (NuGet package `BeneficialStrategies.Iso20022.Example`). It is public.

## Layout

* `src/ExamplePackage` the package; `tests/ExamplePackage.Tests` its tests.
* `examples/NN-name` console projects that use the packed package, as a consumer does; `expected-output.txt` beside each is what it prints.
* `README.md` is also the package README: it is cut at the line `<!-- end of package readme -->` when packed, and its code blocks are filled from the examples.
* `tools/` the release and package scripts, the license check, `run-examples.sh` and `sync-readme.py`.
* `.beneficial/` workspace metadata and the logo files.

## Working here

* Never commit, push or open a pull request unless asked in that turn. Work on a branch; every pull request is linked to an issue (`Closes #n`).
* Never commit `.claude/`. Generated or derived files go under `artifacts/` (ignored) or a `_work/` folder outside the repository, not into it.
* Build and test before proposing a change: `dotnet build -c Release` (warnings are errors) and `dotnet test -c Release --no-build`; then `tools/run-examples.sh` and `python3 tools/sync-readme.py --check`.
* Every public type and member has an XML documentation comment; the build fails on a missing one.
* The README is public text. Never write in it, in an issue, a pull request, a commit message or a release note the name or the content of anything that is not public.
* The version has three parts, `design.breaking.compatible`, and is not Semantic Versioning (see `CONTRIBUTING.md`). Do not change `<Version>` by hand: the release workflow does.
* Examples: types the consumer writes start with `My` and are in a `MyCompany` namespace; data is plainly fictitious; an example is never renumbered, a new one takes the next number.
