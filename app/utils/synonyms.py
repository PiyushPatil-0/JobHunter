"""
Synonym / alias groups used to make preference matching resilient to
abbreviations, spelling variants, and equivalent phrasing across
skills, roles, and locations - e.g. "java developer" vs "java backend
developer", "bangalore" vs "bengaluru", "bcom" vs "bachelor of
commerce", ".NET" vs "DotNet".

IMPORTANT - this is a starter set, not a complete dictionary:
No static list can cover every synonym in every job category, so two
things are combined here:

1. SYNONYM_GROUPS below - precise, curated equivalences across IT,
   commerce/finance, sales & marketing, HR, operations, customer
   support, design, healthcare, legal, manufacturing, degrees, and
   locations. Add new groups any time you notice a real miss; nothing
   else needs to change.
2. `fuzzy_match()` - a safety net for terms that AREN'T in any group
   yet (typos, minor spelling variants like "Bengalooru" or
   "Developor"). It only fires when no exact/synonym match was found,
   and only for reasonably long words, to keep the false-positive risk
   low. It will not invent semantic synonyms ("cook" won't match
   "chef") - it only catches near-identical spellings.

Note on short acronyms: a few groups (e.g. "dotnet" <-> "net", "ca" <->
"chartered accountant") map a multi-letter skill to a very common short
word. That's intentional - it's needed to match real postings ("Build
services using .NET") - but it does mean a user who adds that exact
skill could occasionally see an unrelated job that happens to use the
short word in an ordinary sentence. If that becomes noisy in practice,
trim the offending variant from its group below.
"""

from __future__ import annotations

import difflib
import re

# --- tech / IT ---------------------------------------------------------
_TECH_GROUPS: list[set[str]] = [
    {"javascript", "js"},
    {"typescript", "ts"},
    {"react", "reactjs", "react js", "react.js"},
    {"react native", "reactnative"},
    {"node", "nodejs", "node js", "node.js"},
    {"dotnet", ".net", "dot net", "asp.net", "asp net", "asp dot net"},
    {"golang", "go lang"},
    {"aws", "amazon web services"},
    {"gcp", "google cloud platform", "google cloud"},
    {"azure", "microsoft azure"},
    {"ml", "machine learning"},
    {"ai", "artificial intelligence"},
    {"nlp", "natural language processing"},
    {"ui", "user interface"},
    {"ux", "user experience"},
    {"ui ux", "ui/ux", "uiux"},
    {
        "ci cd",
        "cicd",
        "continuous integration continuous deployment",
        "continuous integration continuous delivery",
    },
    {"k8s", "kubernetes"},
    {"postgres", "postgresql"},
    {"mongo", "mongodb"},
    {"spring boot", "springboot"},
    {"rest api", "restful api", "restapi"},
    {"oop", "object oriented programming"},
    {"dsa", "data structures and algorithms", "data structure and algorithm"},
    {"qa", "quality assurance"},
    {"sql server", "mssql", "ms sql", "microsoft sql server"},
    {"power bi", "powerbi"},
    {"sre", "site reliability engineer", "site reliability engineering"},
    {"devops", "dev ops"},
    {
        "sde",
        "software development engineer",
        "swe",
        "software engineer",
        "software developer",
    },
    {"sdet", "software development engineer in test"},
    {"backend", "back end", "server side"},
    {"frontend", "front end", "client side"},
    {"fullstack", "full stack"},
    {"ios developer", "ios engineer"},
    {"android developer", "android engineer"},
    {"flutter", "flutter dart"},
    {"cyber security", "cybersecurity", "infosec", "information security"},
    {"penetration testing", "pen testing", "pentest", "pentesting"},
    {"data engineer", "data engineering"},
    {"etl", "extract transform load"},
    {"data warehouse", "dwh", "datawarehouse"},
    {"embedded systems", "embedded systems engineer", "embedded engineer"},
    {"salesforce developer", "sfdc developer"},
    {"crm", "customer relationship management"},
    {"erp", "enterprise resource planning"},
    {"sap abap", "abap"},
]

# --- commerce / finance / accounts --------------------------------------
_COMMERCE_GROUPS: list[set[str]] = [
    {"ca", "chartered accountant"},
    {"cma", "cost and management accountant", "certified management accountant"},
    {"cpa", "certified public accountant"},
    {"bcom", "b com", "b.com", "bachelor of commerce"},
    {"mcom", "m com", "m.com", "master of commerce"},
    {"mba finance", "mba in finance"},
    {"accounts", "accounting", "accountancy"},
    {"accounts payable", "ap"},
    {"accounts receivable", "ar"},
    {"gst", "goods and services tax"},
    {"tds", "tax deducted at source"},
    {"tally", "tally erp", "tally erp9", "tally erp 9", "tally prime"},
    {"bookkeeping", "book keeping"},
    {"payroll", "payroll processing"},
    {"audit", "auditing"},
    {"ifrs", "international financial reporting standards"},
    {"gaap", "generally accepted accounting principles"},
    {"sap fico", "sap fi co", "sap finance"},
    {"equity research", "equity analysis"},
    {"financial analyst", "finance analyst"},
    {"investment banking", "ib"},
]

