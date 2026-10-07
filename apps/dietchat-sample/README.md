# DietChat public-content sample

Run from this folder:

```sh
customchat-app run app.yaml
```

Or from the repository root:

```sh
python -m customchat run apps/dietchat-sample/app.yaml
```

Starts at http://127.0.0.1:8080 with no credentials. Demo is an offline response provider, not real AI or DietChat production output. All non-secret settings are filled. Starter questions match the public DietChat page. The four local documents contain public website text captured October 8, 2026, not research papers. The live site exposes no paper library to import.

Try "What does DietChat do?" to test local-document retrieval. The nutrition starter questions exercise the UI but this content does not support medical answers.

For real generation, choose a provider/model and supply your own key in Configuration. PubMed is not enabled automatically; it requires live internet. No keys, passwords, account records or private chats were copied. Production prompts and backend behavior are not available from the public site. This sample does not change an existing workspace or reset an account password.

Public sources:
- https://dietchat.org
- https://dietchat.org/about.html
- https://dietchat.org/contact.html
- https://dietchat.org/addons.html

## Prompts and generated source code

In Configuration, open Advanced, then Prompts, to inspect the prompt stages and their response formats. The Code helpers section contains the custom source-code generator. This offline sample fills the app answer prompt in app.yaml; it does not claim to contain the live DietChat backend prompts. Fill your own provider key to run AI-based prompt tests or code generation.
