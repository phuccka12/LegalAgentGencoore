import json

with open('nghidinh168_knowledge_graph_enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Tim loi vuot den do o Dieu 6 (Xe may)
results = []
for item in data:
    if item['metadata']['article'] == 6:
        behavior_text = str(item['behavior']).lower()
        if 'đèn tín hiệu' in behavior_text or 'vượt đèn đỏ' in behavior_text:
            results.append(item)

if results:
    res = results[0]
    summary = res['behavior']['summary']
    fine = res['consequences']['fine_range']
    remedial = res['consequences']['remedial_measures']
    slang = res['behavior']['semantic_expansion']['slang']
    
    print("-" * 50)
    print(f"Hanh vi: {summary}")
    print(f"Tieng long: {', '.join(slang)}")
    print(f"Muc phat: Tu {fine['min']:,} den {fine['max']:,} dong")
    print(f"Goi y phat (Trung binh): {fine['suggested']:,} dong")
    print(f"Hinh phat bo sung: {', '.join(remedial)}")
    print("-" * 50)
else:
    print("Khong tim thay ket qua.")
