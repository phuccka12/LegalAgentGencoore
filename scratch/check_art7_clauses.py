import sys
sys.path.append('.')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j+s://f5fc20b1.databases.neo4j.io', auth=('f5fc20b1', 'liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE'))

with driver.session() as session:
    res = session.run('MATCH (v:Violation) WHERE v.article = 7 RETURN v.id, v.clause ORDER BY v.clause DESC LIMIT 20')
    with open('article_7_clauses.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"{r['v.id']}: Clause {r['v.clause']}\n")

driver.close()
