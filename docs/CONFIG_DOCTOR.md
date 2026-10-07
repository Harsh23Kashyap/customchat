# YAML doctor

`customchat config-doctor app.yaml` checks the file offline, with line/column, key and a suggested fix. It catches syntax, duplicate keys, typos in standard blocks, wrong types, enum/range errors and existing semantic validation errors. Exit status is 1 for errors. It does not run a source connector, call a model, load `.env`, fix the file or send its contents anywhere.

`customchat doctor app.yaml` remains the separate live provider/source readiness check. Config doctor is not a launch certification.

## Editor autocomplete

Generate the schema beside your app:

```sh
customchat config-schema > customchat.schema.json
```

With a YAML editor supporting JSON Schema, associate that local file with app.yaml. For example, in VS Code with the Red Hat YAML extension, add `.vscode/settings.json`:

```json
{"yaml.schemas": {"./customchat.schema.json": "app.yaml"}}
```

This supplies key completion, choices and basic type/range checks. Run config-doctor for semantic checks such as a required provider model. The schema is generated from the shipped defaults and source options. Source-specific extension keys remain permitted for custom connectors; autocomplete is not a guarantee that arbitrary source options work. There is no custom in-app YAML editor in this slice.

Diagnostics never echo scalar values or syntax excerpts, to avoid exposing accidentally pasted keys. Existing `validate` and runtime behavior are unchanged. Nested keys newly flagged here may have been silently accepted at runtime; review them before replacing your file. The doctor does not rewrite YAML comments or formatting.
