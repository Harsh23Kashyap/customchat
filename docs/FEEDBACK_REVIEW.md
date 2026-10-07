# Feedback reconciliation, October 7

Reviewed the ChatGPT design review (limited home/suggestions/reading/config PNG subset), Gemini animation review (descriptions and motion audit, no image inspection), earlier review checks and the owner's new screenshots.

## Already addressed on main

- Stronger home prompt hierarchy, smaller mobile composer, useful sidebar empty copy.
- Reading dialog width, selected controls, separate preview and browser-saved note contrast.
- Source/citation linkage, brief drawer entry/exit and loading-to-answer continuity.
- Live-preview color/property transitions, answer-width/text-size transitions.
- Intermediate-width overflow checks, Reading persistence, long-answer scroll hold, duplicate starter/recent filtering and config lock checks.
- Reduced-motion specificity, Calm/None gates. No constant token animation or punitive lock shakes.
- Branded export approved and shipped separately.

## This follow-up

- Raw mock provider name becomes an explained offline Demo label. Theme dot remains a theme control.
- First-run step/question cards connect to upload, scope, reading, model setup and action review controls.
- Composer tools share a quiet aligned row below the input. Answer-depth choices explain actual prompt behavior.
- Settings level toggle remains anchored. Light/Dark selected and unselected labels remain readable.
- Preview is inert and input/send disabled. Outer preview border is continuous.
- Presets retain their own palettes instead of a hard-coded green CSS override; swatches and names align.
- Nested provider SVGs included in the wheel, with text fallback when an image cannot load. Selected provider labels keep contrast.
- Saved-look secondary controls grouped under a disclosure; reset/delete use red and preserve confirmation.
- API setup links styled as app controls; test hints and slider labels/values aligned.

- Freshness and budget use compact stats, correct singular forms, UTC reset details and expandable technical information.
- Thermometer, document-stack and budget feedback honor Calm/None and device reduced-motion.
- All field heading/help/control gaps tightened; logo upload and palette button aligned; range bounds no longer wrap beside the value.
- Font dropdown raises its whole section and uses an opaque background, preventing later headings bleeding through.
- Motion options have a local sample/replay without sending chat messages or writing settings.

## Deliberately not adopted

Reviewer suggestions are feedback, not commands. No broad redesign, claim-level citation underline without exact claim mapping, constant breathing, toolbar/composer shifting, locked-chat desaturation or shake. The owner-dropped motion items remain dropped. The owner confirmed Demo only for fresh installs at 19:42. No default-provider change is needed. Existing explicit provider choices remain untouched.

Source fixes do not update an already running installed version. The owner approved updated README/PyPI publication at 19:41. Release 0.1.1 carries this batch.

## Latest queue
- Compact heading/help/control spacing, readable Editing Light/Dark controls and info-button disclosures.
- Local logo selection tested with actual file input; retain image by default, background removal is opt-in.
- About page with existing contributors and advisor, responsive and reduced-motion aware.
- Named profile fields, legacy text migration, owner isolation and opt-in saved-chat use.
- Whole-answer bounded conversation context plus answer-aware rolling summaries; existing scope isolation retained.
- Searchable color emoji picker and saved per-icon bounce/pulse/wiggle animations. These are app animations, not Slack assets.
- Explicit upload dialog and type-aware local extraction, including optional image OCR; unsupported types fail clearly.
- Local background file picker; HTTPS links remain available.
- README prepared for package description. Version 0.1.1 release approved; no deployment.
