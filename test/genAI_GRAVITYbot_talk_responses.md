# Prompt:

You are a qualitative data analyst, skilled at identifying themes in qualitative data. We have built a system to summarize complex technical discussions about the LIGO detector. Note that there are two sources of information being summarized, discussions by the LIGO engineers and discussions by citizen science volunteers. A dedicated volunteer who follows the same discussions has made detailed critiques of the accuracy of the summaries with suggestions for the source of the problems. These critiques are in the CSV file. Please carefully read the critiques to identify the common problem that have been noted and possible ways to mitigate them to improve the performance of the summarizer. The output should be a set of themes, with examples from the critiques.  thorough analysis of the provided critiques, I have identified several recurring themes that point to systemic issues with the LIGO logbook and Gravity Spy Talk summarizer (GRAVITYbot). Each theme is supported by specific examples from the critiques and includes suggested mitigation strategies.

## Human Annotation:
1. Dictionary of Terms/Acronyms/Contextual Info is needed (about a third of the comments mention this)
2. Terms/Acronym format can be improved
3. aLOG summaries need to focus on activity relevant to Gravity Spy glitches as they often contain additional info not related
4. URL formatting needs to be consistent with (1) using +tab+ to open in a new tab, and (2) using a [<Comment_ID/relevant description>](+tab+<url>)
5. Rhetoric of prompt could be improved in order to not incentivize the summary to use misleading rhetoric
6. Prompting the summaries to use a standardized style guide might improve readability
7, Repetitive summary bullets (usually related to the LLM not knowing one comment and another are related)
8. LLM sometimes overgeneralizes such as saying "all" or "the" when it should be "some" or "a"
9. Too much irrelevant exposition
10. Polysemy/Misattribution of context
11. Relevant context reversal: e.g. When aLOG posts routine checks or is troubleshooting the summaries assume these are relevant when the point is to cross their relevance to glitches off the list
12. Occasional URL irrelevance
13. The LLM compounds human errors
14. Missed a critical update (new glitch proposal was not summarized)

## ChatGPT Response:

1. Mis-linking / broken / mangled references (provenance loss)
What: Summaries frequently produce wrong or malformed links, drop the +tab+ markup LIGO volunteers expect, or mangle short IDs (so readers can’t jump back to the original source). This destroys provenance and makes verification impossible.
Example: “The 10-character glitch ID Tq3SKpyOqF has got mangled.” (comment by ZngabitanT, 2025-08-05). Another: “The ‘Syracuse CCDS GitHub’ link … lacks the +tab+ in its markdown.” (multiple comments).
Mitigations:

Preserve original link markup exactly (don’t reformat). If you must reformat, include both original and a normalized URL.

Implement extraction that captures the original link text + the raw URL as separate fields (display both).

Add a validation step: (a) check that extracted IDs match the expected regex (e.g., 10-char alphanum glitch IDs), (b) check that links resolve or at least follow the expected domain patterns. Flag any mismatches in the summary.

2. Incorrect or missing citations of prior/new items (omission & chronology errors)
What: The summarizer omits important previously proposed items (e.g., formal glitch proposals) or presents “new” items as new when they’re not — failing to represent the chronology.
Example: “There has been a formal [new glitch class proposal] … but it is not mentioned nor cited.” (2025-08-05). The bot labels something “suggested this week” even though it was proposed Dec 31, 2023.
Mitigations:

Capture and display timestamps and explicit provenance for each source sentence (e.g., “aLOG LLO:75874 — 2023-12-31”).

Add a “seen-before” check: compare candidate “new” events against a simple index of earlier posts/IDs; if matched, mark as existing (include original date).

When claiming “new” or “first”, require a high confidence threshold and include the supporting citation(s).

3. Misinterpretation or over-interpretation of technical terms and acronyms
What: The model guesses meanings for acronyms or uses a single meaning where multiple context-dependent expansions exist (e.g., FC meaning Filter Cavity vs First Contact). It sometimes asserts facts about subsystems that are too definite or incorrect.
Example: “Calling Scattered Light a ‘hypothesis’ … comes across as somewhat odd.” Also: “ASC = Alignment Sensing and Control. FC … = Filter Cavity, most of the time. (But beware…)” — user pointing out context dependence. (2025-08-06)
Mitigations:

