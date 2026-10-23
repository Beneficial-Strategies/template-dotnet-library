# What `instantiate.py` replaces

| In the template | Becomes | Where it is |
|---|---|---|
| `iso-20022-example` | the repository name (`--repo`) | README links, `Directory.Build.props` (`RepositoryUrl`), the solution file name |
| `iso-20022/iso-20022-example` | the workspace path (`--workspace-path`, default `iso-20022/<repo>`) | `.beneficial/workspace/developer.json`, `owner.json` |
| `BeneficialStrategies.Iso20022.Example` | the package id (`--package-id`) | the project files and their names, `examples/Directory.Build.props`, the README, CLAUDE.md |
| `ExamplePackage` | the folder name under `src/` and `tests/` (`--short`) | the folders, the solution, the project references |
| `TEMPLATE_DESCRIPTION` | the one-sentence description (`--description`) | the README, `PackageDescription`, CLAUDE.md |
| `YYYY-MM-DD` | today | the first entry of `CHANGELOG.md` |
| `YYYY` | this year | `LICENSE` |

`.template/` and `.github/workflows/template-check.yml` are deleted by the script.

## Not replaced, to do by hand
* The placeholder type `Greeting`, its tests and `examples/01-hello`: replace them with the real package.
* The target frameworks: the template has net8.0 and net10.0 (the two newest .NET LTS releases). Add `netstandard2.0` only on purpose, with its Windows test job.
* The repository's About text, the labels and the repository variable `NUGET_USER`, and the trusted publishing policy on nuget.org, which the package owner creates for the repository and `publish.yml`.
