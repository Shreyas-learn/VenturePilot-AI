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


You are an expert startup consultant and business strategist. Generate a comprehensive business blueprint for the following startup.

## Startup Details
{startup_context}

## Retrieved Knowledge Base Context
{rag_context}

---

## Instructions

Generate ALL of the following sections in order. Use professional, concise business language suitable for investor presentations.

### 1. Executive Summary
A 3–4 sentence high-level overview of the startup, its mission, target market, and unique value.

### 2. Problem Statement
Clearly articulate the core problem this startup solves. Describe the pain point, who experiences it, and its scale.

### 3. Proposed Solution
Describe how this startup solves the problem. Be specific about the product or service and the mechanism of value delivery.

### 4. Vision & Mission
- **Vision:** Long-term aspirational future state (1–2 sentences).
- **Mission:** What the company does today to achieve that vision (1–2 sentences).

### 5. Target Customers
Define 2–3 specific customer personas including demographics, pain points, and buying behavior.

### 6. Value Proposition
State the unique value delivered to customers. Use the format: "We help [target customer] achieve [outcome] by [unique approach]."

### 7. Business Model Canvas
Provide all 9 blocks:
- Key Partners
- Key Activities
- Key Resources
- Value Propositions
- Customer Relationships
- Channels
- Customer Segments
- Cost Structure
- Revenue Streams

### 8. Revenue Model
List all revenue streams with pricing models (subscription, one-time, freemium, commission, etc.). Include estimated unit economics where possible.

---

Return the report as valid Markdown only.
Every main section must begin with a level-2 Markdown heading (##).
Do not use JSON, YAML, XML, or HTML.
