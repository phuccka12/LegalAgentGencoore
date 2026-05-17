from neo4j import GraphDatabase
import sys

# Ep terminal hien thi tieng Viet
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

URI = "neo4j+s://f5fc20b1.databases.neo4j.io"
USER = "f5fc20b1"
PASSWORD = "liHxH9XxpFYpFJzXic1olpUHDEMvTQTEbryOUqJHNpE"

def check():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    with driver.session() as session:
        # 1. Kiem tra Mu bao hiem
        print("=== [KIỂM TRA] LỖI MŨ BẢO HIỂM ===")
        res = session.run("MATCH (v:Violation) WHERE v.summary CONTAINS 'mũ bảo hiểm' RETURN v.summary, v.fine_min, v.fine_max LIMIT 3")
        records = list(res)
        if not records:
            print("(!) Khong tim thay chu 'mũ bảo hiểm' trong summary.")
        for r in records:
            print(f"- Lỗi: {r['v.summary']}")
            print(f"  Phat: {r['v.fine_min']} - {r['v.fine_max']} VND\n")

        # 2. Kiem tra Nong do con
        print("\n=== [KIỂM TRA] LỖI NỒNG ĐỘ CỒN ===")
        res = session.run("MATCH (v:Violation) WHERE v.summary CONTAINS 'nồng độ cồn' RETURN v.summary, v.fine_min, v.fine_max LIMIT 3")
        records = list(res)
        if not records:
            print("(!) Khong tim thay chu 'nồng độ cồn' trong summary.")
        for r in records:
            print(f"- Lỗi: {r['v.summary']}")
            print(f"  Phat: {r['v.fine_min']} - {r['v.fine_max']} VND\n")
            
    driver.close()

if __name__ == "__main__":
    check()
