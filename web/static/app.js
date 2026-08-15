let allScorecardMetrics = [];

function setTicker(ticker) {
  document.getElementById('tickerInput').value = ticker;
  document.getElementById('taskInput').value = `Analyze financial performance, 10-K revenue disclosures, and CET1 capital ratio for ${ticker}.`;
  
  document.querySelectorAll('.chip').forEach(chip => {
    if (chip.textContent.includes(ticker)) {
      chip.classList.add('active');
    } else {
      chip.classList.remove('active');
    }
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-item').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(content => content.classList.remove('active'));

  const activeBtn = Array.from(document.querySelectorAll('.tab-item')).find(btn => btn.getAttribute('onclick').includes(tabId));
  if (activeBtn) activeBtn.classList.add('active');

  const activePane = document.getElementById(tabId);
  if (activePane) activePane.classList.add('active');
}

function clearTrace() {
  document.getElementById('traceContainer').innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-terminal"></i>
      <h3>Agent Scratchpad Cleared</h3>
      <p>Click <strong>"Execute Agent"</strong> above to trigger new research run.</p>
    </div>
  `;
  document.getElementById('stepCountBadge').textContent = 'Ready';
}

document.getElementById('researchForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const ticker = document.getElementById('tickerInput').value.trim().toUpperCase();
  const task = document.getElementById('taskInput').value.trim();

  const runBtn = document.getElementById('runAgentBtn');
  runBtn.disabled = true;
  runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Executing Agent...</span>';

  const traceContainer = document.getElementById('traceContainer');
  traceContainer.innerHTML = `
    <div class="empty-state">
      <i class="fa-solid fa-circle-notch fa-spin" style="color: var(--accent-blue);"></i>
      <h3>Executing Autonomous Agent Loop for ${ticker}...</h3>
      <p>Reasoning across SEC EDGAR statutory filings and transcript sources.</p>
    </div>
  `;

  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ticker, task})
    });

    const data = await response.json();
    runBtn.disabled = false;
    runBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> <span>Execute Agent</span>';

    if (data.status === 'success') {
      renderTrace(data.steps_trace);
      renderReport(data);
      renderScorecard(data.scorecard);
      loadSavedReports();

      // Update KPI Bar
      document.getElementById('kpiConfidence').textContent = '95.0%';
      document.getElementById('kpiGrade').textContent = `Grade ${data.scorecard.grade} (${data.scorecard.overall_score.toFixed(1)})`;
    } else {
      traceContainer.innerHTML = `<div class="empty-state" style="color: var(--accent-rose);">
        <i class="fa-solid fa-triangle-exclamation"></i>
        <h3>Execution Failed</h3>
        <p>${data.message}</p>
      </div>`;
    }
  } catch (err) {
    runBtn.disabled = false;
    runBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> <span>Execute Agent</span>';
    traceContainer.innerHTML = `<div class="empty-state" style="color: var(--accent-rose);">
      <i class="fa-solid fa-wifi-slash"></i>
      <h3>Network Connection Failure</h3>
      <p>${err.message}</p>
    </div>`;
  }
});

function renderTrace(steps) {
  const container = document.getElementById('traceContainer');
  container.innerHTML = '';
  document.getElementById('stepCountBadge').textContent = `${steps.length} Steps Executed`;

  steps.forEach(s => {
    const card = document.createElement('div');
    card.className = 'step-card';

    let actionHTML = '';
    if (s.action) {
      actionHTML = `<div class="step-action-code">
        <i class="fa-solid fa-play" style="color: var(--accent-gold); margin-right: 6px;"></i>
        Action: <strong>${s.action.name}</strong>(${JSON.stringify(s.action.arguments)})
      </div>`;
    }

    let obsHTML = '';
    if (s.observation) {
      obsHTML = `<div class="step-observation-code">
        <i class="fa-solid fa-database" style="color: var(--accent-emerald); margin-right: 6px;"></i>Observation: ${s.observation}
      </div>`;
    }

    let finalHTML = '';
    if (s.is_final && s.final_answer) {
      finalHTML = `
        <div class="final-answer-box">
          <div class="final-answer-title"><i class="fa-solid fa-circle-check"></i> Final Research Answer</div>
          <div>${s.final_answer}</div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="step-card-header">
        <span class="step-number-tag">Step ${s.step_number} ${s.is_final ? '• Final Answer' : ''}</span>
        <span style="font-size: 0.78rem; color: var(--text-muted);"><i class="fa-solid fa-clock"></i> Executed</span>
      </div>
      <div class="step-thought"><strong>Thought:</strong> ${s.thought}</div>
      ${actionHTML}
      ${obsHTML}
      ${finalHTML}
    `;

    container.appendChild(card);
  });
}

function renderReport(data) {
  const preview = document.getElementById('reportPreviewContainer');
  preview.textContent = data.markdown_report;

  const bar = document.getElementById('reportDownloadBar');
  bar.style.display = 'flex';
  document.getElementById('pdfDownloadLink').href = data.download_pdf_url;
  document.getElementById('mdDownloadLink').href = data.download_md_url;
}

function renderScorecard(sc) {
  const container = document.getElementById('scorecardContainer');
  if (!sc) return;

  allScorecardMetrics = sc.metric_results || [];

  let catHTML = '';
  for (const [cat, score] of Object.entries(sc.category_scores)) {
    catHTML += `
      <div class="metric-box">
        <div class="metric-header">
          <span class="metric-title">${cat}</span>
          <span class="metric-score-tag">${score.toFixed(1)}</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar"><div class="progress-fill" style="width: ${score}%;"></div></div>
        </div>
      </div>
    `;
  }

  let metricsHTML = '';
  allScorecardMetrics.forEach(m => {
    metricsHTML += `
      <div class="metric-box" data-name="${m.metric_name.toLowerCase()}" data-cat="${m.category.toLowerCase()}">
        <div class="metric-header">
          <span class="metric-title">${m.category} → ${m.metric_name}</span>
          <span class="metric-score-tag" style="color: ${m.score >= 85 ? 'var(--accent-emerald)' : 'var(--accent-gold)'};">${m.score.toFixed(1)}</span>
        </div>
        <div class="metric-description">${m.description}</div>
      </div>
    `;
  });

  container.innerHTML = `
    <div class="scorecard-banner">
      <div class="grade-badge">${sc.grade}</div>
      <div>
        <h2 style="font-size: 1.5rem; font-weight: 800;">Overall Evaluation Score: ${sc.overall_score.toFixed(2)} / 100.0</h2>
        <p style="color: var(--text-muted); font-size: 0.85rem;">Systematically scored across 21 named metrics in 7 core categories.</p>
      </div>
    </div>

    <h3 style="font-size: 1rem; color: var(--accent-blue); margin-bottom: 14px;"><i class="fa-solid fa-layer-group"></i> Category Score Breakdown</h3>
    <div class="metrics-grid" style="margin-bottom: 28px;">${catHTML}</div>

    <h3 style="font-size: 1rem; color: var(--accent-blue); margin-bottom: 14px;"><i class="fa-solid fa-list-check"></i> Individual 21 Evaluation Metrics</h3>
    <div class="metrics-grid" id="individualMetricsGrid">${metricsHTML}</div>
  `;
}

function filterScorecardMetrics() {
  const query = document.getElementById('scorecardSearch').value.toLowerCase().trim();
  const boxes = document.querySelectorAll('#individualMetricsGrid .metric-box');

  boxes.forEach(box => {
    const name = box.getAttribute('data-name') || '';
    const cat = box.getAttribute('data-cat') || '';
    if (name.includes(query) || cat.includes(query)) {
      box.style.display = 'block';
    } else {
      box.style.display = 'none';
    }
  });
}

async function loadSavedReports() {
  const container = document.getElementById('savedReportsContainer');
  try {
    const res = await fetch('/api/reports');
    const data = await res.json();

    if (data.reports && data.reports.length > 0) {
      let cardsHTML = '';
      data.reports.forEach(r => {
        const isPdf = r.type === 'PDF';
        const iconClass = isPdf ? 'fa-file-pdf' : 'fa-file-code';
        const colorClass = isPdf ? 'var(--accent-rose)' : 'var(--accent-blue)';

        cardsHTML += `
          <div class="artifact-card">
            <div>
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <i class="fa-solid ${iconClass}" style="color: ${colorClass}; font-size: 1.1rem;"></i>
                <strong style="font-size: 0.95rem;">${r.name}</strong>
              </div>
              <p style="font-size: 0.78rem; color: var(--text-muted);">${r.type} Format • ${(r.size / 1024).toFixed(1)} KB</p>
            </div>
            <a href="${r.download_url}" target="_blank" class="btn-download ${isPdf ? 'pdf' : 'md'}">
              <i class="fa-solid fa-download"></i> Download
            </a>
          </div>
        `;
      });
      container.innerHTML = cardsHTML;
    } else {
      container.innerHTML = '<div class="empty-state"><p>No saved reports in portfolio library.</p></div>';
    }
  } catch (err) {
    container.innerHTML = '<div class="empty-state" style="color: var(--accent-rose);"><p>Failed to load portfolio artifacts.</p></div>';
  }
}

// Initial load
loadSavedReports();
