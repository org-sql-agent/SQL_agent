import streamlit as st
from agent import ai_agent
import base64

st.title("Titanic AI Agent 🚢 ")
user_input = st.text_input(
    "請輸入問題，例如：'生還率多少？' 或 '畫出生還率和艙等關係' 或 '預測我是否生還'"
)

if "history" not in st.session_state:
    st.session_state["history"] = []

if st.button("送出"):
    with st.spinner("AI 分析中..."):
        result = ai_agent(st.session_state["history"], user_input)
        print(f"AI Response type: {result['type']}")

        if result["type"] == "image":
            img_data = result["data"].get("image_base64", None)
            if img_data:
                st.image(base64.b64decode(img_data), use_container_width=True)
                st.caption(f"🤖 {result['content']}")  ###
            else:
                st.error("圖片資料缺失")
        else:
            st.write(result["content"])

st.subheader("對話紀錄")
for h in st.session_state["history"]:
    if h["role"] == "user":
        st.write(f"User👤 {h['content']}")

    elif h["role"] == "assistant":
        if h.get("type") == "image":
            st.image(base64.b64decode(h["image_base64"]), use_container_width=True)
            st.caption(f"🤖 {h['content']}")
        else:
            st.write(f"🤖 {h['content']}")


# if st.button("送出"):
#     with st.spinner("AI 分析中..."):
#         result = ai_agent(user_input)
#         st.write(result["content"])
