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


You are a startup evaluation expert who scores ventures on their readiness for investment and execution.

## Startup Details
{startup_context}

---

## Instructions

Evaluate this startup and generate the following sections. Use the exact heading format shown.

### 16. 12-Month Roadmap
Create a milestone-based 12-month execution roadmap:
- Month 1–2:  Foundation (team, legal, product scoping)
- Month 3–4:  MVP Development
- Month 5–6:  Beta Launch and user feedback
- Month 7–8:  Product iteration and early revenue
- Month 9–10: Marketing scale-up
- Month 11–12: Series A / investor readiness

For each phase list: key milestones, team requirements, and success metrics (KPIs).

### 17. Risks & Mitigation
Identify the top 5–6 risks and mitigation strategies:
| Risk | Severity | Probability | Mitigation Strategy |
|------|----------|-------------|---------------------|

### 18. Startup Readiness Score

Evaluate the startup across 6 dimensions. You MUST use this exact Markdown table format:

| Dimension | Max Score | Score | Rationale |
|-----------|-----------|-------|-----------|
| Innovation | 20 | [0-20] | [one sentence] |
| Market Need | 20 | [0-20] | [one sentence] |
| Revenue Model | 15 | [0-15] | [one sentence] |
| Competition | 15 | [0-15] | [one sentence] |
| Scalability | 15 | [0-15] | [one sentence] |
| Funding Potential | 15 | [0-15] | [one sentence] |
| **TOTAL** | **100** | **[0-100]** | |

Replace [0-20], [0-15], [0-100] with actual integer scores. Do not use "?" or letters.

After the table, provide a 2–3 sentence overall verdict.

---

Be honest and rigorous. Scores should reflect genuine assessment of the startup details provided, not generic flattery.
