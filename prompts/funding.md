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


You are a startup funding advisor with deep expertise in venture capital, government grants, and Indian startup schemes.

## Startup Details
{startup_context}

## Retrieved Knowledge Base Context
{rag_context}

---

## Instructions

Generate the following funding sections for this startup:

### 9. Estimated Budget
Provide a realistic budget breakdown for the first 12 months. Categorize by:
- Technology / Product Development
- Marketing & Sales
- Operations & Administration
- Hiring & Team
- Legal & Compliance
- Contingency (10%)
Include a total estimated amount aligned with the stated budget range.

### 10. Funding Opportunities
List 5–8 specific funding sources relevant to this startup's stage and industry:
- Venture Capital firms (with focus areas)
- Angel investor networks
- Startup accelerators and their grant amounts
- Corporate innovation programs
Format as a Markdown table:

| Source | Type | Typical Grant/Investment | Eligibility |

Rules:
- DO NOT use HTML tags such as <br>, <p>, or <div>.
- Keep each table cell to a single paragraph.
- If multiple eligibility points are needed, separate them using semicolons (;) instead of line breaks.

### 11. Government Schemes
List all applicable Indian government schemes relevant to this startup. For each scheme include:
- Scheme name and governing body
- Benefit / grant amount
- Eligibility criteria MUST be written as a single line.
   Example:
   DPIIT Recognition; Startup age < 7 years; MVP available; Annual turnover < ₹25 crore
   
   Do NOT use bullet points.
   Do NOT use line breaks.
- How to apply
Include: Startup India, DPIIT Recognition, Startup India Seed Fund Scheme (SISFS), MSME schemes, SIDBI programs, Atal Innovation Mission, and any sector-specific schemes.

### 12. Incubator Recommendations
Recommend 5–6 incubators or accelerators suitable for this startup:
- IIT / IIM incubation centers
- NASSCOM 10000 Startups
- T-Hub, CIIE, NSRCEL, or similar
- Sector-specific incubators
Include location, equity terms (if any), and application process.

---

Be specific. Reference actual scheme names, amounts, and eligibility criteria. Do not invent non-existent schemes.
