// ===================================================
// FinMind AI - Frontend Controller (app.js)
// Connects to FastAPI backend via REST + WebSockets
// ===================================================

const backendOrigin = (
  window.FINMIND_BACKEND_URL || window.location.origin
).replace(/\/$/, "");
const API_BASE = `${backendOrigin}/api/v1`;
const WS_BASE = `${backendOrigin.replace(/^http/, "ws")}/api/v1/ws`;

let activeTicker = "AAPL";
let priceChart = null;
let liveWS = null; // WebSocket for live price ticks
let authToken = null; // JWT stored in memory (not localStorage for security)

// ===================================================
// 1. TICKER SELECTION
// ===================================================
function selectTicker(ticker) {
  activeTicker = ticker;

  // Highlight active button
  document.querySelectorAll(".ticker-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.textContent.trim() === ticker);
  });

  // Update UI
  loadChartData(ticker, 30);
  connectLiveWS(ticker);
  fetchForecastCache(ticker);
  loadStockMetadata(ticker);
}

// ===================================================
// 2. HISTORICAL PRICE CHART
// ===================================================
async function loadChartData(ticker, days) {
  // Update chart control buttons
  document.querySelectorAll(".ctrl-btn").forEach((btn) => {
    const d = btn.onclick?.toString().match(/\d+/)?.[0];
    btn.classList.toggle("active", d && parseInt(d) === days);
  });

  try {
    const resp = await fetch(
      `${API_BASE}/stocks/${ticker}/prices?limit=${days}`,
    );
    if (!resp.ok) throw new Error("Failed to load price data");
    const prices = await resp.json();

    const labels = prices.map((p) =>
      new Date(p.date).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
    );
    const closes = prices
      .map((p) => Number(p.close_price))
      .filter(Number.isFinite);

    // Update company + price info
    document.getElementById("ticker-badge").textContent = ticker;
    if (closes.length > 0) {
      const latest = closes[closes.length - 1];
      const prev = closes[closes.length - 2] || latest;
      const change = latest - prev;
      const pct = ((change / prev) * 100).toFixed(2);
      document.getElementById("live-price").textContent =
        `$${latest.toFixed(2)}`;
      document.getElementById("fc-actual").textContent =
        `$${latest.toFixed(2)}`;
      const changeEl = document.getElementById("price-change");
      const symbol = change >= 0 ? "▲" : "▼";
      changeEl.textContent = `${symbol} ${change >= 0 ? "+" : ""}$${change.toFixed(2)} (${change >= 0 ? "+" : ""}${pct}%)`;
      changeEl.className =
        "price-change " + (change >= 0 ? "bullish" : "bearish");
    }

    renderLineChart(labels, closes);
  } catch (err) {
    console.warn("Chart load error:", err);
  }
}

async function loadStockMetadata(ticker) {
  try {
    const resp = await fetch(`${API_BASE}/stocks/${ticker}`);
    if (!resp.ok) return;
    const stock = await resp.json();
    document.getElementById("company-name").textContent = stock.name || ticker;
    document.getElementById("sector-tag").textContent =
      stock.sector || "Market data";
  } catch (err) {
    console.warn("Stock metadata load error:", err);
  }
}

function renderLineChart(labels, data) {
  const ctx = document.getElementById("price-chart").getContext("2d");
  if (priceChart) priceChart.destroy();

  const isUp = data[data.length - 1] >= data[0];
  const gradient = ctx.createLinearGradient(0, 0, 0, 300);
  gradient.addColorStop(
    0,
    isUp ? "rgba(0,255,136,0.3)" : "rgba(255,68,68,0.3)",
  );
  gradient.addColorStop(1, "rgba(0,0,0,0)");

  priceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Close Price",
          data,
          borderColor: isUp ? "#00ff88" : "#ff4444",
          backgroundColor: gradient,
          borderWidth: 2,
          pointRadius: 0,
          fill: true,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: { label: (ctx) => ` $${ctx.raw.toFixed(2)}` },
        },
      },
      scales: {
        x: {
          ticks: { color: "#64748b", maxTicksLimit: 8 },
          grid: { color: "#1a2744" },
        },
        y: {
          ticks: { color: "#64748b", callback: (v) => `$${v.toFixed(0)}` },
          grid: { color: "#1a2744" },
        },
      },
    },
  });
}

