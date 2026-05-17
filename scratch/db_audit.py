import sys
sys.path.append('.')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('neo4j+s://f5fc20b1.databases.neo4j.io', auth=('f5fc20b1', 'liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE'))

def check_db_stats():
    with driver.session() as session:
        # 1. Dem tong so node Vi pham
        count_res = session.run("MATCH (v:Violation) RETURN count(v) as total").single()
        total_violations = count_res['total']
        
        # 2. Liet ke cac Dieu co trong DB
        articles_res = session.run("MATCH (v:Violation) RETURN DISTINCT v.article as art ORDER BY art")
        articles = [r['art'] for r in articles_res]
        
        # 3. Kiem tra xem co Bo luat Hinh su khong
        criminal_res = session.run("MATCH (n) WHERE toLower(n.summary) CONTAINS 'hình sự' OR toLower(n.title) CONTAINS 'hình sự' RETURN count(n) as total").single()
        criminal_count = criminal_res['total']
        
        # 4. Kiem tra cac loi nang (Ruou bia, Ma tuy)
        severe_res = session.run("MATCH (v:Violation) WHERE toLower(v.summary) CONTAINS 'nồng độ cồn' OR toLower(v.summary) CONTAINS 'ma túy' RETURN count(v) as total").single()
        severe_count = severe_res['total']

        with open('db_audit_report.txt', 'w', encoding='utf-8') as f:
            f.write(f"--- BAO CAO KIEM KE DU LIEU ---\n")
            f.write(f"Tong so loi vi pham (Violation Nodes): {total_violations}\n")
            f.write(f"Cac Dieu (Articles) hien co: {articles}\n")
            f.write(f"So node lien quan den Hinh su: {criminal_count}\n")
            f.write(f"So node lien quan den loi nang (Con/Ma tuy): {severe_count}\n")
            
            # Kiem tra Dieu 260 BLHS
            blhs_res = session.run("MATCH (n) WHERE n.id CONTAINS '260' OR n.title CONTAINS '260' RETURN n.summary LIMIT 1").single()
            if blhs_res:
                f.write(f"Diem tin: Da tim thay tham chieu Den Dieu 260 Bo luat Hinh su.\n")
            else:
                f.write(f"Canh bao: Chua tim thay Node rieng biet cho Dieu 260 BLHS.\n")

check_db_stats()
driver.close()
