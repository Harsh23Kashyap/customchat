# Question suggestions

The empty chat shows up to four short starter questions. Real providers generate one set from the app title, tagline, configured examples, answer instruction and source labels. The set is stored beside chats and reused after reload/restart. Changing that context or provider selects a new cache version. Demo uses configured examples without a model call. Failure or a model-budget limit falls back to examples, without retrying on every load.

Generation goes through the existing model-call budget. It never receives private uploads, profiles or conversation history. It suggests questions, not verified answers; it does not fetch current sports or health facts. The prompt is bounded and model output is treated as text, filtered for short distinct questions.

Recent-question chips come only from the current authenticated owner's saved, non-deleted chats. In no-auth mode all visitors share the local owner, and token mode shares one owner per app token, as existing chats do; use accounts for separate visitors. They are not published as app-wide examples or fed to the starter model. Temporary chat hides them and does not save its questions. Click a chip to ask it. Existing answer follow-ups remain evidence-based, up to three new questions, filtered against earlier questions.

Limits: cached fallback does not retry automatically when the provider recovers; change the context/provider to regenerate. Suggestion quality has mocked-provider and offline UI coverage, not a paid-model quality benchmark.
