import sys
sys.path.append('.')
from neo4j import GraphDatabase

AURA_URI = "neo4j+s://f5fc20b1.databases.neo4j.io"
AURA_USER = "f5fc20b1"
AURA_PASSWORD = "liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE"

driver = GraphDatabase.driver(AURA_URI, auth=(AURA_USER, AURA_PASSWORD))

with driver.session() as session:
    res = session.run("MATCH (n {id: 'ND168_Art7_C10_a'}) RETURN properties(n) as props").single()
    props = res['props']
    with open('node_props.txt', 'w', encoding='utf-8') as f:
        for k, v in props.items():
            f.write(f"{k}: {v}\n")

driver.close()
