import os
import sys
import json
import re
from groq import Groq
from neo4j import GraphDatabase

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load .env file natively if it exists to avoid exposing secrets in Git
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
AURA_URI = os.environ.get("AURA_URI", "")
AURA_USER = os.environ.get("AURA_USER", "")
AURA_PASSWORD = os.environ.get("AURA_PASSWORD", "")


class LegalGraphPathfinder:

    STOP_WORDS = {
        # --- Từ nghi vấn, cảm thán, hội thoại đuôi câu ---
        "bao", "nhiêu", "mấy", "tiền", "phạt", "sao", "thì", "thế", "nào", "vậy",
        "ơi", "à", "á", "hả", "nha", "nhé", "nghen", "dạ", "vâng", "thưa", "ạ",
        "đâu", "hở", "chớ", "ư", "nhở", "chăng", "cơ", "mà", "ôi", "đấy", "thôi",
        "chứ", "hỏi", "cho", "biết", "nghe", "nói", "rồi", "nữa", "với", "hết",

        # --- Đại từ xưng hô, vai vế đời sống (Khử nhiễu danh xưng) ---
        "tôi", "mình", "em", "anh", "chị", "ông", "bà", "bác", "chú", "cô", "dì",
        "cậu", "mợ", "tui", "ní", "bạn", "ta", "tao", "mày", "nó", "chúng", "họ",
        "người", "ai", "chủ", "khách", "tài", "xế", "bác_tài",

        # --- Giới từ, liên từ, cấu trúc điều hướng ---
        "của", "cho", "với", "này", "đó", "ở", "từ", "đến", "như", "và", "hay",
        "hoặc", "nhưng", "vì", "nên", "tại", "do", "bởi", "nếu", "qua", "lại",
        "đi", "về", "ra", "vào", "lên", "xuống", "trong", "ngoài", "trên", "dưới",
        "giữa", "bên", "cạnh", "sau", "trước", "như_vậy", "thành", "ra_sao",

        # --- Động từ tình thái, trợ từ, trạng thái chung chung ---
        "là", "có", "bị", "đang", "sẽ", "đã", "vừa", "mới", "sắp", "hãy", "đừng",
        "muốn", "hiểu", "giúp", "giùm", "hộ", "xem", "coi", "tra", "tìm", "làm",
        "ơn", "vui", "lòng", "xin", "thấy", "bảo", "kêu", "rằng", "cho_hỏi",

        # --- Từ định lượng, phạm vi, tính chất (Tránh làm nhiễu từ khóa chính) ---
        "mức", "cao", "nhất", "tối", "đa", "thiểu", "thấp", "lúc", "khi", "độ",
        "khoảng", "tầm", "cỡ", "loại", "nhóm", "vụ", "việc", "trường", "hợp",
        "hành", "vi", "tình", "huống", "các", "những", "mọi", "mỗi", "từng",
        "toàn", "bộ", "nhiều", "ít", "quá", "lắm",

        # --- Từ khóa phương tiện chung (Khử để không trùng lặp khi Cypher tìm kiếm) ---
        "xe", "máy", "ô", "tô", "hơi", "đạp", "thô", "sơ",

        # --- Thuật ngữ pháp lý nền tảng (BẮT BUỘC KHỬ để tránh CONTAINS trùng vào mọi Node) ---
        "luật", "nghị", "định", "168", "thông", "tư", "quy", "định", "pháp",
        "khung", "chế", "tài", "hình", "thức", "biện", "pháp", "xử", "vi", "phạm",
        "điều", "khoản", "điểm", "văn", "bản", "theo", "chiếu", "căn", "cứ", "bản",
        "án", "quyết", "định", "tố", "tụng", "hành", "chính", "chính_sách"
    }

    VEHICLE_MAP = {
        "xe_mo_to_xe_gan_may": [
            "xe máy", "xe mô tô", "mô tô", "xe gắn máy", "xe máy điện",
            "xe đạp điện", "honda", "yamaha", "suzuki", "vespa",
            "nón bảo hiểm", "mũ bảo hiểm", "mũ", "nón",
        ],
        "xe_o_to": [
            "ô tô", "xe ô tô", "xe hơi", "xe con", "xe tải", "xe khách",
            "xe buýt", "xe bus", "xe container",
        ],
        "xe_dap": ["xe đạp", "xe thô sơ"],
        "nguoi_di_bo": ["người đi bộ", "đi bộ"],
    }

    def __init__(self):
        self.driver = GraphDatabase.driver(AURA_URI, auth=(AURA_USER, AURA_PASSWORD))
        self.client = Groq(api_key=GROQ_API_KEY)

    def close(self):
        self.driver.close()

    def call_ai(self, system_prompt, user_prompt, json_mode=False):
        response_format = {"type": "json_object"} if json_mode else None
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format=response_format
        )
        return completion.choices[0].message.content

    def detect_vehicle(self, query):
        query_lower = query.lower()
        for category, keywords in self.VEHICLE_MAP.items():
            for kw in keywords:
                if kw in query_lower:
                    return category
        return "xe_mo_to_xe_gan_may"

    # =========================================================
    # TẦNG TIỀN XỬ LÝ (PRE-PROCESSOR AGENT - AGENT 0 & 1 GỘP)
    # =========================================================
    def preprocess_query(self, user_query):
        """
        Gộp Chuẩn hóa + Phân loại Intent + Nhận diện phương tiện vào 1 lần gọi LLM.
        Tiết kiệm Token và tăng độ chính xác nhờ ngữ cảnh nhất quán.
        """
        # Backup: Dung Python detect truoc de goi y cho LLM
        python_detected_vehicle = self.detect_vehicle(user_query)

        prompt = (
            "[ROLE] Bạn là Tác tử Tiền xử lý thông minh cho hệ thống Pháp luật Giao thông Việt Nam (Nghị định 168/2024).\n\n"
            f"CÂU HỎI THÔ CỦA NGƯỜI DÂN: '{user_query}'\n"
            f"GỢI Ý PHƯƠNG TIỆN (Dự đoán): {python_detected_vehicle}\n\n"
            "NHIỆM VỤ CỦA BẠN (TRẢ VỀ JSON):\n"
            "1. normalized_query: Chuẩn hóa về hành vi pháp lý. \n"
            "   - 'vượt ẩu', 'chạy láo' -> 'vượt không đúng quy định'\n"
            "   - 'đâm vào', 'va quệt', 'đụng xe' -> 'gây tai nạn'\n"
            "   - 'chạy nhanh', 'phiết' -> 'quá tốc độ'\n"
            "2. clean_keywords: Trích xuất các cụm từ NGẮN, QUAN TRỌNG NHẤT để tìm trong DB.\n"
            "   - BẮT BUỘC trích xuất từ khóa cho TẤT CẢ các hành vi vi phạm được nhắc tới.\n"
            "   - Ví dụ: ['tai nạn', 'vượt', 'tốc độ', 'rượu bia', 'nồng độ cồn'].\n"
            "   - ƯU TIÊN các từ khóa về HẬU QUẢ (Ví dụ: 'tai nạn', 'va chạm') và HÀNH VI chính.\n"
            "3. intent: 'GLOBAL' (chính sách chung) hoặc 'LOCAL' (lỗi cụ thể).\n"
            "4. vehicle_category: Xác định loại xe (xe_mo_to_xe_gan_may, xe_o_to, xe_tho_so_xe_dap, may_keo_xe_may_chuyen_dung).\n\n"
            "QUY TẮC VÀNG: Nếu có hành vi 'đâm/đụng/tai nạn', BẮT BUỘC phải có từ khóa 'tai nạn' trong clean_keywords.\n\n"
            "ĐỊNH DẠNG JSON BẮT BUỘC:\n"
            "{\n"
            "  \"normalized_query\": \"...\",\n"
            "  \"clean_keywords\": [\"tai nạn\", \"vượt\"],\n"
            "  \"intent\": \"LOCAL\",\n"
            "  \"vehicle_category\": \"xe_mo_to_xe_gan_may\"\n"
            "}"
        )

        try:
            res = self.call_ai(
                "Bạn là chuyên gia tiền xử lý ngôn ngữ pháp lý. Chỉ trả về JSON.",
                prompt, json_mode=True
            )
            data = json.loads(res)
            
            # Ghi log de debug
            print(f"[Pre-processor] Intent: {data.get('intent')} | Vehicle: {data.get('vehicle_category')}")
            print(f"[Pre-processor] Normalized: {data.get('normalized_query')}")
            
            return (
                data.get("normalized_query", user_query),
                data.get("clean_keywords", []),
                data.get("intent", "LOCAL"),
                data.get("vehicle_category", python_detected_vehicle)
            )
        except Exception as e:
            print(f"[!] Pre-processing failed: {e}. Fallback to legacy mode.")
            return user_query, [], "LOCAL", python_detected_vehicle

    def get_global_context(self, user_query):
        """
        Xu ly cau hoi GLOBAL: truy van thang DB,
        khong di qua vong lap Pathfinder.
        """
        reasoning_log = [
            "[GLOBAL MODE] Phát hiện câu hỏi vĩ mô. Bỏ qua vòng lặp Pathfinder.",
            "[GLOBAL MODE] Truy vấn trực tiếp dữ liệu tổng quát từ đồ thị.",
        ]
        path_data = []

        # Uu tien: lay cac vi pham co tru diem
        with self.driver.session() as session:
            res = session.run(
                "MATCH (v:Violation) WHERE v.point_deduction IS NOT NULL "
                "AND v.point_deduction > 0 RETURN v LIMIT 20"
            )
            for row in res:
                path_data.append(dict(row["v"]))

        if path_data:
            reasoning_log.append(
                f"[GLOBAL MODE] Tìm thấy {len(path_data)} vi phạm có trừ điểm GPLX."
            )
        else:
            # Fallback: lay Dieu 1-3 (tong quat)
            with self.driver.session() as session:
                res = session.run(
                    "MATCH (v:Violation) WHERE v.article <= 3 RETURN v LIMIT 15"
                )
                for row in res:
                    path_data.append(dict(row["v"]))
            reasoning_log.append(
                "[GLOBAL MODE] Không có dữ liệu trừ điểm. Lấy Điều khoản tổng quát."
            )

        return path_data, reasoning_log
    # BUOC 1: TIM DIEM BAT DAU (ENTRY NODE FINDER - AGENT 2)
    # =========================================================
    def find_entry_node(self, user_query, clean_keywords=None, vehicle_category=None):
        """
        Nhan clean_keywords tu Agent 0 (neu co).
        Loc theo vehicle_category ngay tai DB de tang do chinh xac.
        """
        # Neu khong co keywords tu Agent 0 -> fallback regex
        if not clean_keywords:
            words = re.findall(
                r'[\wàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+',
                user_query.lower()
            )
            clean_keywords = [w for w in words if len(w) > 2 and w not in self.STOP_WORDS]
            if not clean_keywords:
                clean_keywords = [w for w in words if len(w) > 2]

        print(f"[Agent 2] Entry keywords: {clean_keywords}")

        # Lay danh sach tu khoa sach
        search_keywords = [kw.lower().strip() for kw in clean_keywords if len(kw.strip()) > 1]
        
        # Bo sung: Tach cac tu don tu cum tu de tang ti le trung khop
        expanded_keywords = set()
        for kw in search_keywords:
            expanded_keywords.add(kw)
            for word in kw.split():
                if len(word) > 2:
                    expanded_keywords.add(word)
        
        search_list = list(expanded_keywords)[:10]
        print(f"[Agent 2] Searching DB with: {search_list}")

        candidates = []
        seen_ids = set()
        
        with self.driver.session() as session:
            # Query nang cao: Uu tien cac node co TIEN PHAT va trung khop tu khoa
            query = """
            MATCH (v:Violation)-[:APPLIES_TO]->(c:Category {name: $cat})
            WHERE NOT v.id CONTAINS 'Art1_' AND NOT v.id CONTAINS 'Art2_' AND NOT v.id CONTAINS 'Art3_'
            WITH v, 
                 [kw IN $kws WHERE toLower(v.summary) CONTAINS kw] as matches_summary,
                 [kw IN $kws WHERE toLower(coalesce(v.slang, '')) CONTAINS kw] as matches_slang
            WITH v, size(matches_summary) + size(matches_slang) as score
            WHERE score > 0
            RETURN v.id as id, v.summary as summary, v.fine_min as fine_min
            ORDER BY score DESC, v.fine_min DESC
            LIMIT 20
            """
            res = session.run(query, kws=search_list, cat=vehicle_category)
            for rec in res:
                if rec["id"] not in seen_ids:
                    seen_ids.add(rec["id"])
                    candidates.append({"id": rec["id"], "summary": rec["summary"]})
            
            # Ghi log de minh biet no tim duoc nhung gi
            print(f"[Agent 2] Candidates found: {[c['id'] for c in candidates]}")
            
            # Neu van khong co, thu tim kiem Global (khong loc category)
            if not candidates:
                query_global = """
                MATCH (v:Violation)
                WHERE ANY(kw IN $kws WHERE toLower(v.summary) CONTAINS kw)
                RETURN v.id as id, v.summary as summary
                LIMIT 10
                """
                res_g = session.run(query_global, kws=search_list)
                for rec in res_g:
                    if rec["id"] not in seen_ids:
                        seen_ids.add(rec["id"])
                        candidates.append({"id": rec["id"], "summary": rec["summary"]})

        if not candidates:
            return []

        prompt = (
            "[ROLE] Bạn là Tác tử Định vị Tri thức Đa điểm (Multi-Entry Node Finder).\n"
            "Nhiệm vụ: Chọn các ID vi phạm đại diện cho TẤT CẢ các hành vi được nhắc tới trong câu hỏi.\n\n"
            f"CÂU HỎI: '{user_query}'\n"
            f"DANH SÁCH ỨNG VIÊN:\n{json.dumps(candidates, ensure_ascii=False, indent=2)}\n\n"
            "QUY TẮC:\n"
            "1. Phải chọn ID cho TẤT CẢ các hành vi vi phạm được nhắc tới (Ví dụ: vừa rượu bia, vừa tốc độ, vừa tai nạn).\n"
            "2. CHỈ chọn các ID thực sự có hành vi tương ứng được đề cập trong câu hỏi. Tuyệt đối KHÔNG chọn các lỗi không liên quan (ví dụ: không chọn lỗi rượu bia/nồng độ cồn nếu câu hỏi không nhắc tới rượu bia/cồn).\n"
            "3. Trả về một danh sách các ID. Tối đa 5 ID quan trọng nhất.\n"
            "4. CHỈ trả về JSON: {\"chosen_ids\": [\"ID1\", \"ID2\"]}"
        )
        try:
            res = self.call_ai(
                "Bạn là Tác tử định vị đa điểm. Chỉ trả về JSON.",
                prompt, json_mode=True
            )
            chosen_ids = json.loads(res).get("chosen_ids", [])
            print(f"[Agent 2] Multi-Entry Selected: {chosen_ids}")
            return chosen_ids
        except Exception as e:
            print(f"[!] Entry selection failed: {e}")
            return [candidates[0]["id"]] if candidates else []

    # =========================================================
    # BUOC 2: KHAM PHA LANG GIENG (ACTION SPACE FILTERING)
    # =========================================================
    def get_neighbors(self, node_id, vehicle_category=None):
        """
        Lay lang gieng, dong thoi loc bot Violation cua loai xe KHAC tai DB.
        Bridge Node (Authority, Category, Topic) van giu lai.
        """
        if vehicle_category:
            query = """
            MATCH (n {id: $node_id})-[r]-(m)
            WHERE NOT (
                'Violation' IN labels(m)
                AND EXISTS { MATCH (m)-[:APPLIES_TO]->(c:Category) WHERE c.name <> $category }
            )
            RETURN type(r) as relationship,
                   m.id as target_id,
                   labels(m)[0] as label,
                   coalesce(m.summary, m.title, m.name) as description,
                   m.fine_min as fine_min,
                   m.fine_max as fine_max
            LIMIT 10
            """
            with self.driver.session() as session:
                return [dict(r) for r in session.run(query, node_id=node_id, category=vehicle_category)]
        else:
            query = """
            MATCH (n {id: $node_id})-[r]-(m)
            RETURN type(r) as relationship,
                   m.id as target_id,
                   labels(m)[0] as label,
                   coalesce(m.summary, m.title, m.name) as description,
                   m.fine_min as fine_min,
                   m.fine_max as fine_max
            LIMIT 10
            """
            with self.driver.session() as session:
                return [dict(r) for r in session.run(query, node_id=node_id)]

    # =========================================================
    # BUOC 3: LLM PATHFINDING VOI BACKTRACKING (AGENT 3)
    # =========================================================
    def navigate(self, user_query, start_id, vehicle_category=None):
        """
        [DA TOI UU] Agent 3: Tim duong den node hinh phat.
        Neu start_id da la Violation, ve dich luon de tiet kiem token.
        """
        current_id = start_id
        path_history = []
        reasoning_log = []
        
        # --- BUOC TOI UU 1: Kiem tra xem co phai la Violation xịn luon khong ---
        with self.driver.session() as session:
            check_res = session.run(
                "MATCH (n {id: $id}) RETURN n.fine_min as fine_min, labels(n) as labels",
                id=current_id
            ).single()
            
            if check_res and 'Violation' in check_res['labels'] and check_res['fine_min'] is not None:
                # VE DICH LUON - LAY EGO GRAPH
                ego_query = """
                MATCH (n {id: $id})
                OPTIONAL MATCH (n)-[r]-(m)
                RETURN n as violation, 
                       collect({
                           relationship: type(r),
                           label: labels(m)[0],
                           props: properties(m)
                       }) as neighbors
                """
                ego_res = session.run(ego_query, id=current_id).single()
                data_package = {
                    "main_violation": dict(ego_res["violation"]),
                    "related_legal_data": ego_res["neighbors"]
                }
                path_history.append(data_package)
                reasoning_log.append(f"[Instant Finish] Node '{current_id}' là vi phạm cụ thể. Bỏ qua traversal để tiết kiệm token.")
                return path_history, reasoning_log

        # --- NEU KHONG PHAI VI PHAM, MOI CHAY LOOP LLM (AGENT 3) ---
        if not vehicle_category:
            vehicle_category = self.detect_vehicle(user_query)
        print(f"[Agent 3] Vehicle lock: {vehicle_category} | Start: {start_id}")

        path_history = []
        reasoning_log = []
        visited = set()
        stack = [start_id]
        max_hops = 8
        hop = 0
        step = 0

        while stack and hop < max_hops:
            current_id = stack[-1]

            if current_id in visited:
                stack.pop()
                hop += 1
                continue

            visited.add(current_id)
            hop += 1
            step += 1
            print(f"[*] Buoc {step}: tai Node '{current_id}'")

            with self.driver.session() as session:
                curr_data = session.run(
                    "MATCH (n {id: $id}) RETURN n", id=current_id
                ).single()
                if curr_data:
                    path_history.append(dict(curr_data["n"]))

            neighbors = self.get_neighbors(current_id, vehicle_category)
            current_node_data = path_history[-1] if path_history else {}
            has_fine_data = bool(
                current_node_data.get("fine_min") and current_node_data.get("fine_max")
            )

            # Nhanh cut -> Backtrack
            if not neighbors:
                reasoning_log.append(
                    f"Bước {step}: [BACKTRACK] Không gian hành động rỗng tại '{current_id}'. Quay lui."
                )
                stack.pop()
                continue

            # [FIX] valid_ids dam bao khong None
            valid_ids = [n["target_id"] for n in neighbors if n.get("target_id")]

            prompt = (
                "[ROLE] Bạn là Tác tử Điều hướng Đồ thị (LLM Pathfinder) thuộc hệ thống Neuro-symbolic AI pháp lý.\n\n"
                f"CÂU HỎI NGƯỜI DÙNG: '{user_query}'\n"
                f"PHƯƠNG TIỆN ĐÃ KHÓA: {vehicle_category}\n"
                f"NODE BẠN ĐANG ĐỨNG: {current_id}\n"
                f"TRẠNG THÁI TIỀN PHẠT NODE HIỆN TẠI: {'CÓ (fine_min=' + str(current_node_data.get('fine_min')) + ')' if has_fine_data else 'CHƯA'}\n\n"
                "DANH SÁCH CÁC NGẢ ĐƯỜNG LÁNG GIỀNG HỢP LỆ (từ Neo4j, đã lọc đúng loại xe):\n"
                f"{json.dumps(neighbors, ensure_ascii=False, indent=2)}\n\n"
                "NHIỆM VỤ:\n"
                "1. Chọn 'target_id' phù hợp để thực hiện bước nhảy tiếp theo.\n"
                "2. Đánh giá điều kiện DỪNG SỚM để hạ lệnh 'is_final' = true.\n\n"
                "QUY TẮC PHÒNG THỦ CHỐNG TRÔI DẠT NGỮ NGHĨA:\n"
                f"1. [QUY TẮC ĐÍCH - CHỐNG GHOST HOP]: Nếu TRẠNG THÁI TIỀN PHẠT = CÓ, tri thức đã hoàn chỉnh. "
                f"BẮT BUỘC đặt 'next_id' = '{current_id}' (chính Node hiện tại) và 'is_final' = true NGAY LẬP TỨC.\n"
                "2. Nếu Node hiện tại CHƯA có tiền phạt nhưng láng giềng đã có fine_min/fine_max, "
                "chọn 'next_id' là ID láng giềng đó và bật 'is_final' = true.\n"
                "3. TUYỆT ĐỐI KHÔNG nhảy vào Node Thẩm quyền (Authority) nếu đã lộ diện số tiền phạt.\n"
                "4. [RÀO CHẮN TRI THỨC CŨ]: 'reason' CHỈ dựa trên quan hệ cấu trúc từ props láng giềng. "
                "TUYỆT ĐỐI CẤM nhắc Nghị định 100/2019/NĐ-CP hoặc bất kỳ văn bản hết hiệu lực nào khác.\n"
                "5. CHỈ được chọn 'next_id' nằm trong danh sách LÁNG GIỀNG HỢP LỆ ở trên.\n\n"
                "ĐỊNH DẠNG JSON BẮT BUỘC:\n"
                "{\"next_id\": \"ID_buoc_nhay\", "
                "\"reason\": \"[Lý do trích xuất thuần túy từ props láng giềng]\", "
                "\"is_final\": false}"
            )

            try:
                ai_output = self.call_ai(
                    "Bạn là Tác tử Điều hướng Đồ thị (LLM Pathfinder). Chỉ trả về JSON hợp lệ, không giải thích thêm.",
                    prompt, json_mode=True
                )
                decision = json.loads(ai_output)
            except Exception as e:
                reasoning_log.append(
                    f"Bước {step}: [CẢNH BÁO] Lỗi parse JSON: {e}. [BACKTRACK] Quay lui."
                )
                stack.pop()
                continue

            next_id = decision.get("next_id", "")
            reason = decision.get("reason", "Không rõ lý do.")
            is_final = decision.get("is_final", False)

            # [FIX GUARDRAIL] Neu valid_ids rong -> Backtrack, khong guo None
            if not valid_ids:
                reasoning_log.append(
                    f"Bước {step}: [BACKTRACK] Không có láng giềng hợp lệ tại '{current_id}'."
                )
                stack.pop()
                continue

            # [FIX FALSE POSITIVE GUARDRAIL]
            # Chi cuong buc khi AI thuc su bia ID la (khong co trong lang gieng VA khac current_id).
            # Neu AI dien next_id = current_id thi do la tin hieu EARLY STOPPING hop le.
            if next_id not in valid_ids and next_id != current_id:
                original = next_id
                next_id = valid_ids[0] if valid_ids else current_id
                reasoning_log.append(
                    f"Bước {step}: [GUARDRAIL] AI gợi ý ID không hợp lệ '{original}'. "
                    f"Cưỡng bức chọn láng giềng: '{next_id}'."
                )
            elif next_id == current_id and is_final:
                reasoning_log.append(
                    f"Bước {step}: [EARLY STOPPING ✓] Tác tử kích hoạt Dừng sớm tại '{current_id}'. "
                    f"Lý do: {reason}"
                )
            else:
                reasoning_log.append(
                    f"Bước {step}: Từ '{current_id}' → nhảy sang '{next_id}' | Lý do: {reason}"
                )

            if is_final:
                # [NANG CAP] Lay toan bo Ego-Graph cua Node dich (Violation + Sanctions + Authorities)
                # de AI co du du lieu ve Tuoc bang, Tam giu xe...
                final_node_id = next_id if next_id and next_id != current_id else current_id
                
                with self.driver.session() as session:
                    # Truy van lay node hien tai va tat ca cac node lien quan truc tiep
                    query = """
                    MATCH (n {id: $id})
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN n as violation, 
                           collect({
                               relationship: type(r),
                               label: labels(m)[0],
                               props: properties(m)
                           }) as neighbors
                    """
                    res = session.run(query, id=final_node_id).single()
                    if res:
                        data_package = {
                            "main_violation": dict(res["violation"]),
                            "related_legal_data": res["neighbors"]
                        }
                        path_history.append(data_package)

                reasoning_log.append(
                    f"Bước {step}: [ĐÍCH ✓] Hành trình kết thúc. Đã thu thập toàn bộ Ego-Graph của '{final_node_id}'."
                )
                break

            if next_id and next_id not in visited:
                stack.append(next_id)
            elif next_id in visited:
                reasoning_log.append(
                    f"Bước {step}: Node '{next_id}' đã thăm. [BACKTRACK] Quay lui."
                )
                stack.pop()


        return path_history, reasoning_log

    def aggregate_penalties(self, path_data):
        """
        [Symbolic Engine] Tong hop hinh phat theo nguyen tac Luat hanh chinh:
        - Tien phat: Cong don.
        - Tuoc bang/Tam giu: Lay muc cao nhat (khong cong don).
        """
        total_fine_min = 0
        total_fine_max = 0
        max_suspension_months = 0
        max_impound_days = 0
        
        for item in path_data:
            # Lay data tu main_violation hoac tu node goc
            v = item.get("main_violation", item)
            
            # Tien phat
            total_fine_min += v.get("fine_min", 0)
            total_fine_max += v.get("fine_max", 0)
            
            # Tim cac che tai bo sung trong neighbors
            neighbors = item.get("related_legal_data", [])
            for n in neighbors:
                props = n.get("props", {})
                # Gia su trong DB co cac truong nay (hoac parse tu title)
                susp = props.get("license_suspension_months", 0)
                impd = props.get("vehicle_impound_days", 0)
                
                if susp > max_suspension_months: max_suspension_months = susp
                if impd > max_impound_days: max_impound_days = impd

        return {
            "total_fine_min": total_fine_min,
            "total_fine_max": total_fine_max,
            "max_suspension_months": max_suspension_months,
            "max_impound_days": max_impound_days
        }

    # =========================================================
    # BUOC 4: TONG HOP KET QUA (VOI INTENT ROUTER)
    # =========================================================
    def ask(self, user_query):
        """
        Returns tuple (llm_answer, raw_log_lines).
        GLOBAL: truy van thang DB, khong qua Pathfinder
        LOCAL : chay vong lap Pathfinder day du
        """
        print(f"\n{'='*60}")
        print(f"[*] CAU HOI THO: {user_query}")

        # === AGENT 0 & 1 & VEHICLE: TIEN XU LY (GOP) ===
        normalized_query, clean_keywords, intent, vehicle_category = self.preprocess_query(user_query)

        if intent == "GLOBAL":
            path_data, reasoning_log = self.get_global_context(normalized_query)
            mode_label = "GLOBAL SEARCH"
            reasoning_log.insert(0, f"[Agent Pre-processor] Normalized: '{normalized_query}'")
        else:
            # === AGENT 2: TIM CAC ENTRY NODE (Dung cho da vi pham) ===
            start_ids = self.find_entry_node(
                normalized_query,
                clean_keywords=clean_keywords,
                vehicle_category=vehicle_category
            )
            if not start_ids:
                return "Không tìm thấy điểm bắt đầu phù hợp. Vui lòng diễn đạt rõ hơn.", []
            
            # === AGENT 3: PATHFINDER CHO TUNG LOI ===
            aggregated_path_data = []
            aggregated_reasoning = []
            seen_nodes = set()
            
            for s_id in start_ids:
                p_data, p_log = self.navigate(
                    normalized_query,
                    start_id=s_id,
                    vehicle_category=vehicle_category
                )
                if isinstance(p_data, list):
                    # NANG CAP: Duyet nguoc de uu tien bản ghi Ego-Graph (nam o cuoi danh sach)
                    for node in reversed(p_data):
                        node_id = node.get("main_violation", {}).get("id") or node.get("id")
                        if node_id not in seen_nodes:
                            aggregated_path_data.append(node)
                            seen_nodes.add(node_id)
                
                aggregated_reasoning.extend(p_log)
            
            path_data = aggregated_path_data
            reasoning_log = aggregated_reasoning
            mode_label = f"MULTI-PATHFINDER ({len(start_ids)} violations)"
            reasoning_log.insert(0, f"[Agent 0+1] Normalized: '{normalized_query}' | Keywords: {clean_keywords} | Vehicle: {vehicle_category}")

        if isinstance(path_data, str):
            return path_data, []

        if not path_data:
            return "Không thu thập được dữ liệu nào từ đồ thị tri thức.", reasoning_log

        # === TINH TOAN TONG HOP (SYMBOLIC ENGINE) ===
        agg_results = self.aggregate_penalties(path_data)
        context = json.dumps(path_data, ensure_ascii=False, indent=2)

        if intent == "GLOBAL":
         system_prompt = (
                "[ROLE ANCHOR]\n"
                "Bạn là Thẩm phán AI Tối cao chuyên trách giải quyết vi phạm và giải thích chính sách pháp lý vĩ mô dựa trên Nghị định 168/2024/NĐ-CP.\n\n"
                "[NHIỆM VỤ]\n"
                "Tổng hợp, lập luận và phân tích xu hướng, tinh thần của các chính sách pháp lý vĩ mô dựa trên tập bối cảnh được cung cấp. Cung cấp cái nhìn toàn diện và chính xác cho người dân.\n\n"
                "[NGUỒN TRI THỨC TUYỆT ĐỐI (GROUND TRUTH CONSTRAINT)]\n"
                "TUYỆT ĐỐI KHÔNG tự ý suy diễn, giả định số liệu tiền phạt hoặc chế tài nằm ngoài bối cảnh tri thức đồ thị dưới đây.\n\n"
                "--- TẬP TRI THỨC VĨ MÔ TRÍCH XUẤT TỪ ĐỒ THỊ ---\n"
                f"{context}\n"
                "----------------------------------------------\n\n"
                "[YÊU CẦU VĂN PHONG]\n"
                "- Sử dụng văn phong hành chính - tư pháp trang trọng, lập luận sắc bén, gãy gọn.\n"
                "- Sử dụng chuẩn mực từ vựng pháp lý Việt Nam (Ví dụ: Biện pháp khắc phục hậu quả, Tính chất hành vi, Thẩm quyền xử phạt).\n\n"
                "[ĐỊNH DẠNG ĐẦU RA BẮT BUỘC]\n"
                "### ⚖️ KẾT LUẬN\n"
                "[Trình bày câu trả lời tổng hợp mạch lạc, phân tích rõ ràng câu hỏi vĩ mô của người dân dựa trên bối cảnh tri thức]\n\n"
                "### 📜 CĂN CỨ PHÁP LUẬT\n"
                "[Liệt kê chính xác tên các Điều, Khoản của Nghị định 168/2024/NĐ-CP có xuất hiện trong Tập tri thức trên dưới dạng danh sách đầu dòng]"
            )
        else:
            system_prompt = (
                "[ROLE ANCHOR]\n"
                "Bạn là Thẩm phán AI Tối cao được lập trình để soạn thảo Phán quyết xử phạt giao thông chuẩn mực dựa trên luật định của Nghị định 168/2024/NĐ-CP và Luật Xử lý vi phạm hành chính.\n\n"
                "[QUY TẮC NGUỒN SỰ THẬT (GROUND TRUTH CONSTRAINTS)]\n"
                "1. CHỈ sử dụng dữ liệu được cung cấp trong các khối thẻ dữ liệu bên dưới. KHÔNG được sử dụng kiến thức cũ hoặc số liệu ảo giác từ các lượt hội thoại trước.\n"
                "2. Đối chiếu nghiêm ngặt dữ liệu từ 'Hệ thống tính toán cứng (Symbolic)' và 'Dữ liệu đồ thị chi tiết' để đảm bảo tính đồng bộ thông tin.\n"
                "3. Trích xuất chính xác Điểm, Khoản (clause), Điều (article) từ thuộc tính 'main_violation' của từng thực thể vi phạm.\n\n"
                "[RÀO CHẮN AN TOÀN PHÁP LÝ CHÍ MẠNG (CRITICAL SAFETY GUARDRAIL)]\n"
                "- Nếu câu hỏi thô hoặc phần hành vi chứa các yếu tố biến cố va chạm ('tai nạn', 'đâm xe', 'va chạm', 'gây thiệt hại'...) nhưng trong mảng 'related_legal_data' chưa cập nhật các Node chế tài bổ sung tương ứng: TUYỆT ĐỐI KHÔNG ĐƯỢC kết luận 'Không áp dụng'.\n"
                "- Trong trường hợp dính bẫy thiếu dữ liệu tai nạn này, tại mục 'Hình thức phạt bổ sung', bạn BẮT BUỘC phải ghi nguyên văn dòng cảnh báo đỏ sau: \"⚠️ Hệ thống hiện tại chưa cấu trúc đủ dữ liệu Hậu quả thực tế. Cần đối chiếu thêm với kết quả giám định thiệt hại thực tế (về người và tài sản) để xác định chính xác mức độ tước GPLX, tạm giữ phương tiện hoặc khả năng truy cứu trách nhiệm Hình sự theo Điều 260 Bộ luật Hình sự.\"\n\n"
                "[DỮ LIỆU ĐẦU VÀO HỆ THỐNG]\n"
                "<SYMBOLIC_ENGINE_OUTPUT>\n"
                f"- Tổng tiền phạt: {agg_results['total_fine_min']:,} - {agg_results['total_fine_max']:,} VNĐ\n"
                f"- Tước bằng tối đa phát hiện: {agg_results['max_suspension_months']} tháng\n"
                f"- Tạm giữ xe tối đa phát hiện: {agg_results['max_impound_days']} ngày\n"
                "</SYMBOLIC_ENGINE_OUTPUT>\n\n"
                "<GRAPH_CONTEXT_DATA>\n"
                f"{context}\n"
                "</GRAPH_CONTEXT_DATA>\n\n"
                "[ĐỊNH DẠNG ĐẦU RA PHÁN QUYẾT BẮT BUỘC]\n"
                "SỬ DỤNG MARKDOWN CHUẨN. BẮT BUỘC dùng 2 lần xuống dòng (\\n\\n) giữa các mục.\n\n"
                "### ⚖️ TỔNG HỢP PHÁN QUYẾT\n"
                f"> **Tổng tiền phạt:** Từ {agg_results['total_fine_min']:,} đến {agg_results['total_fine_max']:,} VNĐ.\n\n"
                f"> **Hình thức phạt bổ sung:** [Ghi rõ mức tước bằng/tạm giữ xe tối đa ({agg_results['max_suspension_months']} tháng tước bằng, {agg_results['max_impound_days']} ngày giữ xe) HOẶC Cảnh báo đỏ về tai nạn].\n\n"
                "--- \n\n"
                "### 🔍 CHI TIẾT CÁC LỖI VI PHẠM\n"
                "Mỗi lỗi phải nằm trên một dòng riêng biệt:\n\n"
                "- **Lỗi 1:** [Tên hành vi] (Mức phạt: [Tiền])\n\n"
                "- **Lỗi 2:** [Tên hành vi] (Mức phạt: [Tiền])\n\n"
                "### 📖 GIẢI THÍCH PHÁP LÝ\n\n"
                "- [Giải thích về cộng dồn tiền phạt]\n\n"
                "- [Giải thích về lấy mức phạt bổ sung cao nhất]\n\n"
                "- [Lập luận về tính chất tai nạn nếu có]\n\n"
                "### 💡 LƯU Ý THỰC TIỄN\n\n"
                "- [Khuyến cáo 1]\n\n"
                "- [Khuyến cáo 2]\n\n"
                "### 📜 CĂN CỨ PHÁP LUẬT\n\n"
                "- [Điều/Khoản trích dẫn từ JSON]"
            )
        llm_answer = self.call_ai(system_prompt, user_query)

        # LOG THUAN TOAN PYTHON - KHONG QUA LLM
        formatted_path = []
        for n in path_data[:5]:
            # Lay ID thong minh: neu la package thi boc tu main_violation, neu ko thi boc truc tiep
            node_id = n.get("main_violation", {}).get("id") if "main_violation" in n else n.get("id")
            formatted_path.append(node_id if node_id else "?")

        raw_log_lines = [
            "═" * 50,
            f"🗺️  [{mode_label}] GRAPH TRAVERSAL LOG (Python Generated)",
            "═" * 50,
        ] + reasoning_log + [
            "═" * 50,
            f"📊 Tổng: {len(path_data)} node | {len(reasoning_log)} bước | Mode: {mode_label}",
            f"📍 Path: {' → '.join(formatted_path)}",
        ]

        return llm_answer, raw_log_lines


if __name__ == "__main__":
    agent = LegalGraphPathfinder()
    for q in ["Luật mới có trừ điểm không?", "Không đội mũ bảo hiểm xe máy phạt bao nhiêu?"]:
        result = agent.ask(q)
        if isinstance(result, tuple):
            answer, log = result
            print(answer)
            print("\n".join(log))
        else:
            print(result)
        print("\n" + "="*60 + "\n")
    agent.close()