// ===================================================
// 3. LIVE WEBSOCKET PRICE TICKS
// ===================================================
function connectLiveWS(ticker) {
  if (liveWS) {
    liveWS.close();
    liveWS = null;
  }

  liveWS = new WebSocket(`${WS_BASE}/stock-ticks/${ticker}`);

  liveWS.onmessage = (event) => {
    const data = JSON.parse(event.data);
    const price = Number(data.last_price ?? data.price);
    if (!Number.isFinite(price)) return;
    const priceEl = document.getElementById("live-price");
    if (priceEl) priceEl.textContent = `$${price.toFixed(2)}`;
    priceEl?.classList.remove("tick-up", "tick-down");
    priceEl?.classList.add(
      price >= Number(priceEl.dataset.previousPrice || price)
        ? "tick-up"
        : "tick-down",
    );
    if (priceEl) priceEl.dataset.previousPrice = price;
  };

  liveWS.onerror = () => {
    document.getElementById("live-badge").textContent = "● OFFLINE";
  };

  liveWS.onopen = () => {
    document.getElementById("live-badge").textContent = "● LIVE";
    document.getElementById("live-badge").style.color = "#00ff88";
  };
}

// ===================================================
// 4. LSTM FORECAST
// ===================================================
async function runForecast() {
  const btn = document.querySelector(".forecast-card .run-btn");
  btn.textContent = "...";
  try {
    // Step 1: Train the model (or load checkpoint)
    const trainResp = await fetch(
      `${API_BASE}/predictions/${activeTicker}/train`,
      { method: "POST" },
    );
    if (!trainResp.ok)
      throw new Error((await trainResp.json()).detail || "Training failed");

    // Step 2: Get next-day forecast
    const fcResp = await fetch(
      `${API_BASE}/predictions/${activeTicker}/forecast`,
    );
    if (!fcResp.ok)
      throw new Error((await fcResp.json()).detail || "Forecast failed");
    const fc = (await fcResp.json()).forecast;

    const predicted = Number(fc.predicted_next_day_price);
    const actual = parseFloat(fc.last_actual_price);
    const change = predicted - actual;
    const pct = ((change / actual) * 100).toFixed(2);
    const isBullish = change >= 0;

    document.getElementById("fc-actual").textContent = `$${actual.toFixed(2)}`;
    document.getElementById("fc-predicted").textContent =
      `$${predicted.toFixed(2)}`;
    document.getElementById("fc-change").textContent =
      `${change >= 0 ? "+" : ""}$${change.toFixed(2)} (${change >= 0 ? "+" : ""}${pct}%)`;
    document.getElementById("fc-change").className =
      "forecast-value " + (isBullish ? "bullish" : "bearish");

    const sigEl = document.getElementById("fc-signal");
    sigEl.textContent = fc.trend_direction;
    sigEl.className =
      "signal-badge " + (isBullish ? "bullish-badge" : "bearish-badge");
  } catch (err) {
    console.error("Forecast error:", err);
    const signalEl = document.getElementById("fc-signal");
    signalEl.textContent = "ERROR";
    signalEl.className = "signal-badge bearish-badge";
    signalEl.title = err.message;
  }
  btn.textContent = "▶ Run";
}

async function fetchForecastCache(ticker) {
  try {
    const fcResp = await fetch(`${API_BASE}/predictions/${ticker}/forecast`);
    if (!fcResp.ok) return;
    const payload = await fcResp.json();
    const fc = payload.forecast;

    const predicted = Number(fc.predicted_next_day_price);
    const actual = parseFloat(fc.last_actual_price);
    const change = predicted - actual;
    const isBullish = change >= 0;

    document.getElementById("fc-predicted").textContent =
      `$${predicted.toFixed(2)}`;
    const pct = ((change / actual) * 100).toFixed(2);
    document.getElementById("fc-change").textContent =
      `${change >= 0 ? "+" : ""}$${change.toFixed(2)} (${pct}%)`;
    document.getElementById("fc-change").className =
      "forecast-value " + (isBullish ? "bullish" : "bearish");
    const sigEl = document.getElementById("fc-signal");
    sigEl.textContent = fc.trend_direction;
    sigEl.className =
      "signal-badge " + (isBullish ? "bullish-badge" : "bearish-badge");
  } catch (e) {}
}

