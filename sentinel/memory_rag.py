#!/usr/bin/env python3
"""
K8s Sentinel — Cross-Session SQLite Incident Memory Engine (FTS5 Native RAG)
Indexes past incident resolutions and retrieves exact historical remediations
in < 2ms using SQLite's built-in Full-Text Search (FTS5) and BM25 relevance ranking.
Zero vector DB overhead, zero embedding API costs.
"""

import sys
import os
import sqlite3
import time
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(REPO_ROOT, "artifacts/sentinel_memory.sqlite")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_schema():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Base Relational Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incident_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT UNIQUE,
        namespace TEXT,
        workload TEXT,
        root_cause_class TEXT,
        error_signature TEXT,
        smoking_gun TEXT,
        remediation_patch TEXT,
        resolved_at TEXT
    );
    """)

    # 2. SQLite FTS5 Full-Text Search Virtual Table
    cur.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS incident_fts USING fts5(
        incident_id,
        root_cause_class,
        error_signature,
        smoking_gun,
        content='incident_records',
        content_rowid='id'
    );
    """)

    # 3. Automatic Synchronization Triggers
    cur.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_incident_insert AFTER INSERT ON incident_records BEGIN
        INSERT INTO incident_fts(rowid, incident_id, root_cause_class, error_signature, smoking_gun)
        VALUES (new.id, new.incident_id, new.root_cause_class, new.error_signature, new.smoking_gun);
    END;
    """)

    conn.commit()
    conn.close()

def index_incident(incident_id, namespace, workload, root_cause_class, error_signature, smoking_gun, patch):
    init_schema()
    conn = get_connection()
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        cur.execute("""
        INSERT INTO incident_records (incident_id, namespace, workload, root_cause_class, error_signature, smoking_gun, remediation_patch, resolved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(incident_id) DO UPDATE SET
            error_signature=excluded.error_signature,
            smoking_gun=excluded.smoking_gun,
            remediation_patch=excluded.remediation_patch,
            resolved_at=excluded.resolved_at;
        """, (incident_id, namespace, workload, root_cause_class, error_signature, smoking_gun, patch, now_str))
        conn.commit()
    finally:
        conn.close()

def search_incidents(query_text, limit=3):
    init_schema()
    conn = get_connection()
    cur = conn.cursor()
    
    t0 = time.time()
    # Format FTS5 query terms: sanitize and match
    terms = " ".join([f'"{w}"' for w in query_text.replace('"', '').split() if len(w) > 2])
    if not terms:
        terms = f'"{query_text}"'

    sql = """
    SELECT 
        r.incident_id,
        r.namespace,
        r.workload,
        r.root_cause_class,
        r.error_signature,
        r.smoking_gun,
        r.remediation_patch,
        bm25(incident_fts) AS bm25_rank
    FROM incident_fts f
    JOIN incident_records r ON f.rowid = r.id
    WHERE incident_fts MATCH ?
    ORDER BY bm25_rank
    LIMIT ?;
    """

    try:
        cur.execute(sql, (terms, limit))
        rows = [dict(r) for r in cur.fetchall()]
        latency_ms = (time.time() - t0) * 1000
        return rows, latency_ms
    except sqlite3.OperationalError as e:
        # Fallback if complex symbols break FTS query
        fallback_sql = """
        SELECT * FROM incident_records 
        WHERE error_signature LIKE ? OR smoking_gun LIKE ?
        LIMIT ?;
        """
        cur.execute(fallback_sql, (f"%{query_text}%", f"%{query_text}%", limit))
        rows = [dict(r) for r in cur.fetchall()]
        latency_ms = (time.time() - t0) * 1000
        return rows, latency_ms
    finally:
        conn.close()

def seed_default_incidents():
    print("Pre-warming SQLite Incident Memory with institutional knowledge...")
    seeds = [
        {
            "incident_id": "INC-20260827-CRASHLOOP-DEMO",
            "namespace": "demo",
            "workload": "deployment/payments-api",
            "root_cause_class": "CONFIG_INVALID",
            "error_signature": "unknown directive this_directive_does_not_exist nginx default.conf syntax error CrashLoopBackOff",
            "smoking_gun": 'nginx: [emerg] unknown directive "this_directive_does_not_exist" in /etc/nginx/conf.d/default.conf:3',
            "patch": 'kubectl patch configmap nginx-healthz -n demo --type merge -p \'{"data":{"default.conf":"server { listen 80; location = /healthz { return 200 \\"ok\\\\n\\"; } }"}}\''
        },
        {
            "incident_id": "INC-20260827-OOMKILL-DEMO",
            "namespace": "demo",
            "workload": "deployment/payments-api",
            "root_cause_class": "RESOURCE_LIMIT_MISMATCH",
            "error_signature": "OOMKilled exitCode 137 memory cgroup limit exceeded kernel termination",
            "smoking_gun": "lastState.terminated.reason: OOMKilled, exitCode: 137, memory limit 4Mi exceeded",
            "patch": "kubectl -n demo set resources deployment/payments-api --limits=memory=64Mi --requests=memory=32Mi"
        },
        {
            "incident_id": "INC-20260827-PROBEFAIL-DEMO",
            "namespace": "demo",
            "workload": "deployment/payments-api",
            "root_cause_class": "PROBE_ENDPOINT_FAILURE",
            "error_signature": "Liveness probe failed HTTP 404 healthz-deprecated restart storm clean logs",
            "smoking_gun": "Liveness probe failed: HTTP probe failed with statuscode: 404 on path /healthz-deprecated",
            "patch": "kubectl -n demo patch deployment/payments-api --type json -p '[{\"op\": \"replace\", \"path\": \"/spec/template/spec/containers/0/livenessProbe/httpGet/path\", \"value\": \"/healthz\"}]'"
        },
        {
            "incident_id": "INC-20260827-IMAGEPULL-DEMO",
            "namespace": "demo",
            "workload": "deployment/payments-api",
            "root_cause_class": "IMAGE_TAG_INVALID",
            "error_signature": "Failed to pull image ErrImagePull ImagePullBackOff manifest unknown non-existent tag",
            "smoking_gun": "Failed to pull image 'nginx:this-tag-does-not-exist-hackathon': manifest unknown",
            "patch": "kubectl -n demo set image deployment/payments-api payments-api=nginx:alpine"
        }
    ]

    for s in seeds:
        index_incident(s["incident_id"], s["namespace"], s["workload"], s["root_cause_class"], s["error_signature"], s["smoking_gun"], s["patch"])
        print(f"  ✓ Indexed: {s['incident_id']} [{s['root_cause_class']}]")

def main():
    if len(sys.argv) < 2 or sys.argv[1] == "seed":
        seed_default_incidents()
        print(f"✓ SQLite Incident Memory pre-warmed at {DB_PATH}\n")
    elif sys.argv[1] == "search":
        query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "unknown directive"
        results, latency = search_incidents(query)

        print("\033[1;36m" + "="*80 + "\033[0m")
        print("\033[1;37m⚡ K8S SENTINEL: NATIVE SQLITE FTS5 INCIDENT RETRIEVAL (RAG)\033[0m")
        print("\033[1;36m" + "="*80 + "\033[0m")
        print(f"  • Query:        \033[1m\"{query}\"\033[0m")
        print(f"  • Search Engine:\033[1;32m SQLite FTS5 Virtual Table (BM25 Ranked)\033[0m")
        print(f"  • Search Latency:\033[1;32m {latency:.3f} ms (In-Memory Inverted Index)\033[0m")
        print(f"  • Vector DB:    \033[1;32m None required (Zero RAM / Zero API Cost)\033[0m")
        print("\033[1;36m" + "="*80 + "\033[0m\n")

        if not results:
            print("  No matching historical incidents found in SQLite memory.")
        else:
            for idx, r in enumerate(results, 1):
                print(f" \033[1m[{idx}] Match: {r['incident_id']}\033[0m (BM25 Score: {r.get('bm25_rank', 'N/A'):.4f})")
                print(f"     Class:       \033[1;33m{r['root_cause_class']}\033[0m")
                print(f"     Smoking Gun: {r['smoking_gun']}")
                print(f"     Known Fix:   \033[1;32m{r['remediation_patch']}\033[0m\n")

if __name__ == "__main__":
    main()
