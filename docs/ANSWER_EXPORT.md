# Branded answer exports

The answer More menu has Markdown and PDF downloads. Markdown includes app title/tagline, question, answer and numbered citations with source URL, local filename, page/section, version hash and OCR flag. PDF carries app identity and brand-color rule, the same snapshot, page numbers and multiple pages; long answers are no longer silently cut after 58 lines.

These exports use the answer's saved evidence, not today's source state. Version hashes record the corpus at answer time; a URL can change later. They omit account IDs, chat IDs, profiles, temporary histories, settings, keys and other turns. Question/answer/source content is intentionally included, so review it before sharing. Existing permission gates redact revoked evidence first.

The dependency-free PDF uses a standard Latin-1 font. For unsupported scripts or characters it stops with an error instead of replacing them silently; use Markdown for full Unicode. The PDF preserves citation numbers and plain text but does not embed the app logo or rich Markdown styling. PDFs are a simple portable report, not a copy of the chat UI. Temporary answers have no saved turn ID and cannot use the server download routes in this slice. No file is uploaded or sent automatically.