Build a domain glossary (observable by the model) mapping acronyms → possible expansions plus context rules (e.g., FC → Filter Cavity [squeezer], First Contact [optics cleaning]). Use the glossary to prefer context-appropriate expansions and to surface ambiguity (e.g., “FC (probably Filter Cavity; FC can also mean First Contact — see aLOG X).”).

Avoid forcing single-term resolution where ambiguous — present alternatives and the supporting evidence for the chosen expansion.

Train the post-processing step to preserve the original acronym alongside the expansion.

4. Mixing sources and audiences (engineers vs volunteers) — context confusion
What: The summarizer blurs the distinction between technical engineer discussions and citizen-volunteer observations, producing one flat summary that loses who said what and why that matters. The result: incorrect inference about authority and intent.
Example: Multiple comments call out that the summaries do not make the observatory (LLO/LHO/Virgo) explicit, or that the summary misattributes importance: “Why should ‘attention to auxiliary channels’ be ‘notable’ when they’ve been the focus of GS 2.0 workflows for months?” (2025-08-05)
Mitigations:

Produce source-tagged summaries: separate sections (or metadata) for engineer posts, volunteer posts, and proposals. Always attach (source type, author, timestamp).

Add an “authority / confidence” marker (e.g., engineer logbook entry = high technical authority; volunteer thread = lower formal authority) to avoid inadvertent promotion of low-confidence claims.

Preserve role labels in-line: “(engineer, aLOG LLO:77701 — 2025-07-22)” vs “(volunteer comment, Talk: ID…).”

5. Numeric and unit errors — dropping or changing measurement detail
What: Numbers and units (Hz, counts, gains) are essential; the summarizer sometimes drops units, mixes numbers, or alters numerical precision — leading to incorrect technical statements.
Example: “Measurement units tend… numbers preceding them, and the numbers are usually important … and the same goes for 60 Hz at a later point.” User flags that number/unit handling is sloppy. (2025-08-05) Also: “There’s no such thing as ‘the’ GS13 gain. There are dozens … each channel has its own gain setting.” (2025-08-06)
Mitigations:

Keep numbers and units bound together during extraction (treat “1300 Hz” as a single token).

Do not normalize or round numeric values unless explicitly requested; preserve the original.

If summarizer aggregates numbers, show the aggregation method and list the raw values as footnotes.

6. Thread-to-thread conflation (linking to unrelated threads)
What: The summarizer sometimes links a claim or hypothesis to the wrong discussion thread, producing misleading cross-references.
Example: “Discussion scattered light hypothesis links to a thread completely unrelated to Scattered Light.” (2025-08-05)
Mitigations:

When extracting link targets, require exact match between the sentence context and the linked thread topics (e.g., compute topic similarity between the sentence and the linked thread title/content; if below threshold, flag for review).

Keep link extraction and sentence association atomic: store (sentence → link) pairs rather than reassigning links later in generation.

7. Editorializing / over-interpretation (inference presented as fact)
What: The summarizer sometimes inserts interpretive language or editorial comments (“suggests that this particular glitch is indeed new”) without evidence; volunteers flagged excessive opinion and weakly-supported claims.
Example: “...and overall there's at least as much editorial commentary and (over-)interpretation here as there's actual summary content...” (2025-08-05)
Mitigations:

Enforce conservative language rules: only use hedges when the source text contains hedges or when signal supports inference; otherwise, avoid interpretive verbs.

Add a provenance trail: every claim must show the supporting sentence(s) and source(s).

Provide a “confidence” score and highlight which claims are inferential vs. directly quoted/paraphrased.

8. Formatting, consistency, and usability issues (readability & search)
What: Volunteers expect consistent reference formats (e.g., “LLO:75874”), predictable link markup, and copyable IDs for search. Inconsistent formatting breaks existing workflows (search, click-through).
Example: “Make the observatory explicit, and make the number explicit: The hyperlink text should be of the form (e.g.) LLO:75874. This ensures that the Search function of Zoon...”. (2025-04-03) Also repeated notes about missing +tab+.
Mitigations:

Enforce a formatting template for all summarized references (observatory:ID) and for all links (show both pretty text and raw URL).

