import sys
sys.path.append('.')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j+s://f5fc20b1.databases.neo4j.io', auth=('f5fc20b1', 'liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE'))

with driver.session() as session:
    res = session.run('MATCH (v:Violation) WHERE v.summary CONTAINS "tước quyền sử dụng" AND v.summary CONTAINS "Điều 7" RETURN v.id, v.summary')
    with open('search_suspension.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"{r['v.id']}: {r['v.summary']}\n")

driver.close()
