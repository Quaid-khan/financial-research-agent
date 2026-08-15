function setTicker(ticker) {
  document.getElementById('tickerInput').value = ticker;
  document.getElementById('taskInput').value = `Analyze financial performance, 10-K disclosures, and CET1 capital ratio for ${ticker}.`;
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

  event.target.classList.add('active');
  document.getElementById(tabId).classList.add('active');
}

document.getElementById('researchForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const ticker = document.getElementById('tickerInput').value.trim();
  const task = document.getElementById('taskInput').value.trim();

  const runBtn = document.getElementById('runAgentBtn');
  runBtn.disabled = true;
  runBtn.textContent = 'Executing Agent...';

  const traceContainer = document.getElementById('traceContainer');
  traceContainer.innerHTML = '<p style="color: var(--accent-cyan);">🚀 Initializing ReAct Agent control loop for ' + ticker + '...</p>';

  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ticker, task})
    });

    const data = await response.json();
    runBtn.disabled = false;
    runBtn.textContent = 'Run Research';

    if (data.status === 'success') {
      renderTrace(data.steps_trace);
      renderReport(data);
      renderScorecard(data.scorecard);
      loadSavedReports();
    } else {
      traceContainer.innerHTML = '<p style="color: red;">Error: ' + data.message + '</p>';
    }
  } catch (err) {
    runBtn.disabled = false;
    runBtn.textContent = 'Run Research';
    traceContainer.innerHTML = '<p style="color: red;">Network Error: ' + err.message + '</p>';
  }
});

function renderTrace(steps) {
  const container = document.getElementById('traceContainer');
  container.innerHTML = '';
  document.getElementById('stepCountBadge').textContent = `${steps.length} Steps Executed`;

  steps.forEach(s => {
    const stepDiv = document.createElement('div');
    stepDiv.className = 'step-box';

    let actionHTML = '';
    if (s.action) {
      actionHTML = `<div class="action-code">Action: ${s.action.name}(${JSON.stringify(s.action.arguments)})</div>`;
    }

    let obsHTML = '';
    if (s.observation) {
      obsHTML = `<div class="observation-code">Observation:\n${s.observation}</div>`;
    }

    let finalHTML = '';
    if (s.is_final && s.final_answer) {
      finalHTML = `<div style="color: var(--accent-emerald); font-weight: bold; margin-top: 8px;">Final Answer:\n${s.final_answer}</div>`;
    }

    stepDiv.innerHTML = `
      <div class="step-header">Step ${s.step_number} ${s.is_final ? '(FINAL ANSWER)' : ''}</div>
      <div class="thought-text"><strong>Thought:</strong> ${s.thought}</div>
      ${actionHTML}
      ${obsHTML}
      ${finalHTML}
    `;
    container.appendChild(stepDiv);
  });
}

function renderReport(data) {
  document.getElementById('reportPreviewContainer').textContent = data.markdown_report;
  
  const bar = document.getElementById('reportDownloadBar');
  bar.style.display = 'flex';
  document.getElementById('pdfDownloadLink').href = data.download_pdf_url;
  document.getElementById('mdDownloadLink').href = data.download_md_url;
}

function renderScorecard(sc) {
  const container = document.getElementById('scorecardContainer');
  if (!sc) {
    container.innerHTML = '<p style="color: var(--text-muted);">Scorecard data unavailable.</p>';
    return;
  }

  let catHTML = '';
  for (const [cat, score] of Object.entries(sc.category_scores)) {
    catHTML += `
      <div class="metric-card">
        <div class="metric-name">${cat}</div>
        <div class="metric-val">${score.toFixed(1)} / 100</div>
      </div>
    `;
  }

  let metricsHTML = '';
  sc.metric_results.forEach(m => {
    metricsHTML += `
      <div class="metric-card">
        <div class="metric-name">${m.category} → ${m.metric_name}</div>
        <div class="metric-val" style="color: ${m.score >= 85 ? 'var(--accent-emerald)' : 'var(--accent-gold)'};">${m.score.toFixed(1)}</div>
        <div class="metric-desc">${m.description}</div>
      </div>
    `;
  });

  container.innerHTML = `
    <div class="scorecard-header">
      <div class="grade-box">${sc.grade}</div>
      <div>
        <h2 style="font-size: 1.4rem;">Overall Evaluation Score: ${sc.overall_score.toFixed(2)} / 100.0</h2>
        <p style="color: var(--text-muted);">Evaluated across 21 named metrics in 7 core categories.</p>
      </div>
    </div>

    <h3 style="margin-bottom: 12px; color: var(--accent-blue);">Category Score Breakdown</h3>
    <div class="score-metrics-grid" style="margin-bottom: 24px;">${catHTML}</div>

    <h3 style="margin-bottom: 12px; color: var(--accent-blue);">Individual 21 Metrics Scores</h3>
    <div class="score-metrics-grid">${metricsHTML}</div>
  `;
}

async function loadSavedReports() {
  const container = document.getElementById('savedReportsContainer');
  try {
    const res = await fetch('/api/reports');
    const data = await res.json();

    if (data.reports && data.reports.length > 0) {
      let listHTML = '<ul style="list-style: none;">';
      data.reports.forEach(r => {
        listHTML += `
          <li style="padding: 10px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong>${r.name}</strong> <span style="font-size: 0.8rem; color: var(--text-muted);">(${r.type} - ${(r.size / 1024).toFixed(1)} KB)</span>
            </div>
            <a href="${r.download_url}" target="_blank" class="btn-secondary">View / Download</a>
          </li>
        `;
      });
      listHTML += '</ul>';
      container.innerHTML = listHTML;
    } else {
      container.innerHTML = '<p style="color: var(--text-muted);">No reports found.</p>';
    }
  } catch (err) {
    container.innerHTML = '<p style="color: red;">Failed to load saved reports.</p>';
  }
}

// Initial load
loadSavedReports();
