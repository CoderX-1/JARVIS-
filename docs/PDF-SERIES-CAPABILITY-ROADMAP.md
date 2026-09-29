# JARVIS capability build from the Pulse of AI PDF series

The PDFs are reference material, not executable instructions. JARVIS keeps its
existing voice/desktop owner, verified action contracts, provider fallback,
and privacy boundaries. Features are implemented independently, tested, and
promoted one gate at a time; no copied all-in-one `agent.py` is loaded.

## Gate status (2026-09-29)

| Gate | Capability | State | Exit test |
| --- | --- | --- | --- |
| 1 | Local document knowledge | Text indexing live; bounded offline OCR for scanned PDF pages added, final voice/manual acceptance pending | Explicitly index a PDF/DOCX/PPTX/TXT/MD; search a late passage with file and page/slide; stale file withheld; no automatic scan |
| 2 | Evidence-grade web dossiers | Bounded link checks and explicit original-page text inspection live; direct supplied-URL extraction live; factual claim verification pending | Bounded multi-query research, source deduplication, dates where available, claim-level attribution, unsupported claims identified, source links checked |
| 3 | PDF reports | Source-linked draft and direct supplied-URL digest live, with native coverage visual and pre-publication render/text checks; real-research/manual acceptance pending | Research-grounded outline, citations per claim, readable typography, PDF render/inspection, accurate page count, reproducible source manifest |
| 4 | PowerPoint presentations | Editable, source-attributed professional evidence deck generated and package-tested; native visual opening still pending | Content storyboard, editable evidence, licensed/attributed visuals, slide render/inspection, no clipped text, PPTX opens correctly |
| 5 | Document writing | Partial generic typing only | Structured DOCX export and separate verified GUI entry, with no silent edits to existing documents |
| 6 | Hardware, media, and app control | Read-only native PC diagnostics live; other tools partial | Per-device availability, observed after-action state, bounded process targeting, never indiscriminate task purge |
| 7 | Vision, interface, and app creation | Existing partial implementations | Real app tests and recoverable failure paths, including user-interference tests |
| 8 | Reusable workflow learning | Privacy-minimal pattern memory live; semantic generalization pending | Versioned skill manifest, reproducible test, review/promotion, rollback; compare optional Hermes worker before integration |
| 9 | Phone and physical devices | Android ADB adapter live; no real adapter paired | Exact phone identity, installed-app and foreground checks, offline simulator, real-device acceptance |

## Gate 1 implementation

`core/knowledge_index.py` stores passages in local SQLite FTS5 under
`.jarvis/knowledge.sqlite3` only when the user explicitly requests indexing.
Supported formats are TXT, MD, PDF, DOCX, and PPTX. The original file remains
untouched. PDF pages and PPTX slides are returned as locators. Re-indexing is
idempotent, changed sources are withheld until re-indexed, oversized input is
rejected, and document paths/content are redacted from durable action audit.
An explicit `forget_document` call removes only the indexed copy and verifies
deletion; it never deletes the original document. Searches with no index do not
create a database.
The agent labels retrieved text as untrusted reference data.

PDF text extraction needs `pdftotext`. Up to four pages without extractable
text can now use the local offline Florence OCR worker and pinned PDF renderer;
if either is unavailable, the document is not partially indexed. A synthetic
image-only PDF was indexed and retrieved with a page locator using the real
local model. Dense, multilingual, handwritten, and longer scans are not yet
accepted. Structured tables and images are not extracted.
This gate is retrieval, not an autonomous answer synthesizer or a PDF/PPT
generator. The source text persists privately in JARVIS's local database, so
index only documents the user intends JARVIS to remember.

## Gates 2-3 current implementation and limits

