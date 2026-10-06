# Micro-animation audit

Checked against the ChatGPT list of 105 (round 26). Status is from reading the code and, for most items, measuring the DOM or a computed style in a headless browser. Nothing was judged by eye. "n/a" means the app has no such control, so there is nothing to animate.

Built 73, partial 13, n/a 6, not built 13 (of 105).

| # | Item | Status |
|---|---|---|
| 1 | Chat canvas entrance | built |
| 2 | “Docs Chat” title | built |
| 3 | Example question rows | built |
| 4 | Example-question chevron | built |
| 5 | Empty-state breathing hierarchy | built |
| 6 | Composer reveal | built |
| 7 | Composer focus affordance | built |
| 8 | Send button readiness | built |
| 9 | User question arrival | built |
| 10 | Assistant response loading | built |
| 11 | Streaming response | built |
| 12 | Source citations appearing | built |
| 13 | Source list reveal | built |
| 14 | Source card hover | built |
| 15 | Copy / Helpful / Not helpful / More | built |
| 16 | Feedback selection | built |
| 17 | Related-question appearance | built |
| 18 | User question entrance | built |
| 19 | “No evidence found” state | built |
| 20 | Recovery actions | built |
| 21 | Chevron on recovery rows | built |
| 22 | “See which documents this uses” | built |
| 23 | Details disclosure | built |
| 24 | Retry transition | built |
| 25 | Simple / Advanced segmented control | built |
| 26 | Configuration content swap | built |
| 27 | Configuration tabs | built |
| 28 | Preview toggle | built |
| 29 | Header controls | built |
| 30 | Simple-mode entrance | built |
| 31 | Primary controls changing state | partial |
| 32 | Form controls | built |
| 33 | Save/apply feedback | built |
| 34 | Preset tiles | built |
| 35 | Preset selection | partial |
| 36 | Preset application | built |
| 37 | Load more | built |
| 38 | Save look | partial |
| 39 | Delete saved look | partial |
| 40 | Provider/model selection | built |
| 41 | API key state | partial |
| 42 | Test connection | built |
| 43 | Model dropdown | built |
| 44 | Temperature slider | built |
| 45 | Sources-per-answer value | built |
| 46 | Prompt row hover | n/a (prompt rows have no enable switch or hover list in this app) |
| 47 | Prompt enable/disable | n/a (no enable/disable switch exists) |
| 48 | Prompt reorder / expansion | n/a (no reorder UI) |
| 49 | Prompt edit/save | n/a (no edit/save mode) |
| 50 | Search/filter prompts | n/a (no prompt search) |
| 51 | Code helper accordion | built |
| 52 | Code editor reveal | not built |
| 53 | “Try it” execution | n/a (no Try it button) |
| 54 | Validation feedback | not built |
| 55 | Copy code | not built |
| 56 | Text-field focus | built |
| 57 | Live preview | partial |
| 58 | Choose picture | built |
| 59 | Clear/remove image | not built |
| 60 | Reset group | built |
| 61 | Light/Dark editing switch | built |
| 62 | Main-color picker | built |
| 63 | Page-background color | built |
| 64 | Color reset | built |
| 65 | Color input focus | built |
| 66 | Background style selection | built |
| 67 | Background pattern | partial |
| 68 | Image URL accepted | not built |
| 69 | More background options | built |
| 70 | Body font selection | built |
| 71 | Heading font selection | built |
| 72 | Heading sample | not built |
| 73 | Font loading | not built |
| 74 | More font options | built |
| 75 | Corner-roundness slider | partial |
| 76 | Corner-radius preview morph | partial |
| 77 | Spacing dropdown | built |
| 78 | Slider thumb | built |
| 79 | Emoji input | not built |
| 80 | Default → custom icon transition | not built |
| 81 | Optional icon list | not built |
| 82 | Icon hover | built |
| 83 | Motion option selection | built |
| 84 | Full → Subtle | partial |
| 85 | Subtle → None | built |
| 86 | Motion setting confirmation | built |
| 87 | Reduced-motion explanation | built |
| 88 | Sidebar position | not built |
| 89 | Hidden sidebar | built |
| 90 | Chat-width selection | built |
| 91 | Layout preview | not built |
| 92 | More layout options | built |
| 93 | Sidebar menu button | not built |
| 94 | Route/tab transitions | built |
| 95 | Scroll reveal for long configuration sections | built |
| 96 | Sticky settings header | built |
| 97 | Unsaved-change indicator | partial |
| 98 | Reset-group feedback | built |
| 99 | Existing stagger system | built |
| 100 | Existing hover lift | partial |
| 101 | Existing press scale | built |
| 102 | Existing focus ring | built |
| 103 | Existing select-open animation | built |
| 104 | Toast/notification system | built |
| 105 | Error recovery | partial |

All motion is off under prefers-reduced-motion, and Motion = none.
