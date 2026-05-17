import sys
sys.path.append('.')
from neo4j import GraphDatabase

# Neo4j connection details
AURA_URI = "neo4j+s://f5fc20b1.databases.neo4j.io"
AURA_USER = "f5fc20b1"
AURA_PASSWORD = "liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE"

driver = GraphDatabase.driver(AURA_URI, auth=(AURA_USER, AURA_PASSWORD))

def enrich_criminal_nodes():
    print("[*] Connecting to Neo4j to enrich Criminal Law nodes...")
    with driver.session() as session:
        # 1. Create the Law node for BLHS
        print("[*] Creating Law node for BLHS 2015...")
        session.run("""
        MERGE (l:Law {id: 'BLHS_2015'})
        ON CREATE SET l.title = 'Bo luat Hinh su 2015 (Sua doi 2017)', l.publisher = 'Quoc hoi Viet Nam'
        ON MATCH SET l.title = 'Bo luat Hinh su 2015 (Sua doi 2017)'
        """)

        # 2. Create CriminalViolation nodes for Dieu 260, 261, 262
        print("[*] Creating CriminalViolation nodes...")
        criminal_nodes = [
            # Dieu 260: Toi vi pham quy dinh ve tham gia giao thong duong bo
            {
                "id": "BLHS_Art260_C1", "article": "260", "clause": "1",
                "summary": "Vi pham quy dinh ve tham gia giao thong duong bo gay thiet hai cho nguoi khac (lam chet 01 nguoi, gay thuong tich hoac gay ton hai cho suc khoe cua 01 nguoi voi ty le ton thuong co the 61% tro len, hoac gay thiet hai tai san tu 100 trieu den duoi 500 trieu dong).",
                "punishment": "Phat tien tu 30,000,000 den 100,000,000 VND, phat cai tao khong giam giu den 03 nam hoac phat tu tu 01 nam den 05 nam."
            },
            {
                "id": "BLHS_Art260_C2", "article": "260", "clause": "2",
                "summary": "Pham toi thuoc mot trong cac truong hop tang nang: Khong co giay phep lai xe; Su dung ruou, bia ma trong mau hoac hoi tho co nong do con vuot qua muc quy dinh, hoac su dung chat ma tuy; Gay tai nan roi bo chay de tron tranh trach nhiem; Lam chet 02 nguoi; Thiet hai tai san tu 500 trieu den duoi 1.5 ty dong.",
                "punishment": "Phat tu tu 03 nam den 10 nam."
            },
            {
                "id": "BLHS_Art260_C3", "article": "260", "clause": "3",
                "summary": "Pham toi gay hau qua dac biet nghiem trong: Lam chet 03 nguoi tro len; Gay thuong tich cho 03 nguoi tro len voi tong ty le ton thuong co the 200% tro len; Gay thiet hai tai san 1.5 ty dong tro len.",
                "punishment": "Phat tu tu 07 nam den 15 nam."
            },
            # Dieu 261: Toi can tro giao thong duong bo
            {
                "id": "BLHS_Art261_C1", "article": "261", "clause": "1",
                "summary": "Dat chuong ngai vat, dai vat sac nhon, dao boi, san lap duong trai phep, do chat thai hoac thuc hien cac hanh vi can tro giao thong khac gay thiet hai cho nguoi khac (lam chet 01 nguoi, thuong tich >= 61%, hoac thiet hai tai san >= 100 trieu dong).",
                "punishment": "Phat tien tu 30,000,000 den 100,000,000 VND, phat cai tao khong giam giu den 03 nam hoac phat tu tu 06 thang den 03 nam."
            },
            {
                "id": "BLHS_Art261_C2", "article": "261", "clause": "2",
                "summary": "Pham toi can tro giao thong duong bo gay hau qua nghiem trong hon: Tai deo, doc, duong vong, duong cao toc; Lam chet 02 nguoi; Thiet hai tai san tu 500 trieu den duoi 1.5 ty dong.",
                "punishment": "Phat tu tu 02 nam den 07 nam."
            },
            # Dieu 262: Toi dieu dong hoac cho phep nguoi khong du dieu kien dieu khien phuong tien
            {
                "id": "BLHS_Art262_C1", "article": "262", "clause": "1",
                "summary": "Cho phep hoac dieu dong nguoi khong co giay phep lai xe, co su dung ruou bia vuot qua nong do con quy dinh, ma tuy hoac khong du dieu kien suc khoe dieu khien phuong tien gay tai nan nghiem trong (lam chet 01 nguoi, hoac thiet hai tai san >= 100 trieu dong).",
                "punishment": "Phat tien tu 10,000,000 den 50,000,000 VND hoac phat cai tao khong giam giu den 03 nam."
            },
            {
                "id": "BLHS_Art262_C2", "article": "262", "clause": "2",
                "summary": "Giao xe cho nguoi khong du dieu kien gay hau qua nghiem trong hon: Lam chet 02 nguoi; Thiet hai tai san tu 500 trieu den duoi 1.5 ty dong.",
                "punishment": "Phat tien tu 50,000,000 den 200,000,000 VND hoac phat tu tu 01 nam den 03 nam."
            }
        ]

        for node in criminal_nodes:
            session.run("""
            MERGE (c:CriminalViolation {id: $id})
            ON CREATE SET c.article = $article, c.clause = $clause, c.summary = $summary, c.punishment = $punishment, c.type = 'Hinh su'
            ON MATCH SET c.summary = $summary, c.punishment = $punishment
            """, **node)
            
            # Link to the Law node
            session.run("""
            MATCH (l:Law {id: 'BLHS_2015'}), (c:CriminalViolation {id: $id})
            MERGE (l)-[:HAS_ARTICLE]->(c)
            """, id=node["id"])

        print("[SUCCESS] Created all CriminalViolation nodes and linked to BLHS_2015.")

        # 5. Connect Decree 168 Violation nodes to BLHS CriminalViolation nodes (ESCALATES_TO)
        print("[*] Creating ESCALATES_TO relationships...")
        
        # Connection 1: Loi gay tai nan hanh chinh -> BLHS Dieu 260
        res1 = session.run("""
        MATCH (admin:Violation)
        WHERE (toLower(admin.summary) CONTAINS 'tai nan' OR toLower(admin.summary) CONTAINS 'tai nạn' OR admin.id CONTAINS 'C10')
        MATCH (crim:CriminalViolation {id: 'BLHS_Art260_C1'})
        MERGE (admin)-[r:ESCALATES_TO {condition: 'Gay hau qua lam chet nguoi, ton thuong suc khoe >= 61%, hoac thiet hai tai san >= 100 trieu dong'}]->(crim)
        RETURN count(r) as count
        """).single()
        print(f"   [+] Linked {res1['count']} accident violations to BLHS Art 260 Clause 1.")

        res2 = session.run("""
        MATCH (admin:Violation)
        WHERE (toLower(admin.summary) CONTAINS 'tai nan' OR toLower(admin.summary) CONTAINS 'tai nạn' OR admin.id CONTAINS 'C10')
          AND (toLower(admin.summary) CONTAINS 'con' OR toLower(admin.summary) CONTAINS 'cồn' OR toLower(admin.summary) CONTAINS 'ruou' OR toLower(admin.summary) CONTAINS 'rượu' OR toLower(admin.summary) CONTAINS 'ma tuy' OR toLower(admin.summary) CONTAINS 'ma túy' OR toLower(admin.summary) CONTAINS 'chay tron' OR toLower(admin.summary) CONTAINS 'bỏ chạy')
        MATCH (crim:CriminalViolation {id: 'BLHS_Art260_C2'})
        MERGE (admin)-[r:ESCALATES_TO {condition: 'Gay tai nan trong tinh trang say xin/ma tuy, khong bang lai, hoac bo chay sau tai nan'}]->(crim)
        RETURN count(r) as count
        """).single()
        print(f"   [+] Linked {res2['count']} severe/aggravated accident violations to BLHS Art 260 Clause 2.")

        # Connection 2: Loi can tro giao thong (dinh, vat can, san lap duong...) -> BLHS Dieu 261
        res3 = session.run("""
        MATCH (admin:Violation)
        WHERE toLower(admin.summary) CONTAINS 'dinh' OR toLower(admin.summary) CONTAINS 'đinh'
           OR toLower(admin.summary) CONTAINS 'vat sac' OR toLower(admin.summary) CONTAINS 'vật sắc'
           OR toLower(admin.summary) CONTAINS 'chuong ngai' OR toLower(admin.summary) CONTAINS 'chướng ngại'
           OR toLower(admin.summary) CONTAINS 'dao boi' OR toLower(admin.summary) CONTAINS 'đào bới'
           OR toLower(admin.summary) CONTAINS 'vat lieu' OR toLower(admin.summary) CONTAINS 'vật liệu'
           OR toLower(admin.summary) CONTAINS 'xep hang' OR toLower(admin.summary) CONTAINS 'xếp hàng'
        MATCH (crim:CriminalViolation {id: 'BLHS_Art261_C1'})
        MERGE (admin)-[r:ESCALATES_TO {condition: 'Hanh vi can tro gay thiet hai cho nguoi khac (lam chet nguoi, thuong tich >= 61% hoac thiet hai tai san >= 100 trieu dong)'}]->(crim)
        RETURN count(r) as count
        """).single()
        print(f"   [+] Linked {res3['count']} obstruction violations to BLHS Art 261 Clause 1.")

        # Connection 3: Loi giao xe cho nguoi khong du dieu kien -> BLHS Dieu 262
        res4 = session.run("""
        MATCH (admin:Violation)
        WHERE toLower(admin.summary) CONTAINS 'giao xe' 
           OR toLower(admin.summary) CONTAINS 'de cho' OR toLower(admin.summary) CONTAINS 'để cho'
           OR toLower(admin.summary) CONTAINS 'cho muon' OR toLower(admin.summary) CONTAINS 'cho mượn'
           OR toLower(admin.summary) CONTAINS 'chu phuong' OR toLower(admin.summary) CONTAINS 'chủ phương'
        MATCH (crim:CriminalViolation {id: 'BLHS_Art262_C1'})
        MERGE (admin)-[r:ESCALATES_TO {condition: 'Giao xe cho nguoi khong du dieu kien (say xin, ma tuy, khong bang lai...) va gay tai nan chet nguoi hoac ton hai suc khoe >= 61%'}]->(crim)
        RETURN count(r) as count
        """).single()
        print(f"   [+] Linked {res4['count']} vehicle lending/entrustment violations to BLHS Art 262 Clause 1.")

        print("[SUCCESS] ESCALATES_TO relations successfully enriched!")

enrich_criminal_nodes()
driver.close()
