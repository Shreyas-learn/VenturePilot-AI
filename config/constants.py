"""
config/constants.py — Static application constants.

These values are stable and do not depend on environment variables.
Edit here to add or remove options surfaced in the UI.
"""

APP_NAME = "VenturePilot AI"
APP_VERSION = "1.0.0"
APP_TAGLINE = "Your AI Co-Founder"
APP_MOTTO = "Build • Validate • Fund • Launch"

# ---------------------------------------------------------------------------
# Dropdown options
# ---------------------------------------------------------------------------

INDUSTRIES = [
    "AgriTech",
    "CleanTech / GreenTech",
    "EdTech",
    "FinTech",
    "FoodTech",
    "HealthTech / MedTech",
    "HRTech",
    "Legal Tech",
    "Logistics / Supply Chain",
    "Manufacturing",
    "Media & Entertainment",
    "PropTech / Real Estate",
    "RetailTech / E-Commerce",
    "SaaS / Enterprise Software",
    "Social Impact / NGO",
    "SpaceTech",
    "Telecom",
    "Travel & Hospitality",
    "Other",
]

COUNTRIES = [
    "India",
    "United States",
    "United Kingdom",
    "Canada",
    "Australia",
    "Singapore",
    "UAE",
    "Germany",
    "France",
    "Brazil",
    "Other",
]

STARTUP_STAGES = [
    "Idea Stage",
    "Validation / MVP",
    "Early Stage (Pre-Seed)",
    "Seed Stage",
    "Series A",
    "Growth Stage",
]

BUDGET_OPTIONS = [
    "Under ₹5 Lakhs",
    "₹5 – ₹25 Lakhs",
    "₹25 – ₹1 Crore",
    "₹1 – ₹5 Crore",
    "Above ₹5 Crore",
    "Not Sure Yet",
]

# ---------------------------------------------------------------------------
# Startup Readiness Score — dimension weights (total = 100)
# ---------------------------------------------------------------------------

SCORE_DIMENSIONS = {
    "Innovation": 20,
    "Market Need": 20,
    "Revenue Model": 15,
    "Competition": 15,
    "Scalability": 15,
    "Funding Potential": 15,
}

SCORE_TOTAL = sum(SCORE_DIMENSIONS.values())  # 100

# ---------------------------------------------------------------------------
# Report section labels (order defines display sequence)
# ---------------------------------------------------------------------------

REPORT_SECTIONS = [
    "Executive Summary",
    "Problem Statement",
    "Proposed Solution",
    "Vision & Mission",
    "Target Customers",
    "Value Proposition",
    "Business Model Canvas",
    "Revenue Model",
    "Competitor Analysis",
    "SWOT Analysis",
    "Estimated Budget",
    "Funding Opportunities",
    "Government Schemes",
    "Incubator Recommendations",
    "Go-To-Market Strategy",
    "12-Month Roadmap",
    "Risks & Mitigation",
    "Final Recommendation",
    "Investor Elevator Pitch",
    "Startup Readiness Score",
    "Immediate Next Steps",
]

# ---------------------------------------------------------------------------
# Knowledge base subfolder categories
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE_CATEGORIES = [
    "government",
    "funding",
    "business",
    "legal",
    "market",
]