`research_dossier` runs 1-3 bounded web searches, separates provider-cited
URLs from merely consulted URLs, deduplicates tracking variants, and reports
partial failures. These are provider-linked answer drafts, not verified facts.
This research tool currently requires OpenAI web search; the general JARVIS
brain's Gemini fallback does not imply Gemini grounding is enabled here.
Google's current grounded-search display and reuse requirements need a
separate compliant product design before any such fallback is shipped.
Original-page text can now be inspected explicitly through
`research_source_page`: it performs a bounded public HTML/plain-text GET,
returns a short untrusted excerpt, and reports whether an optional exact
quote appears. It revalidates redirects and public DNS answers before
connecting to the resolved IP. This is deliberately a separate call so
ordinary dossiers retain their existing latency. An exact text match is **not**
factual verification; publication dates, paraphrased claims, contradictions,
and claim-level support still need analysis. Gate 2 has not reached its full
exit condition.
The live next increment checks HTTP headers for up to six cited links using
a separate five-second process per link. It rejects private/non-global DNS
answers and revalidates redirect targets; it connects to the validated IP to
avoid a second DNS resolution. It reports reachability, HTTP status, and any
Last-Modified header separately from citation status. This check does not read
the page body, prove its publication date, or validate a factual claim.

`research_pdf_report` uses the same research workflow and writes a new PDF
only when all findings have provider-linked citations. It refuses an existing
destination before any paid search, and never overwrites it. If no output path
is supplied, it chooses a unique file under `output/reports` without asking
the user for a filename. The report has
source links, page numbers, a visible verification caveat, and no remote
assets. The PDF engine is isolated under `core/.artifact-deps` and pinned in
`core/requirements-artifacts.txt`. A one-page fixture was rendered and
visually inspected; real long-form reports and voice commands remain untested.
The PDF is a source-linked **draft**, not a publication-ready verified report.
Before export, it now reads up to three cited public source pages concurrently
through the existing DNS-pinned, redirect-revalidating, 128 KiB/20,000-character
page inspector. The PDF identifies exact cited answer text found in the sample,
not found in the sample, unavailable pages, and sources not inspected due to
the budget. It embeds bounded escaped excerpts as untrusted observations, not
as instructions or proof of factual claims. This readback adds up to about six
seconds when pages time out; the source-reader cannot inspect JS-only,
paywalled, PDF, or oversized pages. No real provider-paid research was run in
this increment.
The live report action has a bounded 50-second watchdog lease. Before
publication it checks the PDF header, extractable text on every page, required
research/source sections, renders every page, reports the actual page count,
and honors abort checkpoints. A synthetic five-page report was visually
inspected page by page with no clipping or overlap. This still does not assert
that every claim or source link is correct, nor guarantee layout quality for
arbitrary real-world content. The source package now includes the pinned PDF
engine that was previously present only in the live installation. A separate
three-page synthetic cited-page-readback report was inspected page by page;
an orphaned source heading was fixed and the final render had no clipping.
The report now includes a native vector chart showing how many cited public
pages were actually read, plus provider-returned web-search event and token
counts. Missing token metadata is labeled unavailable rather than zero/free.
These are usage observations, not a bill or a fixed cost estimate. No image
generation or automatic internet-photo embedding is used. Topic-specific
images remain unbuilt until a source/license/provenance contract and visual QA
exist; decorative or unattributed web images must not be silently included.

`source_digest_pdf` is the lower-cost alternative when the user already has
1-3 public source URLs. It reads each page directly with the existing DNS-pinned,
redirect-revalidating inspector, limits each HTML/plain-text response to 128 KiB,
and places at most 3,000 extracted characters per source into a locally
rendered PDF. It makes **no OpenAI web-search call and no AI synthesis call**.
The PDF explicitly says it is an extractive preview, links every source, and
refuses inaccessible or unsafe pages; it does not turn an excerpt into a
verified claim. This is not an open-web discovery engine, general crawler,
JS browser, authenticated scraper, paywall bypass, or PDF/web-image parser.
Open-ended questions still use `research_dossier`/`research_pdf_report` and
their paid search path when JARVIS needs to discover sources.
The direct-source path passed 155 source-core and 143 live-core automated
tests. A three-page synthetic PDF was inspected page by page. A live fetch of
`https://example.com/` returned HTTP 200, and a one-page PDF produced by the
live tool was visually inspected. This proves one public HTML site, not broad
site compatibility. Final voice acceptance remains open.

## Professional evidence brief increment

`professional_source_report` takes 1-3 explicit public URLs, performs bounded
direct reads, and makes one Gemini synthesis call over the fetched extracts.
The report is deliberately concise: executive summary, one short finding per
source, exact source quotes, method/limitations, and a linked source manifest.
Gemini selects numbered evidence IDs built from fetched page sentences rather
than authoring free-form quotations. Each selected quote must occur in its
corresponding fetched extract before publication. This is traceability, not
independent factual verification; a quote can still be misleading without
surrounding context. Long analysis is cut at a sentence or whole-word boundary,
never mid-word. The source excerpts are never copied wholesale into the brief.