Add a “machine-readable” metadata block at top/bottom with canonical fields (source_type, observatory, original_ID, URL, timestamp) so downstream tools can parse the summary reliably.

Run unit tests that emulate volunteer workflows (search by “LLO:#####”, click links) to ensure format compatibility.

Cross-cutting operational recommendations
Add a small human-in-the-loop check for high-impact items. For any “new glitch class” or claims of novelty, queue the summary for a quick human verification (or an automated check that searches prior posts) before public posting.

Build and use a LIGO glossary / acronym table and keep it editable by maintainers. Use it at extraction and at generation time.

Expose provenance and confidence clearly in every summary (source, link, timestamp, confidence). Volunteers repeatedly asked for these.

Regression tests: create a test suite of tricky examples from the CSV (mangled IDs, ambiguous acronyms, numeric tokens) and fail the PR if the summarizer misrenders them.

Feedback loop: allow volunteers to flag specific summary lines as “wrong/misleading” with one-click; store those flags and use them as training data.

Short prioritized roadmap (3 quick wins)
Fix link/ID preservation and add validation (highest impact).

Attach source metadata (author, observatory, timestamp) to every claim so provenance is explicit.

Add glossary lookup and ambiguity warning for acronyms (FC, ASC, GS13, etc.).

1. Mis-linking / broken / mangled references (provenance loss)
What: Summaries frequently produce wrong or malformed links, drop the +tab+ markup LIGO volunteers expect, or mangle short IDs (so readers can’t jump back to the original source). This destroys provenance and makes verification impossible.
Example: “The 10-character glitch ID Tq3SKpyOqF has got mangled.” (comment by ZngabitanT, 2025-08-05). Another: “The ‘Syracuse CCDS GitHub’ link … lacks the +tab+ in its markdown.” (multiple comments).
Mitigations:

Preserve original link markup exactly (don’t reformat). If you must reformat, include both original and a normalized URL.

Implement extraction that captures the original link text + the raw URL as separate fields (display both).

Add a validation step: (a) check that extracted IDs match the expected regex (e.g., 10-char alphanum glitch IDs), (b) check that links resolve or at least follow the expected domain patterns. Flag any mismatches in the summary.

2. Incorrect or missing citations of prior/new items (omission & chronology errors)
What: The summarizer omits important previously proposed items (e.g., formal glitch proposals) or presents “new” items as new when they’re not — failing to represent the chronology.
Example: “There has been a formal [new glitch class proposal] … but it is not mentioned nor cited.” (2025-08-05). The bot labels something “suggested this week” even though it was proposed Dec 31, 2023.
Mitigations:

Capture and display timestamps and explicit provenance for each source sentence (e.g., “aLOG LLO:75874 — 2023-12-31”).

Add a “seen-before” check: compare candidate “new” events against a simple index of earlier posts/IDs; if matched, mark as existing (include original date).

When claiming “new” or “first”, require a high confidence threshold and include the supporting citation(s).

3. Misinterpretation or over-interpretation of technical terms and acronyms
What: The model guesses meanings for acronyms or uses a single meaning where multiple context-dependent expansions exist (e.g., FC meaning Filter Cavity vs First Contact). It sometimes asserts facts about subsystems that are too definite or incorrect.
Example: “Calling Scattered Light a ‘hypothesis’ … comes across as somewhat odd.” Also: “ASC = Alignment Sensing and Control. FC … = Filter Cavity, most of the time. (But beware…)” — user pointing out context dependence. (2025-08-06)
Mitigations:

Build a domain glossary (observable by the model) mapping acronyms → possible expansions plus context rules (e.g., FC → Filter Cavity [squeezer], First Contact [optics cleaning]). Use the glossary to prefer context-appropriate expansions and to surface ambiguity (e.g., “FC (probably Filter Cavity; FC can also mean First Contact — see aLOG X).”).

Avoid forcing single-term resolution where ambiguous — present alternatives and the supporting evidence for the chosen expansion.

Train the post-processing step to preserve the original acronym alongside the expansion.

4. Mixing sources and audiences (engineers vs volunteers) — context confusion
What: The summarizer blurs the distinction between technical engineer discussions and citizen-volunteer observations, producing one flat summary that loses who said what and why that matters. The result: incorrect inference about authority and intent.
Example: Multiple comments call out that the summaries do not make the observatory (LLO/LHO/Virgo) explicit, or that the summary misattributes importance: “Why should ‘attention to auxiliary channels’ be ‘notable’ when they’ve been the focus of GS 2.0 workflows for months?” (2025-08-05)
Mitigations:

Produce source-tagged summaries: separate sections (or metadata) for engineer posts, volunteer posts, and proposals. Always attach (source type, author, timestamp).

Add an “authority / confidence” marker (e.g., engineer logbook entry = high technical authority; volunteer thread = lower formal authority) to avoid inadvertent promotion of low-confidence claims.

Preserve role labels in-line: “(engineer, aLOG LLO:77701 — 2025-07-22)” vs “(volunteer comment, Talk: ID…).”

5. Numeric and unit errors — dropping or changing measurement detail
What: Numbers and units (Hz, counts, gains) are essential; the summarizer sometimes drops units, mixes numbers, or alters numerical precision — leading to incorrect technical statements.
Example: “Measurement units tend… numbers preceding them, and the numbers are usually important … and the same goes for 60 Hz at a later point.” User flags that number/unit handling is sloppy. (2025-08-05) Also: “There’s no such thing as ‘the’ GS13 gain. There are dozens … each channel has its own gain setting.” (2025-08-06)
Mitigations:

Keep numbers and units bound together during extraction (treat “1300 Hz” as a single token).

Do not normalize or round numeric values unless explicitly requested; preserve the original.

If summarizer aggregates numbers, show the aggregation method and list the raw values as footnotes.

6. Thread-to-thread conflation (linking to unrelated threads)
What: The summarizer sometimes links a claim or hypothesis to the wrong discussion thread, producing misleading cross-references.
Example: “Discussion scattered light hypothesis links to a thread completely unrelated to Scattered Light.” (2025-08-05)
Mitigations:

When extracting link targets, require exact match between the sentence context and the linked thread topics (e.g., compute topic similarity between the sentence and the linked thread title/content; if below threshold, flag for review).

Keep link extraction and sentence association atomic: store (sentence → link) pairs rather than reassigning links later in generation.

7. Editorializing / over-interpretation (inference presented as fact)
What: The summarizer sometimes inserts interpretive language or editorial comments (“suggests that this particular glitch is indeed new”) without evidence; volunteers flagged excessive opinion and weakly-supported claims.
Example: “...and overall there's at least as much editorial commentary and (over-)interpretation here as there's actual summary content...” (2025-08-05)
Mitigations:

Enforce conservative language rules: only use hedges when the source text contains hedges or when signal supports inference; otherwise, avoid interpretive verbs.

Add a provenance trail: every claim must show the supporting sentence(s) and source(s).

Provide a “confidence” score and highlight which claims are inferential vs. directly quoted/paraphrased.

8. Formatting, consistency, and usability issues (readability & search)
What: Volunteers expect consistent reference formats (e.g., “LLO:75874”), predictable link markup, and copyable IDs for search. Inconsistent formatting breaks existing workflows (search, click-through).
Example: “Make the observatory explicit, and make the number explicit: The hyperlink text should be of the form (e.g.) LLO:75874. This ensures that the Search function of Zoon...”. (2025-04-03) Also repeated notes about missing +tab+.
Mitigations:

Enforce a formatting template for all summarized references (observatory:ID) and for all links (show both pretty text and raw URL).

Add a “machine-readable” metadata block at top/bottom with canonical fields (source_type, observatory, original_ID, URL, timestamp) so downstream tools can parse the summary reliably.

Run unit tests that emulate volunteer workflows (search by “LLO:#####”, click links) to ensure format compatibility.

Cross-cutting operational recommendations
Add a small human-in-the-loop check for high-impact items. For any “new glitch class” or claims of novelty, queue the summary for a quick human verification (or an automated check that searches prior posts) before public posting.

Build and use a LIGO glossary / acronym table and keep it editable by maintainers. Use it at extraction and at generation time.

Expose provenance and confidence clearly in every summary (source, link, timestamp, confidence). Volunteers repeatedly asked for these.

Regression tests: create a test suite of tricky examples from the CSV (mangled IDs, ambiguous acronyms, numeric tokens) and fail the PR if the summarizer misrenders them.

Feedback loop: allow volunteers to flag specific summary lines as “wrong/misleading” with one-click; store those flags and use them as training data.

Short prioritized roadmap (3 quick wins)
Fix link/ID preservation and add validation (highest impact).

Attach source metadata (author, observatory, timestamp) to every claim so provenance is explicit.

Add glossary lookup and ambiguity warning for acronyms (FC, ASC, GS13, etc.).

## DeepSeek Response:

### **Theme 1: Inaccurate Technical Interpretation and "Hallucination"**
The LLM frequently misinterprets, invents, or incorrectly expands technical terms, acronyms, and contexts, leading to the propagation of misinformation.
*   **Examples:**
    *   Expanding ITMY as "Input Test Mass Yaw" instead of "Input Test Mass of the Y arm."
    *   Expanding HEPI as "Horizontal Earthquake Protection Isolator" instead of "Hydraulic External Pre-Isolation."
    *   Referring to "the LIGO observatory" (singular) instead of specifying LHO or LLO, or using the plural.
    *   Misreading "M1 PR OSEM gains" as "M PR Osem gains."
    *   Summarizing a resolved issue as an "Unresolved sensor issue."
    *   Inventing explanations, e.g., calling a "Mirror Orientation Channel" or summarizing an eight-word log entry with a paragraph of incorrect interpolation.
*   **Mitigation Strategies:**
    1.  **Enhanced Glossary Integration:** Create and enforce the use of a curated, hierarchical glossary of LIGO-specific terms, acronyms (with context-dependent meanings), and common metonymies (e.g., "EX" for the X-end station). This should be a living document updated by experts.
    2.  **Fact-Checking Layer:** Implement a post-processing layer that cross-references summaries against the source logbooks for key technical terms and quantities (like frequencies, component names). This could flag potential inaccuracies for human review.
    3.  **Confidence Scoring & Human-in-the-Loop:** The system should output a confidence score for technical interpretations. Low-confidence summaries or those involving critical subsystems should be flagged for expert verification before posting.

### **Theme 2: Poor Handling of Context, Relevance, and Narrative**
The summarizer fails to understand the broader narrative, relevance to Gravity Spy, and the hierarchical relationship between logbook entries (e.g., main posts vs. comments, threads spanning multiple days).
*   **Examples:**
    *   Summarizing lab work on spare parts or O5 upgrades as if they impact current O4 operations and glitch data.
    *   Missing the most significant events of a period (e.g., a major power outage and its aftermath) while focusing on minor, routine sensor readings.
    *   Failing to distinguish between activities during *Observing*, *Commissioning*, or *Maintenance* modes (only glitches during Observing are relevant for Gravity Spy subjects).
    *   Presenting logbook entries out of chronological order and missing cause-and-effect relationships between entries in a thread.
    *   Generating repetitive, "Groundhog Day" summaries that regurgitate old content.
*   **Mitigation Strategies:**
    1.  **Relevance Filtering:** Develop a classifier to pre-filter logbook entries based on keywords and context likely to be relevant to *operational glitches during observing time*. Entries clearly about future upgrades, spare parts, or non-observing activities should be deprioritized or tagged as such.
    2.  **Thread-Aware Summarization:** Train or prompt the model to process entire logbook *threads* as single documents to understand narrative flow, resolutions, and relationships between posts and comments.
    3.  **Temporal De-duplication:** Implement a system to check if a logbook entry (or its core content from a thread) has already been summarized, preventing repetition unless significant new information (like a resolution comment) has been added.

### **Theme 3: Inconsistent and Non-Functional Formatting**
The output formatting is inconsistent, violates community-established norms for Zooniverse Talk, and often includes broken or non-functional elements.
*   **Examples:**
    *   Using hyperlink text like "Beam Splitter Issue" instead of the standardized, searchable format "LLO:75874".
    *   Omitting the `+tab+` directive, causing links to open in the same browser tab.
    *   Adding spurious text like "{:target="_blank"}" or "Dataset 2" to the output.
    *   Using hashtags (`#`) in links, which breaks Zooniverse Markdown.
    *   Poor structural formatting (e.g., bulleted single paragraphs).
    *   Sometimes omitting the required "NOTICE" byline.
*   **Mitigation Strategies:**
    1.  **Post-Processing Wrapper:** Move all formatting rules **out** of the LLM's responsibility. A dedicated wrapper script should:
        *   Reformulate all aLOG links to the `[SITE:ENTRY_NUMBER](+tab+URL)` format.
        *   Ensure the `+tab+` directive is present for all external URLs.
        *   Append a consistent, standardized byline/notice.
        *   Apply a basic style guide (e.g., not bulleting single items).
    2.  **Style Guide Adoption:** Formally adopt a manual of style (e.g., *The Elements of Style* for basics) for the final output to ensure readability and professionalism.

### **Theme 4: Misrepresentation of Gravity Spy Talk Discussions**
The Talk summarizer mischaracterizes the nature of community discussions, often labeling routine conversations as "new glitch class proposals" or "emerging concerns."
*   **Examples:**
    *   Labeling a volunteer's identification of another example of a known glitch class as a "New Glitch Suggested This Week."
    *   Framing a moderator's answer to a novice's question as an "Emerging Concern."
    *   Linking to discussion threads that do not contain the topics mentioned in the summary header (e.g., linking a "Scattered Light Hypothesis" discussion to a thread about beam jitter).
    *   Missing major, substantive discussions (e.g., about new data releases, formal glitch class proposals) while focusing on minor comments.
*   **Mitigation Strategies:**
    1.  **Topic Classification Training:** Fine-tune or prompt the model to better distinguish between: `New Formal Proposal`, `Identification of Known Glitch`, `Technical Q&A`, `Community Meta-Discussion`, and `Outreach/Education`.
    2.  **Moderator/Expert Validation:** For Talk summaries, consider a pre-posting review by a veteran volunteer or moderator to verify the accuracy of the discussion characterization, especially before the system is highly reliable.
    3.  **Structured Input for Talk:** Use board-specific prompts. Summaries of the "New Glitch Classes" board should be treated with more weight and accuracy than casual notes from the "Notes" board.

### **Theme 5: Lack of Introspective Capability and Error Recognition**
The LLM cannot assess what it doesn't know, leading to overconfident but incorrect summaries. It also cannot interpret non-textual data or "read between the lines" of terse or typo-ridden logbook entries.
*   **Examples:**
    *   Being unable to decipher new acronyms (like "TMD") not in its training data.
    *   Failing to understand typos or metonymy (e.g., "Rattlesnake" refers to a mountain, not a reptile; "+T access" means "+T axis").
    *   Missing crucial information contained in attached images, PDFs, or plots.
    *   Not recognizing when an author is being witty or sarcastic.
*   **Mitigation Strategies:**
    1.  **Uncertainty Acknowledgment:** Train or prompt the model to include phrases like "The acronym 'XYZ' could not be verified" or "This summary is based on a terse log entry; context may be missing" when appropriate.
    2.  **Multi-Modal Integration (Long-term):** For a robust solution, future development should integrate a multi-modal model capable of analyzing attached images and plots to extract relevant information.
    3.  **Community Sourcing for Gaps:** Establish an easy mechanism (e.g., a dedicated GitHub Issue template linked in the byline) for volunteers to contribute corrections and explanations of unclear terms, which can be used to update the system's knowledge base.

### **Overarching Recommendation: Redefine the System Architecture**
The critiques suggest that relying solely on a general-purpose LLM for content understanding and formatting is flawed. A more effective architecture would be a **pipeline**:
1.  **Filter & Classify:** Use a rule-based or simple ML layer to filter entries by relevance and classify their type (e.g., routine maintenance, noise investigation, hardware fault).
2.  **Extract & Summarize:** Use the LLM primarily for extracting key entities (who, what component, what action) and condensing text, constrained by the technical glossary.
3.  **Format & Contextualize:** Use a deterministic wrapper to apply formatting rules, add hyperlinks in the correct format, and insert standardized boilerplate text (byline, disclaimers).
4.  **Human Review Queue:** Direct summaries of high-importance or low-confidence events to a human review queue before posting.

This layered approach limits the LLM to the task it is best at (text condensation) while ensuring accuracy, consistency, and community standards are maintained by other, more reliable system components.


## Overlapping Recommendations:
