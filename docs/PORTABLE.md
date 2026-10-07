# Portable apps

Run `customchat export path/to/app.yaml my-app.zip`, or choose **Download app ZIP** in Configuration. The CLI never overwrites an existing file. Extract the ZIP into a new empty directory, then run:

```
customchat validate app.yaml
customchat run app.yaml
```

The bundle contains app.yaml, supported local source documents (.md/.txt/.json/.csv/.pdf), saved theme and stage prompts, and a manifest with hashes and required environment-variable names. Local source paths become relative paths under assets/. Storage becomes a new local SQLite database and the host becomes loopback. Logos stay in the validated theme as embedded PNG data.

The Configuration export captures the running app's applied model/retrieval settings and enabled sources. The CLI captures the YAML plus saved theme/prompts, not unsaved or runtime-only settings. Remote source URLs, background images and fonts remain remote references. Python connector modules, optional PDF/OCR tools and semantic model directories must be installed separately. Local semantic model paths are references, not copied model files.

No .env, stored keys, database, accounts, conversations, uploaded personal documents, cache or saved-look collection is copied. Inline credential fields and credential-bearing URLs stop the export. Source symlinks, private-looking filenames and files in the app's state folder also stop it. Local assets have a 64 MB limit.

**Review local documents before sharing.** This is an app export, not an automatic content sanitizer: private text inside an ordinary source document, prompt or branded text can still be included. It does not upload or publish anything. Environment-variable names are listed in manifest.json; enter their values separately on the destination computer.

With configuration locked, the export endpoint is unavailable. Otherwise it uses the same owner/admin permissions as configuration editing.
