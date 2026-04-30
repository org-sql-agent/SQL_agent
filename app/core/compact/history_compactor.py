"""
history_compactor.py
--------------------
負責壓縮傳給 LLM 的對話上下文（context）。

設計原則：
  - 只動 LLM 看到的 context，絕對不修改傳入的 history list（原始 list 由前端自行維護）
  - 超過 COMPACT_THRESHOLD（token 估算）才觸發壓縮
  - 壓縮策略：保留最近 KEEP_RECENT 筆訊息，把更早的歷史 summary 成一段摘要注入
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

# ── 設定 ──────────────────────────────────────────────────────────────────────

# 觸發壓縮的 token 門檻（估算值）
COMPACT_THRESHOLD: int = 3_000

# 壓縮時保留最近幾筆訊息不動
KEEP_RECENT: int = 6


# ── Token 估算 ────────────────────────────────────────────────────────────────


def _estimate_tokens(text: str) -> int:
    """
    粗略估算 token 數：中英混合約 2 chars / token。
    不需要精準，只做門檻觸發用。
    """
    return max(1, len(text) // 2)


def count_context_tokens(history: list[dict], user_input: str) -> int:
    """計算本次 LLM 呼叫的預估 token 總量（history + user_input）。"""
    total = _estimate_tokens(user_input)
    for msg in history:
        total += _estimate_tokens(str(msg.get("content") or ""))
        total += _estimate_tokens(str(msg.get("summary") or ""))
    return total


# ── 壓縮邏輯 ──────────────────────────────────────────────────────────────────


def _summarize_older(older: list[dict], client: "OpenAI", model: str) -> str:
    """把舊對話列表摘要成一段純文字。"""
    lines: list[str] = []
    for msg in older:
        role = msg.get("role", "unknown")
        content = str(msg.get("content") or "")
        summary = msg.get("summary")
        # echarts 類型的 assistant 訊息以 summary 為主，跳過龐大的 JSON
        if msg.get("type") == "echarts" and summary:
            lines.append(f"{role}（圖表）: {summary}")
        elif content:
            lines.append(f"{role}: {content}")

    older_text = "\n".join(lines)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一個對話摘要助手。"
                    "請將以下對話歷史壓縮成簡潔的繁體中文摘要，"
                    "保留重要的資料查詢結果、預測結果與關鍵數字，"
                    "讓後續對話能夠無縫繼續。只輸出摘要內容，不要其他說明。"
                ),
            },
            {"role": "user", "content": f"請摘要以下對話：\n\n{older_text}"},
        ],
    )
    return response.choices[0].message.content.strip()


def _compact_history(history: list[dict], client: "OpenAI", model: str) -> list[dict]:
    """
    把 history 壓縮後回傳新 list：
      [摘要佔位訊息 x2] + [最近 KEEP_RECENT 筆]
    不修改原始 history。
    """
    if len(history) <= KEEP_RECENT:
        return list(history)

    older = history[:-KEEP_RECENT]
    recent = history[-KEEP_RECENT:]

    summary_text = _summarize_older(older, client, model)

    return [
        {
            "role": "user",
            "content": f"【前段對話摘要】\n{summary_text}",
        },
        {
            "role": "assistant",
            "content": "了解，我已掌握前段對話重點，請繼續。",
        },
    ] + recent


# ── 公開介面 ──────────────────────────────────────────────────────────────────


def maybe_compact(
    history: list[dict],
    user_input: str,
    client: "OpenAI",
    model: str,
) -> list[dict]:
    """
    若本次 context 超過 COMPACT_THRESHOLD，回傳壓縮後的 history 副本；
    否則直接回傳淺層副本。

    ＃原始 history list 永遠不會被修改。
    """
    token_count = count_context_tokens(history, user_input)

    if token_count <= COMPACT_THRESHOLD:
        return list(history)

    print(
        f"[Compactor] Context tokens ≈ {token_count} > {COMPACT_THRESHOLD}，觸發壓縮..."
    )
    compacted = _compact_history(history, client, model)
    print(f"[Compactor] 壓縮完成：{len(history)} → {len(compacted)} 筆訊息")

    print("[Compactor] 壓縮後的 history 預覽：")
    for msg in compacted[:2]:  # 只印前兩筆（摘要佔位訊息）
        print(f"  - {msg['role']}: {msg['content'][:]}...")

    return compacted