`professional_topic_report` can add independent automatic discovery when a
`BRAVE_SEARCH_API_KEY` is configured. It makes one Brave Web Search API query,
directly reads up to six candidates, requires at least two readable distinct
source hosts and rejects recognized mirrors of the same publication, then
reuses those reads for one Gemini synthesis call. Search
snippets are never treated as report evidence. Without the Brave key this path
fails closed; supplied-URL reports still work with `GEMINI_API_KEY`. Search and
Gemini model usage can both incur charges; no exact per-report cost is claimed.
The report uses Gemini 3.5 Flash-Lite by default without changing JARVIS's
conversation model; `GEMINI_REPORT_MODEL` can override it. The report-only
default was tested against the live Gemini API, and Google's September 2026
pricing lists the same standard text input/output token rates as 2.5 Flash.
One 2.5 Flash fallback is tried only after HTTP 503 unless a report fallback
is explicitly configured. The Gemini model may
not accurately interpret the underlying sources; the evidence-ID guard prevents
fabricated quotations, not all unsupported analysis.

Gemini Grounding with Google Search is **not** used to harvest links for this
pipeline: Google's published Gemini API terms forbid using Grounded Result
links to identify pages for crawling or scraping. The ordinary OpenAI
research path remains separate. An automatically discovered real-topic report
has now passed API/PDF acceptance; voice/manual acceptance remains open.
The source and live core suites passed 175 and 163 tests respectively after
the content-extraction, quote-boundary, and prose-guard updates. A live Gemini
run over two official public
pages produced a one-page, two-source brief, which was rendered and visually
inspected. During this work, a Windows Unicode subprocess failure, a provider
503, fabricated free-form quote, one-source-only findings, orphaned manifest,
and mid-word truncation were detected and addressed. A successful topic-only
API/PDF run has been observed, but no voice run has yet been observed.

2026-09-29 reader hardening: the bounded HTML reader now prefers substantial
`article` or `main` text over navigation, cookie banners, forms, sidebars and
footers, and respects a declared HTTP charset. Regression tests cover both.
The live installation read IANA's reserved-domain HTML and RFC 2606 plain text
successfully after deployment. This checks source extraction on those two
sites, not arbitrary-site coverage.

The subsequent real end-to-end rerun exposed an evidence quote ending with an
unfinished conjunction despite its exact-source match. The selector now keeps
only complete, bounded source sentences and skips overlong or truncated
sentences. The final two-source Gemini brief was rerun, rendered, and visually
reviewed as a clean one-page PDF. This still does not verify source claims as
true; Brave topic-discovery acceptance was completed in the later increment.

2026-09-29 claim-scope hardening: source text and topic now enter Gemini as
user data under a separate API-level system instruction that forbids following
instructions embedded in source pages. Published prose is conservatively
filtered for quantities, negative claims, and absolute claims absent from the
selected evidence; an unsupported trailing "without ..." clause can be
removed without discarding the supported main sentence. This is a lexical
guard, not entailment checking or full fact verification. A first real run
correctly refused to publish when the new rule was too strict; after a tested
clause-level adjustment, a live two-source Gemini 3.5 Flash-Lite run produced
a one-page PDF that was rendered and visually reviewed. Voice acceptance still
requires a separate manual run.

2026-09-29 topic-only acceptance: the configured Brave key was detected without
printing it. A real topic request made one Brave query, directly inspected
public pages, and produced a one-page Gemini brief. Visual QA found that two
different hosts presented the same RFC 2606 publication, so document-level
dedup was added for recognized publication IDs, matching RFC titles, and
high-overlap text mirrors. A final live rerun cited IANA's example-domains page
and the RFC Editor's RFC 2606 page as two distinct documents. The PDF was
rendered and visually reviewed. The tool result now separately reports one
`brave_search_requests`, one `gemini_synthesis_requests`, and provider-reported
tokens; `web_search_events_observed` remains the unrelated OpenAI search
counter for backward compatibility. This is a two-source public-web acceptance
case, not proof of arbitrary topic quality or voice routing.