# --- sales & marketing ----------------------------------------------------
_SALES_MARKETING_GROUPS: list[set[str]] = [
    {"sales executive", "sales associate", "sales representative"},
    {"business development", "bd", "business development executive", "bde"},
    {"digital marketing", "online marketing"},
    {"seo", "search engine optimization", "search engine optimisation"},
    {"sem", "search engine marketing"},
    {"smm", "social media marketing"},
    {"ppc", "pay per click"},
    {"telecalling", "tele calling", "telesales", "tele sales"},
    {"field sales", "on field sales"},
    {"inside sales", "tele sales"},
    {"key account manager", "kam"},
    {"content marketing", "content writing"},
    {"performance marketing", "growth marketing"},
]

# --- HR & recruitment -------------------------------------------------
_HR_GROUPS: list[set[str]] = [
    {"hr", "human resources"},
    {"hr executive", "human resources executive"},
    {"hr generalist", "human resources generalist"},
    {"hrbp", "hr business partner", "human resources business partner"},
    {"talent acquisition", "recruitment", "recruiting", "ta"},
    {"payroll executive", "payroll specialist"},
    {"l&d", "learning and development", "l and d"},
]

# --- operations, logistics & supply chain -----------------------------
_OPERATIONS_GROUPS: list[set[str]] = [
    {"supply chain", "scm", "supply chain management"},
    {"warehouse", "warehousing"},
    {"logistics", "logistics management"},
    {"procurement", "purchasing"},
    {"inventory management", "stock management"},
    {"operations executive", "ops executive"},
]

# --- customer support / BPO --------------------------------------------
_SUPPORT_GROUPS: list[set[str]] = [
    {"bpo", "business process outsourcing"},
    {"kpo", "knowledge process outsourcing"},
    {"customer support", "customer service", "customer care"},
    {"technical support", "tech support"},
    {"voice process", "voice based process"},
    {"non voice process", "non voice based process", "chat process"},
]

# --- design / creative --------------------------------------------------
_DESIGN_GROUPS: list[set[str]] = [
    {"graphic design", "graphic designer", "graphic designing"},
    {"ui designer", "ui ux designer"},
    {"video editing", "video editor"},
    {"motion graphics", "motion design"},
]

# --- legal ---------------------------------------------------------------
_LEGAL_GROUPS: list[set[str]] = [
    {"llb", "bachelor of laws", "bachelor of legislative law"},
    {"advocate", "lawyer", "legal counsel"},
    {"legal executive", "legal associate"},
]

# --- manufacturing / mechanical / electrical -----------------------------
_MANUFACTURING_GROUPS: list[set[str]] = [
    {"mechanical engineer", "mech engineer"},
    {"production engineer", "manufacturing engineer"},
    {"quality control", "qc"},
    {"quality assurance engineer", "qa engineer"},
    {"plc programming", "plc scada", "scada"},
    {"cad", "computer aided design"},
    {"cnc operator", "cnc machinist"},
]

# --- education / academic -------------------------------------------------
_EDUCATION_GROUPS: list[set[str]] = [
    {"teacher", "educator", "faculty"},
    {"assistant professor", "asst professor"},
    {"academic counselor", "academic counsellor"},
]

# --- healthcare (kept conservative - "MD" etc are too ambiguous to alias) -
_HEALTHCARE_GROUPS: list[set[str]] = [
    {"gnm", "general nursing and midwifery"},
    {"bpt", "bachelor of physiotherapy"},
    {"staff nurse", "nursing staff"},
    {"pharmacist", "pharmacy executive"},
]

# --- degrees / qualifications ---------------------------------------------
_DEGREE_GROUPS: list[set[str]] = [
    {"btech", "b.tech", "bachelor of technology"},
    {"be", "b.e", "bachelor of engineering"},
    {"mtech", "m.tech", "master of technology"},
    {"mba", "master of business administration"},
    {"bba", "bachelor of business administration"},
    {"mca", "master of computer applications"},
    {"bca", "bachelor of computer applications"},
    {"phd", "doctorate", "doctor of philosophy"},
    {"bsc", "b.sc", "bachelor of science"},
    {"msc", "m.sc", "master of science"},
]

# --- employment / experience phrasing --------------------------------------
_EMPLOYMENT_GROUPS: list[set[str]] = [
    {"fresher", "entry level", "new grad", "graduate trainee"},
    {"work from home", "remote", "wfh"},
    {"work from office", "wfo", "onsite", "on site"},
]

