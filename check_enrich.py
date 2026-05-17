import json

with open('nghidinh168_knowledge_graph_enriched.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

art6 = [item for item in data if item['metadata']['article'] == 6 and item['behavior']['semantic_expansion']['slang']]
print(f"Enriched Art 6 nodes: {len(art6)}")
if art6:
    print(json.dumps(art6[0], indent=2, ensure_ascii=False))
