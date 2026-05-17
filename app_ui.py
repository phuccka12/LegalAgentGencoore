import streamlit as st
from legal_agent import LegalAgent
import sys

# Cau hinh UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

st.set_page_config(page_title="Hệ thống Tra cứu Luật 168 - AI Agent", layout="wide")

st.title("⚖️ Trợ lý ảo Pháp luật Giao thông (Nghị định 168)")
st.markdown("---")

if "agent" not in st.session_state:
    st.session_state.agent = LegalAgent()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Hien thi lich su chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input tu nguoi dung
if prompt := st.chat_input("Hỏi về vi phạm giao thông (VD: Nồng độ cồn xe máy)..."):
    # Them cau hoi vao lich su
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Agent tra loi
    with st.chat_message("assistant"):
        with st.status("Đang truy vấn Đồ thị tri thức Neo4j Aura...", expanded=True) as status:
            try:
                response = st.session_state.agent.ask(prompt)
                status.update(label="Truy vấn thành công!", state="complete", expanded=False)
                st.markdown(response)
                # Luu cau tra loi
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                status.update(label="Lỗi hạn mức API (429)", state="error", expanded=False)
                st.error(f"Hệ thống đang bận do hết hạn mức API miễn phí. Vui lòng thử lại sau 1 phút. Chi tiết: {e}")

st.sidebar.info("Hệ thống sử dụng công nghệ GraphRAG: Gemini 1.5 + Neo4j Knowledge Graph.")
if st.sidebar.button("Xóa lịch sử trò chuyện"):
    st.session_state.messages = []
    st.rerun()
