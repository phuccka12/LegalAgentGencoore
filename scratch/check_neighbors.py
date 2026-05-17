import sys
sys.path.append('.')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j+s://f5fc20b1.databases.neo4j.io', auth=('f5fc20b1', 'liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE'))

with driver.session() as session:
    res = session.run('MATCH (v:Violation {id: "ND168_Art7_C10_a"})-[r]-(m) RETURN type(r), labels(m), properties(m) as props')
    with open('neighbors_detailed.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"Rel: {r['type(r)']} | Label: {r['labels(m)']} | ID: {r['props'].get('id')} | Title: {r['props'].get('title') or r['props'].get('name')}\n")

driver.close()
