import base64
import os

import requests
import streamlit as st
from streamlit_echarts import st_echarts

from app.utils.json_utils import clean_markdown_json

SERVICE_API_URL = os.getenv("SERVICE_API_URL", "http://localhost:8080/Service")

st.set_page_config(page_title="Titanic AI Agent", layout="wide")
st.title("Titanic AI Agent 🚢")

# display_history : 完整對話紀錄，只用來渲染畫面，永不刪減
# llm_history     : 送給 API 的 context；backend compact 後會回傳壓縮版，
#                   前端存下來下次直接送，不再重壓完整的 display_history
if "display_history" not in st.session_state:
    st.session_state["display_history"] = []
if "llm_history" not in st.session_state:
    st.session_state["llm_history"] = []


# ── 渲染單則訊息 ──────────────────────────────────────────────────────────────


def render_assistant_message(msg: dict, chart_key: str) -> None:
    """把一則 assistant 訊息渲染到畫面上（在 st.chat_message 內呼叫）。"""
    msg_type = msg.get("type")

    if msg_type == "image":
        img_b64 = (msg.get("data") or {}).get("image_base64")
        if img_b64:
            st.image(base64.b64decode(img_b64), use_container_width=True)
            st.caption(msg.get("content", ""))
        else:
            st.error("圖片資料缺失")

    elif msg_type == "echarts":
        option = clean_markdown_json(msg.get("content", ""))
        if option:
            st_echarts(options=option, height="500px", key=chart_key)
            st.caption(msg.get("summary") or "（未提供摘要）")
        else:
            st.error("圖表資料解析失敗")

    else:
        st.write(msg.get("content", ""))


# ── 渲染歷史紀錄（由上往下 = 時間順序，最新在最下面）────────────────────────


for i, msg in enumerate(st.session_state["display_history"]):
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])

    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            render_assistant_message(msg, chart_key=f"chart-{i}")


# ── 輸入欄（固定在最底部）────────────────────────────────────────────────────


user_input = st.chat_input(
    "請輸入問題，例如：生還率多少？畫出生還率和艙等關係、預測我是否生還"
)

if user_input:
    # 立即顯示使用者訊息
    with st.chat_message("user"):
        st.write(user_input)

    # 呼叫 API（送 llm_history，不是 display_history）
    with st.chat_message("assistant"):
        with st.spinner("AI 分析中..."):
            try:
                response = requests.post(
                    SERVICE_API_URL,
                    json={
                        "text": user_input,
                        "history": st.session_state["llm_history"],
                    },
                    timeout=120,
                )
                response.raise_for_status()
                body = response.json()
                result = body["data"]
                # backend 回傳的壓縮 context base，存回來供下次使用
                returned_llm_base: list = body.get("llm_history", [])
            except requests.RequestException as exc:
                st.error(f"API 呼叫失敗: {exc}")
                st.stop()
            except (KeyError, ValueError) as exc:
                st.error(f"API 回應格式錯誤: {exc}")
                st.stop()

        latest_key = f"chart-latest-{len(st.session_state['display_history'])}"
        render_assistant_message(result, chart_key=latest_key)

    # ── 組訊息物件 ────────────────────────────────────────────────────────────
    user_msg: dict = {"role": "user", "content": user_input}
    assistant_msg: dict = {
        "role": "assistant",
        "type": result.get("type"),
        "content": result.get("content", ""),
        "summary": result.get("summary"),
    }
    if result.get("data"):
        assistant_msg["data"] = result["data"]

    # display_history：完整保留，只用於畫面渲染
    st.session_state["display_history"].append(user_msg)
    st.session_state["display_history"].append(assistant_msg)

    # llm_history：backend 回傳的壓縮 base + 本次新訊息
    # 下次送出時已是壓縮過的狀態，不會觸發重複壓縮
    st.session_state["llm_history"] = returned_llm_base + [user_msg, assistant_msg]