# --- locations (India-focused; extend as your user base needs) -------------
_LOCATION_GROUPS: list[set[str]] = [
    {"bangalore", "bengaluru"},
    {"gurgaon", "gurugram"},
    {"mumbai", "bombay"},
    {"pune", "poona"},
    {"delhi", "new delhi", "ncr", "delhi ncr"},
    {"chennai", "madras"},
    {"kolkata", "calcutta"},
    {"noida", "greater noida"},
    {"vizag", "visakhapatnam"},
    {"trivandrum", "thiruvananthapuram"},
    {"hyderabad", "secunderabad"},
    {"ahmedabad", "amdavad"},
    {"vadodara", "baroda"},
    {"mysore", "mysuru"},
    {"kochi", "cochin"},
    {"varanasi", "banaras", "kashi"},
    {"prayagraj", "allahabad"},
    {"surat", "suratcity"},
    {"jaipur", "jaipur city"},
    {"lucknow", "lakhnau"},
    {"nagpur", "nagpur city"},
    {"indore", "indore city"},
    {"bhopal", "bhopal city"},
    {"patna", "patna city"},
    {"coimbatore", "kovai"},
    {"nashik", "nasik"},
    {"faridabad", "faridabad city"},
    {"ghaziabad", "ghaziabad city"},
    {"chandigarh", "chandigarh city"},
    {"guwahati", "gauhati"},
    {"bhubaneswar", "bhubaneshwar"},
    {"remote", "work from home", "wfh"},
]

SYNONYM_GROUPS: list[set[str]] = (
    _TECH_GROUPS
    + _COMMERCE_GROUPS
    + _SALES_MARKETING_GROUPS
    + _HR_GROUPS
    + _OPERATIONS_GROUPS
    + _SUPPORT_GROUPS
    + _DESIGN_GROUPS
    + _LEGAL_GROUPS
    + _MANUFACTURING_GROUPS
    + _EDUCATION_GROUPS
    + _HEALTHCARE_GROUPS
    + _DEGREE_GROUPS
    + _EMPLOYMENT_GROUPS
    + _LOCATION_GROUPS
)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def normalize_phrase(text: str) -> str:
    """
    Lower-cased, alphanumeric-only tokens joined by single spaces and
    padded with a leading/trailing space, e.g. "Spring-Boot!" ->
    " spring boot ".

    The padding is what makes `phrase in normalize_phrase(other)` a
    safe, word-boundary-respecting containment check: "java" never
    matches inside "javascript" because " java " is not a substring of
    " javascript ", but "spring" does correctly match inside
    "spring boot" because " spring " is a substring of " spring boot ".
    """
    tokens = _tokenize(text)
    return " " + " ".join(tokens) + " " if tokens else ""


def _build_index() -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for group in SYNONYM_GROUPS:
        normalised_group = {normalize_phrase(phrase) for phrase in group}
        for phrase in normalised_group:
            index.setdefault(phrase, set()).update(normalised_group)
    return index


# phrase (normalised) -> every normalised phrase considered equivalent to it
_PHRASE_TO_GROUP: dict[str, set[str]] = _build_index()


def expand(term: str) -> set[str]:
    """
    Every normalised phrase considered equivalent to `term`, including
    `term` itself. Callers check a job's normalised text for any of
    these, instead of just the literal term.
    """
    own = normalize_phrase(term)
    if not own:
        return set()
    return _PHRASE_TO_GROUP.get(own, {own})


# Words this short are excluded from fuzzy matching - a near-miss on a
# 3-letter word is far too likely to be a coincidence (e.g. "sap" vs
# "spa"), so fuzzy matching only kicks in for longer, more distinctive
# words where a near-identical spelling really does mean "same word".
_FUZZY_MIN_WORD_LENGTH = 5
_FUZZY_MIN_RATIO = 0.84


def fuzzy_match(haystack_text: str, term: str) -> bool:
    """
    Safety net for spelling variants that aren't in any synonym group
    yet - e.g. a job listing "Bengalooru" (typo) against a preference
    for "Bengaluru", or "Developor" against "Developer".

    Only compares single words of reasonable length, and only accepts
    near-identical matches (ratio >= 0.84, roughly "one or two
    characters different"). This deliberately will NOT catch different
    words that merely relate to each other ("chef" vs "cook") - that
    needs an explicit synonym group above, not fuzzy matching.
    """
    term_tokens = [t for t in _tokenize(term) if len(t) >= _FUZZY_MIN_WORD_LENGTH]
    if not term_tokens:
        return False

    haystack_tokens = [t for t in _tokenize(haystack_text) if len(t) >= _FUZZY_MIN_WORD_LENGTH]
    if not haystack_tokens:
        return False

    for term_token in term_tokens:
        matches = difflib.get_close_matches(
            term_token, haystack_tokens, n=1, cutoff=_FUZZY_MIN_RATIO
        )
        if matches:
            return True
    return False
