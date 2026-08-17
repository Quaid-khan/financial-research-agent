// Atlas Research Workspace Controller

let currentTheme = localStorage.getItem('atlas_theme') || 'light';
let currentFinancialData = {
  years: [2022, 2023, 2024],
  revenue: [128.695, 158.104, 177.556],
  net_income: [37.676, 49.552, 58.471],
  total_assets: [3665.743, 3875.393, 4002.814],
  total_liabilities: [3373.411, 3547.515, 3658.056]
};
let currentActiveMetric = 'revenue';

// THEME TOGGLE LOGIC (Bright Mode / Dark Mode)
function applyTheme(theme) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('atlas_theme', theme);

  const iconEl = document.getElementById('themeToggleIcon');
  const textEl = document.getElementById('themeToggleText');

  if (theme === 'dark') {
    if (iconEl) iconEl.className = 'fa-solid fa-moon';
    if (textEl) textEl.textContent = 'Dark Mode';
  } else {
    if (iconEl) iconEl.className = 'fa-solid fa-sun';
    if (textEl) textEl.textContent = 'Bright Mode';
  }
}

function toggleTheme() {
  const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
  applyTheme(nextTheme);
  renderChart(); // Redraw chart for contrast
}

// SIDEBAR NAV TAB SWITCHER
function switchNavTab(paneId) {
  document.querySelectorAll('.sidebar-nav .nav-link').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.sidebar-nav .nav-link')).find(
    btn => btn.getAttribute('onclick') && btn.getAttribute('onclick').includes(paneId)
  );
  if (activeBtn) activeBtn.classList.add('active');

  const activePane = document.getElementById(paneId);
  if (activePane) activePane.classList.add('active');
}

// TICKER SELECTION & PROMPT SUGGESTIONS
function setTickerChip(ticker, sector) {
  const input = document.getElementById('tickerSelect');
  if (input) input.value = ticker;

  const promptArea = document.getElementById('promptTextarea');
  if (promptArea) {
    promptArea.value = `Analyze revenue, net income, total assets, and capital ratios for ${ticker} for the last 3 fiscal years.`;
  }
  updateCharCounter();

  document.querySelectorAll('.chip-btn').forEach(chip => {
    if (chip.textContent.trim() === ticker) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });
}

function onTickerSelectChange() {
  const inputVal = document.getElementById('tickerSelect').value.trim().toUpperCase();
  document.querySelectorAll('.chip-btn').forEach(chip => {
    if (chip.textContent.trim() === inputVal) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });
}

function updateCharCounter() {
  const text = document.getElementById('promptTextarea').value;
  document.getElementById('charCounter').textContent = `${text.length} / 500`;
}