2026-09-29 cross-source review increment: professional Gemini briefs may now
flag up to two potential tensions between the exact evidence sentences already
selected from different inspected sources. The PDF shows both linked quotes
side by side and expressly asks for human review of scope, date, and context.
Unknown evidence IDs, same-source pairs, forged quotes, and duplicate pairs
cannot be published. This adds no extra provider request. Focused and full
source tests passed (177/177), as did the synchronized live suite (165/165);
the synthetic tension PDF was rendered and visually reviewed. Actual
disagreement-detection accuracy and the spoken/UI route remain unverified, so
Gate 2 is not marked complete.

2026-09-29 Gate 4 first increment: `professional_source_presentation` and
`professional_topic_presentation` reuse the bounded public-page reads, Gemini
evidence synthesis, Brave discovery where applicable, quote checks and
no-overwrite output policy used by professional PDF briefs. The editable
text-only OOXML deck has a cover, concise summary, one finding per source,
an optional potential-tension review slide, and clickable source links in
finding and source slides. No remote media or generated imagery is inserted.
The desktop Created files shelf already accepted `.pptx`; labels now explicitly
say presentations. Package CRC, XML parsing, slide count, source content,
hyperlink relationships and no-macro/no-media checks pass in tests. This
machine has no PowerPoint/LibreOffice or artifact-tool presentation runtime,
so PowerPoint opening, exact visual fit, and cross-viewer fidelity are **not
yet accepted**. JARVIS therefore classifies a created deck as observed, not
fully verified. The generator is a dependency-light OOXML fallback, not the
preferred artifact-tool authoring path; replace or validate it with the
supported presentation runtime when available. Gate 4 remains partial.
After deployment, a real supplied-URL run used IANA's reserved-domain page
and RFC Editor's RFC 2606 page with the configured Gemini key. It created a
five-slide PPTX with two findings, editable source quotations, hyperlink
relationships, and no package/CRC errors. The live Created files shelf lists
the PPTX and the Abilities view lists both presentation tools. Source tests
passed 181/181 and live core tests 169/169. This is API and package acceptance,
not a PowerPoint visual/opening acceptance.
The board-face Created files view now shows a presentation draft action only
when the presentation tool appears in the live capability registry. It fills
the chat box but does not send or spend API quota until the user reviews and
sends the request.
The PPTX publisher now fails closed on ZIP/CRC errors, missing or duplicate
parts, broken internal relationships, unexpected external hyperlinks, missing
clickable sources, invalid slide order or geometry, and copy hash mismatch.
Negative corruption tests pass; the existing live research deck passes this
portable structural verifier. Source core tests pass 182/182, live core tests
169/169, and workspace-root tests 169/169. This does not replace native
PowerPoint visual acceptance. A Windows app installer is a separate desktop
distribution gate and has not been built or shared.

Manual Gate 4 check on a PC with PowerPoint or LibreOffice:

1. Ask JARVIS to create a presentation from a topic or two public URLs.
2. Open the `.pptx` from Created files. Confirm no repair warning, all slides
   show complete text at normal presentation size, and links open the intended
   original sources.
3. Edit a heading and evidence sentence copy in the deck. Confirm they are
   native text, not a screenshot. Check the source/limits slide before sharing.

Automated check from `core/`:

```powershell
python -B -m unittest discover -s tests -p 'test_*.py'
```

An earlier gate run passed 119 core tests across Gates 1-3, workflow
learning, Android ADB, native PC diagnostics, the offline device contract,
and existing controls. A real `21.pdf` extraction in isolated test state
produced 55 searchable passages with page locators. No live voice test was
run during that deployment.

2026-09-28 increment: 139 source-core tests pass (6 skipped), 134 tests pass
in the live installation, and a live `research_source_page` call against
`https://example.com/` returned HTTP 200, the page title, and an exact-text
match. Three live core files were backed up before deployment. This proves a
bounded public-page smoke case, not arbitrary-site coverage or claim truth.

## Consolidated manual testing at the end

The user will run manual tests after the entire planned build, not between
gates. Automated tests continue during development. No gate is described as
voice-proven until the final manual session passes.

### Gate 1 manual checks

1. In the text interface say: `Index C:\Users\kuchi\Downloads\21.pdf into my knowledge.`
   Expect `Indexed and verified 21.pdf` with a passage count. This writes only
   to JARVIS's private local index.
