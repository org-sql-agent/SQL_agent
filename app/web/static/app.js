/* ── State ──────────────────────────────────────────────────────────────── */
let displayHistory = JSON.parse(localStorage.getItem('displayHistory') || '[]');
let llmHistory     = JSON.parse(localStorage.getItem('llmHistory')     || '[]');

/* ── DOM Refs ───────────────────────────────────────────────────────────── */
const messagesEl  = document.getElementById('messages');
const inputEl     = document.getElementById('user-input');
const sendBtn     = document.getElementById('send-btn');
const clearBtn    = document.getElementById('clear-btn');
const welcomeEl   = document.getElementById('welcome');

/* ── Init ───────────────────────────────────────────────────────────────── */
window.addEventListener('load', () => {
  if (displayHistory.length > 0) {
    welcomeEl.style.display = 'none';
    displayHistory.forEach((msg, i) => renderMessage(msg, i, false));
  }
  scrollToBottom(false);
});

/* ── Hint Buttons ───────────────────────────────────────────────────────── */
document.querySelectorAll('.hint-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    inputEl.value = btn.dataset.hint;
    autoResize();
    inputEl.focus();
  });
});

/* ── Clear ──────────────────────────────────────────────────────────────── */
clearBtn.addEventListener('click', () => {
  if (!confirm('確定要清除所有對話紀錄嗎？')) return;
  displayHistory = [];
  llmHistory = [];
  localStorage.removeItem('displayHistory');
  localStorage.removeItem('llmHistory');
  messagesEl.innerHTML = '';
  messagesEl.appendChild(welcomeEl);
  welcomeEl.style.display = 'flex';
});

/* ── Input: auto-resize & keyboard ─────────────────────────────────────── */
inputEl.addEventListener('input', autoResize);

inputEl.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});

sendBtn.addEventListener('click', handleSend);

function autoResize() {
  inputEl.style.height = 'auto';
  inputEl.style.height = Math.min(inputEl.scrollHeight, 160) + 'px';
}

/* ── Send ───────────────────────────────────────────────────────────────── */
async function handleSend() {
  const text = inputEl.value.trim();
  if (!text || sendBtn.disabled) return;

  // Reset input
  inputEl.value = '';
  autoResize();
  setSending(true);

  // Hide welcome
  welcomeEl.style.display = 'none';

  // Show user message immediately
  const userMsg = { role: 'user', content: text };
  renderMessage(userMsg, displayHistory.length, true);

  // Show loading
  const loadingEl = showLoading();
  scrollToBottom(true);

  try {
    const response = await fetch(SERVICE_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, history: llmHistory }),
    });

    if (!response.ok) throw new Error(`伺服器錯誤：HTTP ${response.status}`);

    const body = await response.json();
    const result = body.data;
    const returnedLlmBase = body.llm_history || [];

    loadingEl.remove();

    // Build & render assistant message
    const assistantMsg = {
      role:    'assistant',
      type:    result.type,
      content: result.content || '',
      summary: result.summary || null,
      ...(result.data ? { data: result.data } : {}),
    };
    renderMessage(assistantMsg, displayHistory.length + 1, true);
    scrollToBottom(true);

    // Persist state
    displayHistory.push(userMsg, assistantMsg);
    llmHistory = [...returnedLlmBase, userMsg, assistantMsg];
    localStorage.setItem('displayHistory', JSON.stringify(displayHistory));
    localStorage.setItem('llmHistory',     JSON.stringify(llmHistory));

  } catch (err) {
    loadingEl.remove();
    renderError(err.message);
    scrollToBottom(true);
  } finally {
    setSending(false);
    inputEl.focus();
  }
}

function setSending(busy) {
  sendBtn.disabled = busy;
  inputEl.disabled = busy;
}

/* ── Render Message ─────────────────────────────────────────────────────── */
function renderMessage(msg, index, animate) {
  const row = document.createElement('div');
  row.className = `message ${msg.role}${animate ? '' : ' no-anim'}`;
  row.dataset.index = index;

  const avatar = document.createElement('div');
  avatar.className = 'avatar';
  avatar.textContent = msg.role === 'user' ? '👤' : '🤖';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.appendChild(buildBubbleContent(msg, index));

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesEl.appendChild(row);

  // Init chart after DOM paint
  if (msg.role === 'assistant' && msg.type === 'echarts') {
    const chartDiv = row.querySelector('.chart-container');
    if (chartDiv) requestAnimationFrame(() => initChart(chartDiv, msg.content));
  }
}

function buildBubbleContent(msg, index) {
  const frag = document.createDocumentFragment();

  if (msg.role === 'user') {
    const p = document.createElement('p');
    p.textContent = msg.content;
    frag.appendChild(p);
    return frag;
  }

  // Assistant: text
  if (msg.type !== 'echarts' && msg.type !== 'image') {
    const p = document.createElement('p');
    p.textContent = msg.content;
    frag.appendChild(p);
    return frag;
  }

  // Assistant: image
  if (msg.type === 'image') {
    const b64 = (msg.data || {}).image_base64;
    if (b64) {
      const img = document.createElement('img');
      img.src = `data:image/png;base64,${b64}`;
      img.style.cssText = 'width:100%;border-radius:8px;';
      frag.appendChild(img);
      if (msg.content) {
        const cap = document.createElement('p');
        cap.className = 'chart-summary';
        cap.textContent = msg.content;
        frag.appendChild(cap);
      }
    } else {
      frag.appendChild(makeErrorEl('圖片資料缺失'));
    }
    return frag;
  }

  // Assistant: echarts
  const chartDiv = document.createElement('div');
  chartDiv.className = 'chart-container';
  chartDiv.id = `chart-${index}-${Date.now()}`;
  frag.appendChild(chartDiv);

  if (msg.summary) {
    const cap = document.createElement('p');
    cap.className = 'chart-summary';
    cap.textContent = msg.summary;
    frag.appendChild(cap);
  }

  return frag;
}

/* ── ECharts ────────────────────────────────────────────────────────────── */
function initChart(container, content) {
  const option = parseJson(content);
  if (!option) {
    container.replaceWith(makeErrorEl('圖表資料解析失敗'));
    return;
  }
  const chart = echarts.init(container, 'dark');
  chart.setOption(option);
  window.addEventListener('resize', () => chart.resize());
}

function parseJson(text) {
  try {
    const cleaned = text.replace(/```json|```/g, '').trim();
    return JSON.parse(cleaned);
  } catch {
    return null;
  }
}

/* ── Loading ────────────────────────────────────────────────────────────── */
function showLoading() {
  const row = document.createElement('div');
  row.className = 'message assistant';

  row.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="bubble">
      <div class="loading-dots">
        <span></span><span></span><span></span>
      </div>
    </div>`;

  messagesEl.appendChild(row);
  return row;
}

/* ── Error ──────────────────────────────────────────────────────────────── */
function renderError(msg) {
  const row = document.createElement('div');
  row.className = 'message assistant';
  row.innerHTML = `
    <div class="avatar">🤖</div>
    <div class="bubble">${makeErrorEl(msg).outerHTML}</div>`;
  messagesEl.appendChild(row);
}

function makeErrorEl(msg) {
  const el = document.createElement('p');
  el.className = 'error-msg';
  el.textContent = `⚠️ ${msg}`;
  return el;
}

/* ── Scroll ─────────────────────────────────────────────────────────────── */
function scrollToBottom(smooth) {
  const container = document.getElementById('chat-container');
  container.scrollTo({
    top: container.scrollHeight,
    behavior: smooth ? 'smooth' : 'instant',
  });
}
