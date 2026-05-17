import sys
sys.path.append('.')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j+s://f5fc20b1.databases.neo4j.io', auth=('f5fc20b1', 'liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE'))

with driver.session() as session:
    res = session.run('MATCH (v:Violation) WHERE v.article = 7 AND v.clause = 11 RETURN v.id, v.summary')
    with open('clause_11_nodes.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"{r['v.id']}: {r['v.summary']}\n")

driver.close()
