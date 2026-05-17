import sys
sys.path.append('.')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j+s://f5fc20b1.databases.neo4j.io', auth=('f5fc20b1', 'liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE'))

with driver.session() as session:
    res = session.run('MATCH (v {id: "ND168_Art7_C11_c"}) RETURN v.summary, v.license_suspension_days')
    with open('temp_sanction.txt', 'w', encoding='utf-8') as f:
        for r in res:
            f.write(f"Summary: {r['v.summary']}\nSuspension: {r['v.license_suspension_days']}\n")

driver.close()
