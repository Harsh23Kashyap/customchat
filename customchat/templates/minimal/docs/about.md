# What is CustomChat

CustomChat turns one YAML file into a chat application. You describe the sources of evidence, the model provider and the look of the app. The engine retrieves evidence, writes an answer that cites it, and keeps the earlier questions of the conversation in mind.

# Conversation memory

Every question is rewritten into a standalone question using the earlier turns of the same conversation, so a follow-up such as "what about its cost?" still retrieves the right evidence. A rolling summary keeps long conversations short.
