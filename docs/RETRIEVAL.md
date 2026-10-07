# Optional document retrieval

Offline BM25 remains the default. Markdown citations now retain the section; PDF citations retain the page, file name and content-version hash. The source drawer shows these anchors beside the extracted text. Saved answers keep their original metadata, not the latest document's identity. Local sections from the same document are no longer discarded just because they share a title.

## PDFs and local OCR

Install `pip install 'customchat[documents]'` for pypdf page extraction. Add PDFs to a local source folder. Text PDFs need no OCR. For image-only pages, explicitly set `ocr: true` on the source and install Poppler's pdftoppm and Tesseract locally. OCR never uploads a file or calls a model/API. Missing dependencies cause the local source to fail closed with a status error, not a fake successful scan. Limits: 8 MB per PDF, 100 pages, 30 seconds per render/OCR subprocess. OCR can misread words and numbers: citation metadata labels OCR text so readers check the original.

## Optional hybrid and reranking

Install `pip install 'customchat[semantic]'`. Supply an already-installed local SentenceTransformer directory and, optionally, a CrossEncoder directory:

```
sources:
  - type: local_files
    id: docs
    path: docs
    semantic_model: /absolute/path/to/local-embedding-model
    rerank_model: /absolute/path/to/local-cross-encoder
```

Keyword and cosine rankings are combined with reciprocal rank fusion. The optional cross encoder reranks at most 30 candidates. Embeddings refresh when the content version changes. Models load locally with remote code disabled and local-files-only loading; CustomChat does not download them. Model names/URLs are not accepted. Model folders are not included in portable exports.

No optional model means no embedding calls or new dependency in the BM25 path. These are retrieval options, not a promise of better answers on every corpus. The ranking integration has deterministic injected-model tests; a real installed semantic model has not been benchmarked in this release. OCR has been checked with a generated image-only PDF, not every language/layout. Page anchors require pypdf rather than the fallback unpaged upload extractor.