// ===================================================
// 5. FINBERT SENTIMENT ANALYZER
// ===================================================
async function analyzeSentiment() {
  const headline = document.getElementById("headline-input").value.trim();
  if (!headline) return;

  try {
    const resp = await fetch(`${API_BASE}/genai/sentiment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ headlines: [headline] }),
    });
    if (!resp.ok)
      throw new Error((await resp.json()).detail || "Sentiment request failed");
    const payload = await resp.json();
    const data = payload.results?.[0] || {};

    // Show results
    document.getElementById("sentiment-result").classList.remove("hidden");

    const label =
      data.sentiment || data.sentiment_label || data.label || "NEUTRAL";
    const conf = Number(data.confidence ?? data.score ?? 0);
    const pos = Number(data.probabilities?.positive ?? data.positive ?? 0);
    const neg = Number(data.probabilities?.negative ?? data.negative ?? 0);
    const neu = Number(data.probabilities?.neutral ?? data.neutral ?? 0);

    const labelEl = document.getElementById("sentiment-label-val");
    labelEl.textContent = label.toUpperCase();
    labelEl.className =
      "signal-badge " +
      (label.toLowerCase() === "positive"
        ? "bullish-badge"
        : label.toLowerCase() === "negative"
          ? "bearish-badge"
          : "signal-badge");
    document.getElementById("sentiment-conf").textContent =
      `${(conf * 100).toFixed(1)}%`;

    document.getElementById("bar-pos").style.width =
      `${(pos * 100).toFixed(1)}%`;
    document.getElementById("bar-neg").style.width =
      `${(neg * 100).toFixed(1)}%`;
    document.getElementById("bar-neu").style.width =
      `${(neu * 100).toFixed(1)}%`;
    document.getElementById("pos-pct").textContent =
      `${(pos * 100).toFixed(1)}%`;
    document.getElementById("neg-pct").textContent =
      `${(neg * 100).toFixed(1)}%`;
    document.getElementById("neu-pct").textContent =
      `${(neu * 100).toFixed(1)}%`;
  } catch (err) {
    console.error("Sentiment error:", err);
  }
}

// ===================================================
// 6. AI COPILOT (RAG)
// ===================================================
async function sendCopilotQuery() {
  const input = document.getElementById("copilot-input");
  const query = input.value.trim();
  if (!query) return;
  input.value = "";

  appendCopilotMessage(query, "user");
  const thinkingEl = appendCopilotMessage("Thinking...", "ai");

  try {
    const resp = await fetch(`${API_BASE}/genai/copilot/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, ticker: activeTicker }),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.detail || "Copilot request failed");
    thinkingEl.textContent =
      data.answer ||
      data.response ||
      data.response_text ||
      "I could not find an answer.";
  } catch (err) {
    thinkingEl.textContent = "Error connecting to AI Copilot.";
  }
}

function appendCopilotMessage(text, role) {
  const chat = document.getElementById("copilot-chat");
  const msg = document.createElement("div");
  msg.className = `copilot-msg ${role}`;
  msg.textContent = text;
  chat.appendChild(msg);
  chat.scrollTop = chat.scrollHeight;
  return msg;
}

// ===================================================
// 7. AUTH - LOGIN & REGISTER
// ===================================================
function openAuthModal() {
  document.getElementById("auth-modal").classList.remove("hidden");
}
function closeAuthModal() {
  document.getElementById("auth-modal").classList.add("hidden");
}

function switchTab(tab) {
  document
    .getElementById("login-tab")
    .classList.toggle("hidden", tab !== "login");
  document
    .getElementById("register-tab")
    .classList.toggle("hidden", tab !== "register");
  document.querySelectorAll(".tab-btn").forEach((btn, i) => {
    btn.classList.toggle(
      "active",
      (tab === "login" && i === 0) || (tab === "register" && i === 1),
    );
  });
}

