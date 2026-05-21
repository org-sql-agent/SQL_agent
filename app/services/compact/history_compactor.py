"""
負責壓縮傳給 LLM 的對話上下文（context）。

設計原則：
  - 只動 LLM 看到的 context，絕對不修改傳入的 history list
  - 超過 COMPACT_THRESHOLD（token 估算）才觸發壓縮
  - 壓縮策略：保留最近 KEEP_RECENT 筆訊息，把更早的歷史 summary 成一段摘要注入
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from openai import OpenAI

COMPACT_THRESHOLD: int = 3_000
KEEP_RECENT: int = 6


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 2)


def count_context_tokens(history: list[dict], user_input: str) -> int:
    total = _estimate_tokens(user_input)
    for msg in history:
        total += _estimate_tokens(str(msg.get("content") or ""))
        total += _estimate_tokens(str(msg.get("summary") or ""))
    return total


def _summarize_older(older: list[dict], client: "OpenAI", model: str) -> str:
    lines: list[str] = []
    for msg in older:
        role = msg.get("role", "unknown")
        content = str(msg.get("content") or "")
        summary = msg.get("summary")
        if msg.get("type") == "echarts" and summary:
            lines.append(f"{role}（圖表）: {summary}")
        elif content:
            lines.append(f"{role}: {content}")

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
            {"role": "user", "content": f"請摘要以下對話：\n\n{chr(10).join(lines)}"},
        ],
    )
    return response.choices[0].message.content.strip()


def _compact_history(history: list[dict], client: "OpenAI", model: str) -> list[dict]:
    if len(history) <= KEEP_RECENT:
        return list(history)

    older = history[:-KEEP_RECENT]
    recent = history[-KEEP_RECENT:]
    summary_text = _summarize_older(older, client, model)

    return [
        {"role": "user", "content": f"【前段對話摘要】\n{summary_text}"},
        {"role": "assistant", "content": "了解，我已掌握前段對話重點，請繼續。"},
    ] + recent


def maybe_compact(
    history: list[dict],
    user_input: str,
    client: "OpenAI",
    model: str,
) -> list[dict]:
    token_count = count_context_tokens(history, user_input)
    if token_count <= COMPACT_THRESHOLD:
        return list(history)

    print(
        f"[Compactor] Context tokens ≈ {token_count} > {COMPACT_THRESHOLD}，觸發壓縮..."
    )
    compacted = _compact_history(history, client, model)
    print(f"[Compactor] 壓縮完成：{len(history)} → {len(compacted)} 筆訊息")
    return compacted
