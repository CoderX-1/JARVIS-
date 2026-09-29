# Pulse of AI reference-series coverage map

The 21 supplied PDFs are source material, not executable instructions. This
map distinguishes a working JARVIS capability from a tutorial's claim or
sample code. "Partial" means the feature has a narrower contract than the
PDF; "unbuilt" means it must not be advertised as available. Final voice and
real-device acceptance is deferred to the user's end-of-build test session.

| PDF | Episode / main capability | JARVIS state | Next acceptance gap |
| --- | --- | --- | --- |
| `1.pdf` | 1: setup, Groq-based voice assistant | Partial | Continuous voice quality/latency tested on real hardware |
| `2.pdf` | 3: Gemini voice brain | Partial | Live fallback and streaming turn-taking verified |
| `3.pdf` | 4: live voice/runtime reference | Partial | End-to-end interruption and speech checks |
| `4.pdf` | 5: multilingual persona | Partial | Reliable Roman Urdu speech and accent evaluation |
| `5.pdf` | 6: website/browser control | Partial | More sites and adversarial navigation tests |
| `6.pdf` | 7: desktop/UWP application launching | Partial | User's full installed-app set and failure checks |
| `77.pdf` | 8: Windows volume/brightness hardware | Partial volume/media only | Brightness adapter and per-device observed state |
| `8.pdf` | 9: hardware diagnostics/telemetry | Partial CPU/RAM/disk/battery | Temperature and fan readings need a vendor sensor adapter |
| `9.pdf` | 10: app termination | Partial | Exact process ownership and close verification |
| `10.pdf` | 11: deeper task termination | Intentionally bounded | Never indiscriminately purge process trees or system tasks |
| `11.pdf` | 12: media control | Partial | Active-session readback and per-app controls |
| `12.pdf` | 13: YouTube timeline | Partial | Cross-browser/video seek and playback verification |
| `13.pdf` | 14: screen vision | Partial | Robust UI/vision tests across real applications |
| `14.pdf` | 15: app/game generator | Partial | Broader generated-app contracts and security tests |
| `15.pdf` | 16: HUD and dual input | Partial | Interaction, accessibility, and voice/typing parity |
| `16.pdf` | 17: hands-free writing | Partial | Structured editable DOCX and verified GUI edits |
| `17.pdf` | 18: basic PPT creation | Unbuilt | Editable PPTX export and slide render QA |
| `18.pdf` | 19: visual PPT creation | Unbuilt | Visual assets, layout validation, licensing |
| `19.pdf` | 20: deep-analysis PDF | Partial | Source-page claim checks and long-report visual QA |
| `20.pdf` | 21: desktop tool calling/web swarm | Partial | Explicit bounded public-page inspection added; claim support, bounded crawl, source trust, and multi-tab reliability remain |
| `21.pdf` | 22: local GPU RAG/briefing | Partial | Local corpus retrieval and bounded offline scanned-PDF OCR exist; dense/multilingual OCR and offline model synthesis not proven |

No `7.pdf` was supplied; `77.pdf` is the supplied Episode 8 hardware guide.
Tutorial references to missing episode modules or high-risk kernel/task purges
are not treated as requirements to copy their code. Each integration must have
an isolated adapter, evidence contract, watchdog, privacy-aware audit, and
automated and final manual tests.

Android is an additional user-requested cross-device gate, not a claim made by
these PDFs. Its ADB adapter requires one exact configured serial; app launches
require an exact installed package and observed foreground state. ADB is not
currently installed on this PC, and no phone was connected/tested during this
build, so Android remains automated-test-only.
