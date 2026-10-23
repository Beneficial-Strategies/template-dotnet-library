<!-- template-notice -->
> **This is the template for a published .NET package** of the Beneficial Strategies family. It is a working skeleton, and what you read below is the README skeleton of the package it makes. To make a package: create a repository from this template (the green button), then in it run
> `python3 .template/instantiate.py --repo <name> --package-id <PackageId> --description "<one sentence>."`
> and follow what it prints. What it replaces is in [`.template/placeholders.md`](.template/placeholders.md).
<!-- /template-notice -->

![Beneficial Strategies](https://raw.githubusercontent.com/Beneficial-Strategies/iso-20022-example/main/.beneficial/logo.png)

# BeneficialStrategies.Iso20022.Example

TEMPLATE_DESCRIPTION

## Install

```
dotnet add package BeneficialStrategies.Iso20022.Example --prerelease
```

The package is in alpha, so the command asks for a prerelease version.

## How to use

### Say hello

<!-- snippet: examples/01-hello/Program.cs#hello -->
```csharp
using BeneficialStrategies.Iso20022;

Console.WriteLine(Greeting.For("Acme Corp"));      // Hello, Acme Corp.
```
<!-- /snippet -->

Try the [project](https://github.com/Beneficial-Strategies/iso-20022-example/tree/main/examples/01-hello) yourself.

## More

* Documentation, release notes and issues: https://github.com/Beneficial-Strategies/iso-20022-example
* License: MIT. Status: alpha.

<!-- end of package readme -->

## Building and contributing

```
dotnet build -c Release
dotnet test -c Release --no-build
tools/run-examples.sh              # packs the package, then builds and runs every example against it
python3 tools/sync-readme.py       # fills the code blocks above from the examples
```

A bug report or a change starts with an issue; a bug fix names the test that failed before it. See CONTRIBUTING.md.
