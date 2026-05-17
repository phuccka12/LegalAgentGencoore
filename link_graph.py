import json
import re
from neo4j import GraphDatabase
import sys

# Ep terminal hien thi tieng Viet
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# --- CONFIG ---
AURA_URI = "neo4j+s://f5fc20b1.databases.neo4j.io"
AURA_USER = "f5fc20b1"
AURA_PASSWORD = "liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE"

def link_authorities_to_violations():
    driver = GraphDatabase.driver(AURA_URI, auth=(AURA_USER, AURA_PASSWORD))
    
    # 1. Lay danh sach tat ca cac Authority tu Neo4j
    with driver.session() as session:
        print("[*] Dang lay danh sach cac quan chuc (Authorities)...")
        results = session.run("MATCH (a:Authority) RETURN a.id, a.title, a.raw_text, a.limit")
        
        for record in results:
            a_id = record["a.id"]
            a_title = record["a.title"]
            raw_text = record["a.raw_text"] or ""
            a_limit = record["a.limit"] or 0
            
            # 2. Dung Regex de tim cac chu "Dieu 6", "Dieu 7", "Dieu 8"...
            # Regex nay tim chu "Dieu" theo sau la mot hoac nhieu so
            articles = re.findall(r"Điều (\d+)", raw_text)
            articles = list(set([int(a) for a in articles])) # Loc trung va chuyen sang so
            
            if articles:
                print(f" -> Ong {a_title} co quyen phat cac Dieu: {articles}")
                
                # 3. Tao quan he [:CAN_SANCTION] voi dieu kien:
                # - So Dieu (article) phai khop
                # - Muc phat toi da (fine_max) phai nho hon hoac bang Han muc cua ong do (limit)
                #   (Ngoai tru cac ong cap cao co limit = 0 hoac rat lon)
                
                query = """
                MATCH (a:Authority {id: $a_id})
                MATCH (v:Violation)
                WHERE v.article IN $articles
                AND (a.limit = 0 OR v.fine_max <= a.limit)
                MERGE (a)-[r:CAN_SANCTION]->(v)
                RETURN count(r) as links
                """
                res = session.run(query, a_id=a_id, articles=articles)
                link_count = res.single()["links"]
                print(f"    [+] Da tao {link_count} ket noi [:CAN_SANCTION]")
    
    driver.close()
    print("\n[ thanh cong] Do thi da duoc ket noi chanh chit!")

if __name__ == "__main__":
    link_authorities_to_violations()
