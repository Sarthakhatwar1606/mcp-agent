"""Seed sample enterprise data into DuckDB (catalog) and ChromaDB (vector search)."""
import compat  # noqa: F401 — must be first, fixes Python 3.14 protobuf crash
import json
from pathlib import Path

import chromadb
import duckdb

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ── DuckDB catalog ─────────────────────────────────────────────────────────────
print("Seeding DuckDB catalog…")
db = duckdb.connect(str(DATA_DIR / "catalog.duckdb"))

db.execute("""
CREATE OR REPLACE TABLE employees (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR,
    department  VARCHAR,
    role        VARCHAR,
    salary      INTEGER,
    hire_date   DATE,
    location    VARCHAR
)
""")
db.execute("""
INSERT INTO employees VALUES
(1, 'Alice Johnson',  'Engineering',  'Senior Engineer',  130000, '2021-03-15', 'San Francisco'),
(2, 'Bob Smith',      'Data Science', 'ML Engineer',      145000, '2020-07-01', 'Remote'),
(3, 'Carol White',    'Engineering',  'Staff Engineer',   175000, '2019-01-20', 'New York'),
(4, 'David Lee',      'Product',      'Product Manager',  140000, '2022-06-10', 'Austin'),
(5, 'Eva Martinez',   'Data Science', 'Data Analyst',     105000, '2023-01-05', 'Chicago'),
(6, 'Frank Brown',    'Engineering',  'Junior Engineer',   95000, '2023-08-20', 'Remote'),
(7, 'Grace Kim',      'Design',       'UX Designer',      115000, '2021-11-30', 'Seattle'),
(8, 'Henry Davis',    'Sales',        'Account Executive', 90000, '2022-02-14', 'Boston')
""")

db.execute("""
CREATE OR REPLACE TABLE projects (
    id          INTEGER PRIMARY KEY,
    name        VARCHAR,
    team        VARCHAR,
    status      VARCHAR,
    budget      INTEGER,
    start_date  DATE,
    deadline    DATE
)
""")
db.execute("""
INSERT INTO projects VALUES
(1, 'Vector Search Platform',        'Engineering',  'In Progress', 500000, '2024-01-01', '2024-12-31'),
(2, 'Customer Analytics Dashboard',  'Data Science', 'Completed',   150000, '2023-06-01', '2023-12-15'),
(3, 'Mobile App v2.0',               'Engineering',  'Planning',    300000, '2024-03-01', '2024-09-30'),
(4, 'AI Recommendation Engine',      'Data Science', 'In Progress', 400000, '2024-02-01', '2024-11-30'),
(5, 'Enterprise SSO Integration',    'Engineering',  'Completed',    80000, '2023-09-01', '2024-01-31')
""")

db.execute("""
CREATE OR REPLACE TABLE sales (
    id          INTEGER PRIMARY KEY,
    product     VARCHAR,
    region      VARCHAR,
    quarter     VARCHAR,
    revenue     INTEGER,
    units_sold  INTEGER
)
""")
db.execute("""
INSERT INTO sales VALUES
(1, 'Enterprise Plan', 'North America', 'Q1 2024', 1200000,  48),
(2, 'Enterprise Plan', 'Europe',        'Q1 2024',  850000,  34),
(3, 'Pro Plan',        'North America', 'Q1 2024',  450000, 300),
(4, 'Enterprise Plan', 'North America', 'Q2 2024', 1400000,  56),
(5, 'Pro Plan',        'Asia Pacific',  'Q2 2024',  280000, 187),
(6, 'Enterprise Plan', 'Europe',        'Q2 2024',  920000,  37),
(7, 'Starter Plan',    'North America', 'Q2 2024',  120000, 800),
(8, 'Pro Plan',        'Europe',        'Q2 2024',  390000, 260)
""")

db.close()
print("  employees, projects, sales tables created.")

# ── ChromaDB knowledge base ───────────────────────────────────────────────────
print("Seeding ChromaDB knowledge base…")
client = chromadb.PersistentClient(path=str(DATA_DIR / "chromadb"))
col = client.get_or_create_collection("documents", metadata={"hnsw:space": "cosine"})

existing = col.get()
if existing["ids"]:
    col.delete(ids=existing["ids"])

docs = [
    "Our data governance policy requires all sensitive PII data to be tagged and access-controlled "
    "via the catalog before any ML model training. Violations trigger automatic alerts.",

    "The Vector Search Platform project uses HNSW (Hierarchical Navigable Small World) algorithm "
    "for approximate nearest-neighbor search, achieving sub-millisecond latency at 100M vectors.",

    "Q2 2024 earnings summary: Total ARR grew 42% YoY to $58M. Enterprise segment led growth "
    "with 120 new logos in North America. Churn rate improved to 3.2%.",

    "MCP (Model Context Protocol) enables AI agents to securely call enterprise tools through "
    "a standardized interface with full audit logging and role-based access control.",

    "LangGraph is an open-source framework for building stateful, multi-actor AI applications. "
    "It models agent workflows as directed graphs, enabling loops, branches, and persistence.",

    "Security policy update: All internal API calls must include a signed JWT token validated "
    "against the IAM service. Rate limits are 1000 req/min per service account.",

    "The AI Recommendation Engine improved click-through rates by 34% in A/B testing. "
    "It uses a two-tower neural network architecture trained on 6 months of interaction data.",

    "Engineering on-call runbook: For P0 incidents, page the on-call lead via PagerDuty, "
    "open a war room in Slack #incidents, and post a status update every 15 minutes.",
]

ids   = [f"doc_{i}" for i in range(len(docs))]
metas = [
    {"category": "governance",   "source": "policy-v3"},
    {"category": "engineering",  "source": "design-doc"},
    {"category": "business",     "source": "earnings-q2-2024"},
    {"category": "engineering",  "source": "architecture"},
    {"category": "engineering",  "source": "documentation"},
    {"category": "security",     "source": "policy-v7"},
    {"category": "ml",           "source": "experiment-results"},
    {"category": "operations",   "source": "runbook"},
]

col.add(documents=docs, ids=ids, metadatas=metas)
print(f"  {len(docs)} enterprise documents added.")
print("\nDone! Run:  streamlit run app.py")
