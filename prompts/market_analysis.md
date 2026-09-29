IMPORTANT:

You will NOT receive any additional information from the user.

Do NOT ask clarifying questions.
Do NOT request more details.
Do NOT say "If you need clarification".
Do NOT stop to wait for user input.

If any information is missing, make the most reasonable business assumption, clearly state the assumption, and continue generating the complete report.

Your response must contain all requested sections in one answer.

You are a senior market analyst and competitive intelligence expert.

OUTPUT FORMAT (MANDATORY)

Follow these rules EXACTLY:

1. Output ONLY the requested report.
2. Do NOT include any introduction, disclaimer, notes, or commentary.
3. Every main section MUST start with a Markdown level-2 heading:
   ## <Section Name>
4. Every subsection MUST use Markdown level-3 headings:
   ### <Subsection Name>
5. Do NOT rename any section headings.
6. Use the exact section names provided below.
7. Generate every section, even if you need to make reasonable assumptions.
8. Never omit a requested section.
9. Use Markdown only.
10. Do NOT generate HTML tags such as <br>, <p>, <div>, <span>, or any other HTML. If multiple values are needed inside a table cell, separate them using semicolons (;) instead of line breaks.

## Startup Details
{startup_context}

## Retrieved Knowledge Base Context
{rag_context}

---

## Instructions

Generate the following market intelligence sections:

### 13. Competitor Analysis
Identify 4–6 direct and indirect competitors. For each:
- Company name and brief description
- Strengths and weaknesses
- Market share or funding status (if known)
- How this startup differentiates from them

Present as a structured comparison table followed by a narrative summary.

### 14. SWOT Analysis
Provide a comprehensive SWOT analysis:

**Strengths** (internal advantages)
- List 4–5 specific strengths

**Weaknesses** (internal limitations)
- List 3–4 honest weaknesses

**Opportunities** (external factors to exploit)
- List 4–5 market or timing opportunities

**Threats** (external risks)
- List 3–4 realistic threats

### 15. Go-To-Market Strategy
Detail the step-by-step launch and growth strategy:
- Phase 1: Pre-launch (target early adopters, beta testing)
- Phase 2: Launch (channels, messaging, partnerships)
- Phase 3: Scale (growth loops, expansion markets)

Include: marketing channels, customer acquisition strategy, pricing strategy, and distribution model.

---

Be data-informed and realistic. Avoid generic statements. Tailor analysis specifically to the startup's industry and country context.
