import json
import os
import re

INPUT_FILE = "nghidinh168_knowledge_graph_ultra.json"
OUTPUT_VIOLATIONS = "nghidinh168_violations_final.json"
OUTPUT_AUTHORITIES = "nghidinh168_authorities_final.json"

def fix_id(node_id):
    # 1. Sua loi tien to ND32, NDXX thanh ND168
    new_id = re.sub(r'^ND\d+_(.*)', r'ND168_\1', node_id)
    # 2. Xoa bo _pnull
    new_id = new_id.replace("_pnull", "")
    return new_id

def clean_hallucinated_slang(node_id, slang_list):
    # Danh sach tu cam (ao giac)
    forbidden = ["Thông chốt hụt", "Cồn kịch khung hụt", "Dùng dế", "Xe lam đời mới", "Xe túc túc vào cao tốc", "Giam xe sau"]
    cleaned = [s for s in slang_list if s not in forbidden]
    
    # Bo sung tu chuan cho cac node bi loi
    if node_id == "ND168_Art6_C4_d":
        cleaned.extend(["Ôm làn", "Cản địa", "Không cho vượt"])
    if node_id == "ND168_Art6_C5_h":
        cleaned.extend(["Dùng điện thoại", "Vừa lái vừa bấm"])
    
    return list(set(cleaned))

def main():
    if not os.path.exists(INPUT_FILE):
        print("Khong tim thay file nguon!")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    violation_nodes = []
    authority_nodes = []

    for item in data:
        # Sua ID
        item["node_id"] = fix_id(item["node_id"])
        art_num = item["metadata"]["article"]

        # Xu ly Slang cho cac node vi pham
        if "behavior" in item and "semantic_expansion" in item["behavior"]:
            item["behavior"]["semantic_expansion"]["slang"] = clean_hallucinated_slang(
                item["node_id"], 
                item["behavior"]["semantic_expansion"].get("slang", [])
            )

        # PHAN LOAI ONTOLOGY
        if 6 <= art_num <= 40:
            # Day la VIOLATION
            violation_nodes.append(item)
        elif 41 <= art_num <= 55:
            # Day la AUTHORITY (Chuan hoa lai Schema)
            auth_node = {
                "node_id": item["node_id"],
                "metadata": item["metadata"],
                "authority": {
                    "title": item["behavior"]["summary"],
                    "raw_text": item["behavior"]["raw_legal_text"],
                    "max_fine_limit": item["consequences"]["fine_range"]
                }
            }
            authority_nodes.append(auth_node)
        else:
            # Cac dieu 1-5 giu lai trong violations de tham chieu
            violation_nodes.append(item)

    # Luu file
    with open(OUTPUT_VIOLATIONS, "w", encoding="utf-8") as f:
        json.dump(violation_nodes, f, ensure_ascii=False, indent=2)
    
    with open(OUTPUT_AUTHORITIES, "w", encoding="utf-8") as f:
        json.dump(authority_nodes, f, ensure_ascii=False, indent=2)

    print(f"--- DA HOAN TAT DAI PHAU THUAT ---")
    print(f"1. Violations Node: {len(violation_nodes)} -> {OUTPUT_VIOLATIONS}")
    print(f"2. Authority Node: {len(authority_nodes)} -> {OUTPUT_AUTHORITIES}")

if __name__ == "__main__":
    main()