async function doLogin() {
  const email = document.getElementById("login-email").value.trim();
  const pass = document.getElementById("login-password").value;
  clearAuthError();

  const form = new FormData();
  form.append("username", email);
  form.append("password", pass);

  try {
    const resp = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      body: form,
    });
    const data = await resp.json();
    if (!resp.ok) return showAuthError(data.detail || "Login failed");

    authToken = data.access_token;
    document.getElementById("auth-btn").textContent =
      `Hi, ${data.user_name.split(" ")[0]}`;
    closeAuthModal();
    loadPortfolio();
  } catch (err) {
    showAuthError("Server error. Is the backend running?");
  }
}

async function doRegister() {
  const name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const pass = document.getElementById("reg-password").value;
  clearAuthError();

  try {
    const resp = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, full_name: name, password: pass }),
    });
    const data = await resp.json();
    if (!resp.ok) return showAuthError(data.detail || "Registration failed");

    authToken = data.access_token;
    document.getElementById("auth-btn").textContent =
      `Hi, ${data.user_name.split(" ")[0]}`;
    closeAuthModal();
    loadPortfolio();
  } catch (err) {
    showAuthError("Server error. Is the backend running?");
  }
}

function showAuthError(msg) {
  const el = document.getElementById("auth-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}
function clearAuthError() {
  document.getElementById("auth-error").classList.add("hidden");
}

// ===================================================
// 8. PORTFOLIO
// ===================================================
async function loadPortfolio() {
  if (!authToken) return;

  try {
    const resp = await fetch(`${API_BASE}/portfolio/`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    const items = await resp.json();
    renderPortfolio(items);
  } catch (err) {
    console.warn("Portfolio load error:", err);
  }
}

function renderPortfolio(items) {
  const body = document.getElementById("portfolio-body");
  if (!items.length) {
    body.innerHTML = `<div class="portfolio-empty">No positions yet. Click + Add to get started.</div>`;
    return;
  }
  body.innerHTML = items
    .map((item) => {
      const pl = item.profit_loss || 0;
      const pct = item.profit_loss_pct || 0;
      const isPos = pl >= 0;
      return `<div class="portfolio-item">
      <div class="portfolio-item-header">
        <span class="portfolio-ticker">${item.ticker}</span>
        <span class="portfolio-pl ${isPos ? "bullish" : "bearish"}">${isPos ? "+" : ""}$${pl.toFixed(2)} (${isPos ? "+" : ""}${pct.toFixed(2)}%)</span>
      </div>
      <div style="display:flex; justify-content:space-between; margin-top:4px; font-size:12px; color:#64748b;">
        <span>${item.shares_owned} shares @ $${item.buy_price.toFixed(2)}</span>
        <span>Now: $${(item.current_price || item.buy_price).toFixed(2)}</span>
      </div>
    </div>`;
    })
    .join("");
}

function showAddPosition() {
  if (!authToken) {
    openAuthModal();
    return;
  }
  const ticker = prompt("Ticker symbol (e.g. AAPL):");
  if (!ticker) return;
  const shares = parseFloat(prompt("Number of shares:") || "0");
  const price = parseFloat(prompt("Your buy price per share ($):") || "0");
  if (!shares || !price) return;
  buyStock(ticker.toUpperCase(), shares, price);
}

async function buyStock(ticker, shares, buy_price) {
  try {
    const resp = await fetch(`${API_BASE}/portfolio/buy`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${authToken}`,
      },
      body: JSON.stringify({ ticker, shares, buy_price }),
    });
    const data = await resp.json();
    if (resp.ok) {
      alert(data.message);
      loadPortfolio();
    } else alert(data.detail || "Failed to add position.");
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ===================================================
// INIT ON PAGE LOAD
// ===================================================
window.addEventListener("DOMContentLoaded", () => {
  loadChartData(activeTicker, 30);
  connectLiveWS(activeTicker);
  fetchForecastCache(activeTicker);
  loadStockMetadata(activeTicker);
});