// METRIC PILLS & CHART RENDERER
function setChartMetric(metricKey) {
  currentActiveMetric = metricKey;
  document.querySelectorAll('.metric-pill-btn').forEach(btn => {
    if (btn.getAttribute('onclick').includes(metricKey)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
  renderChart();
}

function renderChart() {
  const container = document.getElementById('chartContainer');
  if (!container) return;

  const data = currentFinancialData[currentActiveMetric] || currentFinancialData.revenue;
  const years = currentFinancialData.years || [2022, 2023, 2024];

  const minVal = Math.min(...data) * 0.85;
  const maxVal = Math.max(...data) * 1.15;
  const range = maxVal - minVal || 1;

  // Chart dimensions
  const width = 500;
  const height = 140;
  const paddingX = 60;
  const paddingY = 20;

  const points = data.map((val, idx) => {
    const x = paddingX + (idx * ((width - 2 * paddingX) / (data.length - 1)));
    const y = height - paddingY - (((val - minVal) / range) * (height - 2 * paddingY));
    return { x, y, val, year: years[idx] };
  });

  const pathD = points.reduce((acc, p, idx) => {
    return idx === 0 ? `M ${p.x} ${p.y}` : `${acc} L ${p.x} ${p.y}`;
  }, '');

  const isDark = currentTheme === 'dark';
  const lineColor = isDark ? '#38bdf8' : '#2563eb';
  const gridColor = isDark ? '#1e293b' : '#e2e8f0';
  const textColor = isDark ? '#94a3b8' : '#64748b';

  let svgHtml = `
    <svg class="chart-svg" viewBox="0 0 ${width} ${height}">
      <!-- Horizontal Grid Lines -->
      <line x1="${paddingX}" y1="${paddingY}" x2="${width - paddingX}" y2="${paddingY}" stroke="${gridColor}" stroke-dasharray="4" />
      <line x1="${paddingX}" y1="${height / 2}" x2="${width - paddingX}" y2="${height / 2}" stroke="${gridColor}" stroke-dasharray="4" />
      <line x1="${paddingX}" y1="${height - paddingY}" x2="${width - paddingX}" y2="${height - paddingY}" stroke="${gridColor}" stroke-dasharray="4" />

      <!-- Trend Line -->
      <path d="${pathD}" fill="none" stroke="${lineColor}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />

      <!-- Data Points & Labels -->
      ${points.map(p => `
        <circle cx="${p.x}" cy="${p.y}" r="5" fill="${lineColor}" stroke="${isDark ? '#161f33' : '#ffffff'}" stroke-width="2" />
        <text x="${p.x}" y="${p.y - 12}" fill="${lineColor}" font-size="11" font-weight="700" text-anchor="middle">$${p.val >= 1000 ? (p.val / 1000).toFixed(2) + 'T' : p.val.toFixed(1) + 'B'}</text>
        <text x="${p.x}" y="${height - 2}" fill="${textColor}" font-size="11" font-weight="600" text-anchor="middle">FY ${p.year}</text>
      `).join('')}
    </svg>
  `;

  container.innerHTML = svgHtml;
}

// LIVE API RESEARCH SUBMISSION
document.getElementById('researchForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const ticker = document.getElementById('tickerSelect').value.toUpperCase();
  const task = document.getElementById('promptTextarea').value.trim();

  const runBtn = document.getElementById('runResearchBtn');
  runBtn.disabled = true;
  runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Analyzing...</span>';

  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker, task })
    });

    const data = await response.json();
    runBtn.disabled = false;
    runBtn.innerHTML = '<i class="fa-solid fa-play"></i> <span>Run research</span>';

    if (data.status === 'success') {
      updateOverviewUI(data.report, data.scorecard);
      renderTrace(data.state);
      renderReport(data.report);
      renderScorecard(data.scorecard);
    } else {
      alert(`Research Execution Error: ${data.message}`);
    }
  } catch (err) {
    runBtn.disabled = false;
    runBtn.innerHTML = '<i class="fa-solid fa-play"></i> <span>Run research</span>';
    alert(`Network Connection Failure: ${err.message}`);
  }
});

function updateOverviewUI(report, scorecard) {
  const ticker = report.ticker || '';
  const name = report.company_name || '';

  // Unhide research results container and health card
  const initialBlank = document.getElementById('initialBlankState');
  const resultsContainer = document.getElementById('researchResultsContainer');
  const healthCard = document.getElementById('healthCardContainer');

  if (initialBlank) initialBlank.style.display = 'none';
  if (resultsContainer) resultsContainer.style.display = 'block';
  if (healthCard) healthCard.style.display = 'block';

  // Update Brief Card Header
  document.getElementById('briefLogoBadge').textContent = ticker;
  document.getElementById('briefCompanyName').textContent = name;
  document.getElementById('briefCompanySector').textContent = `${ticker} · Statutory SEC Disclosures`;

  const tag = document.getElementById('briefVerificationTag');
  if (scorecard.system_verified !== false) {
    tag.className = 'verification-tag';
    tag.innerHTML = '<i class="fa-solid fa-circle-check"></i> <span>Citations verified</span>';
  } else {
    tag.className = 'verification-tag';
    tag.style.backgroundColor = 'var(--rose-bg)';
    tag.style.color = 'var(--rose-text)';
    tag.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> <span>Verification issue</span>';
  }

  // Update Financial Series & Chart
  if (report.financial_series) {
    currentFinancialData = report.financial_series;
    renderChart();
  }

  // Update Period & Timestamp Labels
  const years = currentFinancialData.years || [2022, 2023, 2024];
  document.getElementById('briefPeriodLabel').textContent = `Period: FY ${years[0]} - FY ${years[years.length - 1]}`;
  document.getElementById('briefTimestamp').textContent = `Run on ${new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}`;

  // Update Recent Filings Table
  const revVal = currentFinancialData.revenue[currentFinancialData.revenue.length - 1] || 0;
  const niVal = currentFinancialData.net_income[currentFinancialData.net_income.length - 1] || 0;
  const astVal = currentFinancialData.total_assets[currentFinancialData.total_assets.length - 1] || 0;
  const latestYear = years[years.length - 1] || 2024;

  document.getElementById('recentFilingsBody').innerHTML = `
    <tr>
      <td>FY ${latestYear}</td>
      <td>Revenue</td>
      <td><strong>$${revVal >= 1000 ? (revVal / 1000).toFixed(2) + 'T' : revVal.toFixed(2) + 'B'}</strong></td>
      <td><a href="#" class="source-link" onclick="switchNavTab('reportsPane')">10-K (${latestYear}) · Section 3 <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i></a></td>
    </tr>
    <tr>
      <td>FY ${latestYear}</td>
      <td>Net income</td>
      <td><strong>$${niVal >= 1000 ? (niVal / 1000).toFixed(2) + 'T' : niVal.toFixed(2) + 'B'}</strong></td>
      <td><a href="#" class="source-link" onclick="switchNavTab('reportsPane')">10-K (${latestYear}) · Section 3 <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i></a></td>
    </tr>
    <tr>
      <td>FY ${latestYear}</td>
      <td>Total assets</td>
      <td><strong>$${astVal >= 1000 ? (astVal / 1000).toFixed(2) + 'T' : astVal.toFixed(2) + 'B'}</strong></td>
      <td><a href="#" class="source-link" onclick="switchNavTab('reportsPane')">10-K (${latestYear}) · Section 3 <i class="fa-solid fa-arrow-up-right-from-square" style="font-size: 0.75rem;"></i></a></td>
    </tr>
  `;
}

