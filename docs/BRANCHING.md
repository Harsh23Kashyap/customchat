# Edit and branch

Choose More > Edit + branch on a saved answer. Edit the question in the prompt. A new chat copies only visible earlier turns from that same chat, with new turn/topic IDs and fresh empty summaries. The old question, its answer and later turns are not copied. The original chat stays unchanged. The edited question is put into the composer for review; you press Send to run it. Creating a branch makes no model call.

The notice links back to the original chat. The branch remains in the chat list. Deleted chats/turns and another account's turns cannot be branched. Feedback is not copied. Source citations are copied with earlier turns, as their original snapshots. Storage writes are committed together.

Temporary chat does not support this saved branch operation, so it cannot accidentally persist private temporary context. Cross-chat topic history is deliberately not copied. Optional MySQL uses the common transaction path but has not been tested against a live MySQL server for this feature.
