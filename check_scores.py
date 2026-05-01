import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "niit_design_automation.db")
con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
cur = con.cursor()

print("\n=== All Design Scores ===")
cur.execute("""
  SELECT d.title, s.overall_score, s.requirement_coverage_score,
         s.template_completeness_score, s.technical_consistency_score,
         s.missing_requirements, s.contradictions
  FROM scorecard s
  JOIN designdocument d ON d.id = s.design_document_id
  ORDER BY s.overall_score DESC
""")
rows = cur.fetchall()
print(f"Found {len(rows)} design(s).\n")
for row in rows:
    r = dict(row)
    print(f"  Title            : {r['title']}")
    print(f"  Overall Score    : {r['overall_score']}")
    print(f"  Req Coverage     : {r['requirement_coverage_score']}")
    print(f"  Template Complete: {r['template_completeness_score']}")
    print(f"  Tech Consistency : {r['technical_consistency_score']}")
    print(f"  Missing Reqs     : {r['missing_requirements']}")
    print(f"  Contradictions   : {r['contradictions']}")
    print()

print("=== Designs with Missing Requirements ===")
cur.execute("""
  SELECT d.title, s.missing_requirements
  FROM scorecard s
  JOIN designdocument d ON d.id = s.design_document_id
  WHERE s.missing_requirements != '[]'
""")
rows = cur.fetchall()
print(f"Found {len(rows)} design(s) with missing requirements.\n")
for row in rows:
    r = dict(row)
    print(f"  Title   : {r['title']}")
    print(f"  Missing : {r['missing_requirements']}")
    print()

print("=== Average Score by Design Status ===")
cur.execute("""
  SELECT d.status, ROUND(AVG(s.overall_score), 1) AS avg_score, COUNT(*) AS count
  FROM scorecard s
  JOIN designdocument d ON d.id = s.design_document_id
  GROUP BY d.status
""")
rows = cur.fetchall()
for row in rows:
    r = dict(row)
    print(f"  Status: {r['status']:35s}  Avg Score: {r['avg_score']}  Count: {r['count']}")

print("\n=== Rejected Designs vs Their Scores (Accuracy Gap) ===")
cur.execute("""
  SELECT d.title, s.overall_score, r.reviewer_name, r.comments
  FROM reviewtask r
  JOIN designdocument d ON d.id = r.design_document_id
  JOIN scorecard s ON s.design_document_id = d.id
  WHERE r.status = 'REJECTED'
  ORDER BY s.overall_score DESC
""")
rows = cur.fetchall()
print(f"Found {len(rows)} rejected review(s).\n")
for row in rows:
    r = dict(row)
    print(f"  Title         : {r['title']}")
    print(f"  Overall Score : {r['overall_score']}")
    print(f"  Reviewer      : {r['reviewer_name']}")
    print(f"  Comments      : {r['comments']}")
    print()

con.close()
print("Done.")
