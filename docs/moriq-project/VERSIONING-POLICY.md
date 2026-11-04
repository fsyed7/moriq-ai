# Versioning policy
Keep existing Brain 0.1.0 and historical task numbering intact. Use task checkpoint labels for unreleased engineering work; no migration release/tag is created. A future accepted public API can use semantic versioning after its compatibility policy is agreed. Breaking contract schemas need explicit version negotiation and denial tests; never silently reinterpret version=1.

Maintain MORIQ-CHANGELOG.md separately from inherited CHANGELOG.md. Record date, component, user-visible behavior, exact reviewed commit, test evidence and known limitations. A local file or branch is not a published release.