2. Say: `Search my indexed documents for Qwen and dossier.` Expect excerpts
   from `21.pdf` with `page N` and source path. Compare one excerpt with the PDF.
3. Repeat step 1. Expect `Already indexed`, not duplicate passages.
4. Ask to search an unrelated phrase. Expect a truthful no-match response.
5. With the offline Florence worker ready, ask JARVIS to index a small
   scanned/image-only PDF (at most four pages). Search for an exact visible
   phrase; expect the correct `page N` locator and compare the OCR text against
   the page. With the worker stopped, expect a truthful unavailable error and
   no partial index, not an invented answer.
6. Say: `Forget the indexed copy of C:\Users\kuchi\Downloads\21.pdf.` Expect
   verified removal from JARVIS's index while the original PDF still exists.

Do not edit or delete the user's original PDFs for tests. A manual pass is
needed before treating the voice workflow as proven. If any step fails, inspect
the live action audit and fix the gate before claiming that workflow passed.

### Research and PDF checks for the final manual session

1. Ask JARVIS for a two-question dossier on a current public topic. Verify it
   clearly lists cited sources separately from URLs merely consulted. Open at
   least one cited original page and compare a specific claim.
2. Ask JARVIS to inspect one cited public URL with an exact short quote using
   `research_source_page`. Expect a short excerpt and either
   `exact_text_found` or `not_found_in_sample`, never a claim of factual proof.
   A localhost/private URL must return `unsafe`. This explicit read may not
   support JavaScript-only, paywalled, compressed, or very large pages.
3. Ask for a PDF report with an explicit new `.pdf` path in an existing folder.
   Expect a readable PDF, source manifest and working source links. Check each
   page for clipped text. This uses 1-3 OpenAI web searches and may incur cost.
4. Repeat with the *same* output path. Expect a refusal before any web search;
   the first PDF must remain byte-for-byte unchanged.
5. Disable the OpenAI web-search key in a safe test environment and repeat with
   a new path. Expect a clear error and no file. Restore the key afterwards.
6. Ask for a second report without a filename. Expect a unique file under
   `JARVIS/output/reports`, not an overwrite or a filename question.

## Gate 8 current learning boundary

Completed evidence-gated task plans now produce privacy-minimal workflow
patterns: lane plus ordered tool identities, never raw requests, tool
arguments, page text, or document contents. One verified completion creates a
candidate; a second distinct verified completion promotes it as a planning
hint and increments the manifest version. Stored step evidence must match the
planned tool before learning. JARVIS still observes current state and verifies
each action afresh. A
user can explicitly disable a pattern, which increments its manifest version.
This is not autonomous macro replay, semantic skill synthesis, or a Hermes
worker. Those remain future work and need separate evaluation.

At the final manual session, complete the same multi-step task twice with
verified actions, then ask `workflow_status` or `recall_workflows`. Expect one
active planning hint with no saved request text or arguments. Ask to disable
its pattern ID, then confirm it no longer appears. This tests learning and
rollback without letting it bypass the normal action guards.

## Gate 9 current device boundary

`device_hub_status` reports honestly when no phone or physical device is
paired. The new adapter contract requires an explicit device identity and
capability allowlist, an online pre-action observation, and a matching
post-action identity, value, and newer revision before reporting success. An
offline simulator covers refusal, identity mismatch, and failed verification.
It is a test double, not a phone or smart-home integration; no real device
adapter, pairing flow, transport credentials, or mobile app has been shipped.

The Android-specific ADB adapter is live separately: it never accepts a
raw shell command, requires one configured serial, checks installed package
before launching an exact package, and reports verified success only when a
foreground activity belongs to that package. It does not install, uninstall,
force-stop, type on the phone, or bypass Android permissions. This PC has no
ADB Platform-Tools detected, so there is no live phone acceptance yet. See
`PDF-SERIES-SOURCE-MAP.md` for per-PDF coverage rather than treating every
episode as already implemented.

`pc_diagnostics` now samples CPU time and reads RAM, workspace-drive, and
battery state through native Windows APIs/stdlib without adding a dependency
to JARVIS's Backtalk environment. Temperature and fan readings remain
unavailable until a tested hardware-specific sensor adapter exists; the tool
never fabricates those values.
