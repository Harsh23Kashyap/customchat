# Source scope

The Source scope button beside the composer selects one configured collection or one local document. The colored chip says what the next question is locked to, and Clear removes the lock. Answer metadata retains the selected scope after chat reload; Shorter/Deeper regeneration keeps that scope.

Local document filtering happens before top-k selection, semantic fusion and reranking. Scope is part of the query cache key. Unknown/missing document choices fail closed. Scoped questions do not include personal uploads or prior chat summaries/answers, which could otherwise reintroduce facts from other documents. Follow-up wording also loses old chat context under a lock; phrase the subject explicitly.

An explicit collection selection excludes automatic personal-upload retrieval. An empty explicit source list means no sources, rather than silently searching all. Scope labels are not access-control rules. Configured sources and their local document filenames remain visible to every authenticated app visitor. Permission-aware documents are a separate pending feature; do not host private team sources on a shared app until that is configured and verified.

This slice locks collection or local document, not a historical version hash. The latest indexed version is used. Current UI scope remains for subsequent questions until cleared and is not restored as a global preference after reload. Optional semantic paths apply the same document filter but real model quality is not benchmarked. No remote document browsing/scope is implemented.

Update: permission-aware source rules are now available in PERMISSIONS.md. The scope picker filters choices through them. Sources without rules remain shared by default; a scope selection itself never grants access.
