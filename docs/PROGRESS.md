# Live progress and calmer reading

Streaming sends real progress events before context preparation, source checks, passage selection, writing, citation checks, saving and related questions. Labels describe the stage being attempted, not a promise that it succeeded. No matching evidence says so. While waiting for the first server event the UI says "Waiting for the app". It never invents percentages or completed work.

Progress is a short screen-reader live region outside the answer text. Existing Stop and retry controls remain; interrupted questions stay in the composer. Stop closes the browser request, but a provider operation already running on the server may still finish or cost a model call. Server-side cancellation is not implemented.

Scrolling up during a stream holds the reading offset. Reduced-motion settings suppress token and starter entrance animations. Existing app motion options Full/Subtle/None remain available in Configuration; this slice does not add a new named Calm preset or claim a full accessibility audit.

NDJSON clients should accept progress events before meta, tokens and done, ignoring unknown event kinds. Validation still precedes the first event. Tests cover stage ordering, real HTTP error status and delayed UI source-failure/retry behavior without paid models.