function renderTrace(state) {
  const container = document.getElementById('traceContainer');
  if (!state || !state.steps || state.steps.length === 0) return;

  let html = '';
  state.steps.forEach((step, idx) => {
    html += `
      <div class="trace-card">
        <div class="trace-step-header">
          <span class="step-num">Step ${idx + 1}</span>
          <span class="tool-tag"><i class="fa-solid fa-wrench"></i> ${step.action}</span>
        </div>
        <div class="trace-thought">
          <strong>Thought:</strong> ${step.thought}
        </div>
        ${step.action_input ? `
          <div class="trace-action">
            <pre>Arguments: ${JSON.stringify(step.action_input, null, 2)}</pre>
          </div>
        ` : ''}
        ${step.observation ? `
          <div class="trace-observation">
            <pre>Observation: ${step.observation}</pre>
          </div>
        ` : ''}
      </div>
    `;
  });
  container.innerHTML = html;
}

function renderReport(report) {
  const container = document.getElementById('reportMarkdownContainer');
  if (!report || !report.markdown_content) return;

  document.getElementById('reportHeaderTicker').textContent = report.ticker || 'JPM';
  document.getElementById('pdfDownloadBtn').href = report.pdf_download_url || '#';

  let formattedText = report.markdown_content
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code>$1</code>')
    .replace(/\n\n/gim, '<br><br>');

  container.innerHTML = `<div class="markdown-preview">${formattedText}</div>`;
}

