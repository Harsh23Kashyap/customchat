# Prompts

Configuration > Prompts is visible in both Simple and Advanced. All unedited stages inherit CustomChat 0.1.6 defaults; all prompt.system/style fields are explicitly filled in each YAML. Code helpers is separate.

| Stage | Default state | Purpose / format |
|---|---|---|
| Question check | Off | If enabled, VALID or INVALID plus reason. Optional local model call. |
| Follow-up rewrite | On | Rewrites a contextual follow-up as a standalone question. Returns only question. |
| Search queries | On stage; query_rewrite false | Default keyword extraction, not model multi-query rewriting. Adapter removes plain-language filler. |
| Relevance filter | Off | If enabled, returns matching passage numbers or NONE. |
| Answer | On | News-specific system prompt from YAML. Only evidence-backed claims, [n] citations, dates/publishers, conflict handling, no breaking-news claim. |
| Support check | Off | If enabled, OK or UNSUPPORTED with reason. |
| Revise against sources | Off | Optional extra model call; off in this sample. |
| Follow-up suggestions | On | Three short related questions. |
| Conversation summary | On | Two-sentence topic summary for bounded history. |

Quick is 2-4 sentences; Standard adds agreements/conflicts; Deep adds sections and missing context. Every style asks for dates and citations. The YAML answer_note warns about incomplete/delayed news. Citation ledger records claim links; it is not an independent fact-check.

You can inspect and save each stage in Configuration > Prompts. User edits persist beside the database and override inherited text. "Use default" removes that stage's override. "Write it with AI" in Demo returns a template; with local Ollama it uses your model. Code helpers generates reviewed Python but does not replace this bundle's adapter automatically. Do not paste keys in descriptions or prompts.
