import json
import os

INPUT_FILE = "nghidinh168_knowledge_graph.json"
OUTPUT_FILE = "nghidinh168_knowledge_graph_final.json"

def clean_and_verify():
    if not os.path.exists(INPUT_FILE):
        print("File khong ton tai!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[*] Tong so node ban dau: {len(data)}")

    # 1. Loai bo trung lap dua tren node_id
    seen_ids = set()
    unique_data = []
    duplicates = 0
    for item in data:
        node_id = item.get("node_id")
        if node_id not in seen_ids:
            unique_data.append(item)
            seen_ids.add(node_id)
        else:
            duplicates += 1
    
    print(f"[*] Da loai bo {duplicates} node trung lap.")

    # 2. Sap xep lai theo thu tu Dieu -> Khoan -> Diem
    def sort_key(item):
        m = item.get("metadata", {})
        art = m.get("article")
        if art is None: art = 0
        cl = m.get("clause")
        if cl is None: cl = 0
        pt = m.get("point")
        if pt is None: pt = ""
        return (art, cl, str(pt))

    unique_data.sort(key=sort_key)

    # 3. Kiem tra cac Dieu con thieu
    articles_present = sorted(list(set(item.get("metadata", {}).get("article") for item in unique_data if item.get("metadata", {}).get("article") is not None)))
    all_possible = list(range(1, 56))
    missing = [a for a in all_possible if a not in articles_present]
    
    print(f"[*] Danh sach Dieu hien co: {articles_present}")
    print(f"[*] CAC DIEU CON THIEU CAN VA NOT: {missing}")

    # 4. Luu file sach
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=2)
    
    print(f"[*] Da luu file sach tai: {OUTPUT_FILE}")
    print(f"[*] Tong so node cuoi cung: {len(unique_data)}")

if __name__ == "__main__":
    clean_and_verify()