function renderScorecard(scorecard) {
  const container = document.getElementById('scorecardContainer');
  if (!scorecard) return;

  const criticalFailures = scorecard.critical_failures || [];
  const systemVerified = scorecard.system_verified !== false;

  let html = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <div>
        <h2 style="font-size: 1.8rem; font-weight: 800;">${scorecard.overall_score.toFixed(1)} <span style="font-size: 0.9rem; color: var(--text-dim);">/ 100</span></h2>
        <p style="font-size: 0.85rem; color: var(--text-muted);">Overall Evaluation Score</p>
      </div>
      <div style="font-size: 1.5rem; font-weight: 800; color: var(--accent-blue);">
        Grade ${scorecard.grade}
      </div>
    </div>
  `;

  if (criticalFailures.length > 0) {
    html += `
      <div style="background: var(--rose-bg); color: var(--rose-text); padding: 16px; border-radius: 8px; margin-bottom: 20px;">
        <h4 style="font-weight: 700; margin-bottom: 6px;"><i class="fa-solid fa-triangle-exclamation"></i> Critical Validation Failures Detected</h4>
        <ul>${criticalFailures.map(cf => `<li>${cf}</li>`).join('')}</ul>
      </div>
    `;
  }

  html += `
    <table class="filings-table">
      <thead>
        <tr>
          <th>Category</th>
          <th>Metric Name</th>
          <th>Score</th>
          <th>What Good Looks Like</th>
        </tr>
      </thead>
      <tbody>
        ${(scorecard.metric_scores || []).map(m => `
          <tr>
            <td><strong>${m.category}</strong></td>
            <td><code>${m.name}</code></td>
            <td><strong style="color: ${m.score >= 85 ? 'var(--emerald-text)' : 'var(--rose-text)'};">${m.score.toFixed(1)}</strong></td>
            <td>${m.description}</td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  container.innerHTML = html;
}

// TOP MARKET INFORMATION TICKER CONTROLLER
async function loadMarketTicker() {
  const container = document.getElementById('tickerTrackContainer');
  if (!container) return;

  try {
    const resp = await fetch('/api/market-ticker');
    if (!resp.ok) throw new Error('Market ticker API unavailable');
    const data = await resp.json();

    if (data.status === 'success' && data.tickers && data.tickers.length > 0) {
      // Duplicate items array for continuous scrolling marquee
      const items = [...data.tickers, ...data.tickers];
      container.innerHTML = items.map(t => {
        const isUp = t.change >= 0;
        const sign = isUp ? '+' : '';
        const badgeClass = isUp ? 'up' : 'down';
        const icon = isUp ? 'fa-caret-up' : 'fa-caret-down';
        return `
          <div class="ticker-item">
            <span class="ticker-symbol">${t.symbol}</span>
            <span class="ticker-price">$${t.price.toFixed(2)}</span>
            <span class="ticker-badge ${badgeClass}">
              <i class="fa-solid ${icon}"></i> ${sign}${t.percent_change.toFixed(2)}%
            </span>
          </div>
        `;
      }).join('');
    }
  } catch (err) {
    console.warn('Market ticker update error:', err);
  }
}

// VECTOR MEMORY EXPLORER CONTROLLER
async function searchVectorMemory() {
  const inputEl = document.getElementById('memorySearchQuery');
  const resultsContainer = document.getElementById('memorySearchResults');
  if (!inputEl || !resultsContainer) return;

  const query = inputEl.value.trim();
  if (!query) return;

  resultsContainer.innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-spinner fa-spin"></i>
      <h3>Searching Vector Memory...</h3>
      <p>Retrieving semantic embeddings from ChromaDB.</p>
    </div>
  `;

  try {
    const resp = await fetch(`/api/memory/search?q=${encodeURIComponent(query)}`);
    const data = await resp.json();

    if (data.results && data.results.length > 0) {
      resultsContainer.innerHTML = `
        <div style="margin-bottom: 12px; font-weight: 700; color: var(--text-muted);">
          Found ${data.count} stored memory chunks for "${query}"
        </div>
        <div class="filings-table-wrapper">
          <table class="filings-table">
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Source</th>
                <th>Memory Text Chunk</th>
                <th>Relevance Score</th>
              </tr>
            </thead>
            <tbody>
              ${data.results.map(r => `
                <tr>
                  <td><strong>${r.metadata?.ticker || 'N/A'}</strong></td>
                  <td><code>${r.metadata?.source || 'ChromaDB'}</code></td>
                  <td>${r.text}</td>
                  <td><strong style="color: var(--emerald-text);">${((1.0 - (r.distance || 0)) * 100).toFixed(1)}%</strong></td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } else {
      resultsContainer.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-folder-open"></i>
          <h3>No matching vector memory chunks found</h3>
          <p>No stored findings matched your query "${query}". Try another query term.</p>
        </div>
      `;
    }
  } catch (err) {
    resultsContainer.innerHTML = `
      <div class="empty-state">
        <i class="fa-solid fa-triangle-exclamation" style="color: var(--rose-text);"></i>
        <h3>Error Searching Vector Memory</h3>
        <p>${err.message}</p>
      </div>
    `;
  }
}

// TRACE GALLERY CONTROLLER
async function loadTraceGallery() {
  const container = document.getElementById('traceContainer');
  if (!container) return;

  try {
    const resp = await fetch('/api/traces');
    const data = await resp.json();

    if (data.traces && data.traces.length > 0) {
      container.innerHTML = data.traces.map(t => `
        <div class="trace-card">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <h4 style="font-weight: 800; color: var(--text-main); font-size: 1.05rem;">${t.title}</h4>
            <span class="verification-tag" style="background-color: var(--accent-blue-light); color: var(--accent-blue);">
              Score: ${(t.confidence_score * 100).toFixed(0)}%
            </span>
          </div>
          <p style="font-size: 0.85rem; color: var(--text-muted); margin-bottom: 10px;"><strong>Query:</strong> "${t.query}"</p>
          <div style="background-color: var(--bg-card-subtle); padding: 10px 14px; border-radius: 6px; font-size: 0.82rem; color: var(--text-main);">
            <i class="fa-solid fa-lightbulb" style="color: #eab308; margin-right: 6px;"></i> <strong>Key Trace Highlights:</strong> ${t.highlights}
          </div>
        </div>
      `).join('');
    }
  } catch (err) {
    console.warn('Error loading trace gallery:', err);
  }
}

// INITIALIZATION
window.addEventListener('DOMContentLoaded', () => {
  applyTheme(currentTheme);
  updateCharCounter();
  loadMarketTicker();
  loadTraceGallery();
  setInterval(loadMarketTicker, 30000);
});
