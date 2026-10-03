/**
 * RetentionIntel - Enterprise People Analytics & Flight Risk Frontend Engine
 */

let summaryData = null;
let sampleProfiles = [];
let currentEmployeeRecord = null;
let deptChartInstance = null;
let tenureChartInstance = null;

// Tab Switching
function switchToTab(tabId) {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
  });
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.toggle('active', content.id === tabId);
  });
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    switchToTab(tab.getAttribute('data-tab'));
  });
});

// Load Overview Summary
async function loadSummary() {
  try {
    const res = await fetch('/api/summary');
    const data = await res.json();
    summaryData = data;

    // Set KPIs
    document.getElementById('kpi-records').textContent = data.records.toLocaleString();
    document.getElementById('kpi-rate').textContent = (data.overall_attrition_rate * 100).toFixed(1) + '%';
    document.getElementById('kpi-left-count').textContent = data.attrition_count.toLocaleString();
    document.getElementById('kpi-loss').textContent = '$' + (data.estimated_turnover_loss / 1000000).toFixed(2) + 'M';
    document.getElementById('kpi-auc').textContent = (data.model_status.roc_auc || 0.833).toFixed(3) + ' AUC';

    // Render Department Cards
    renderDepartmentCards(data.department_analysis);

    // Render Charts
    renderCharts(data);
  } catch (err) {
    console.error('Error loading summary:', err);
  }
}

// Render Department Breakdown Cards
function renderDepartmentCards(deptList) {
  const container = document.getElementById('dept-card-container');
  if (!container || !deptList) return;

  container.innerHTML = deptList.map(d => {
    const ratePct = (d.attrition_rate * 100).toFixed(1);
    const riskBadgeClass = d.attrition_rate >= 0.20 ? 'high' : (d.attrition_rate >= 0.14 ? 'medium' : 'low');
    return `
      <div class="dept-card">
        <div class="card-header">
          <h3>${d.department}</h3>
          <span class="risk-pill ${riskBadgeClass}">${ratePct}% Turnover</span>
        </div>
        <div class="dept-stats-row">
          <div class="dept-stat-box">
            <span>TOTAL HEADCOUNT</span>
            <strong>${d.headcount.toLocaleString()}</strong>
          </div>
          <div class="dept-stat-box">
            <span>AVG SALARY</span>
            <strong>$${Math.round(d.avg_salary).toLocaleString()}/mo</strong>
          </div>
          <div class="dept-stat-box">
            <span>SATISFACTION INDEX</span>
            <strong>${d.avg_satisfaction.toFixed(2)} / 4.0</strong>
          </div>
          <div class="dept-stat-box">
            <span>EST. TURNOVER COST</span>
            <strong>$${Math.round(d.headcount * d.attrition_rate * 28500 / 1000).toLocaleString()}k</strong>
          </div>
        </div>
        <p class="small text-secondary">Primary department retention strategy: Benchmarking grade equity and managing overtime shift demands.</p>
      </div>
    `;
  }).join('');
}

// Render Visualizations (Supports Chart.js and Native Offline Bar Fallback)
function renderCharts(data) {
  let chartJsSuccess = false;

  // Try Chart.js if CDN loaded
  if (typeof Chart !== 'undefined') {
    try {
      const deptCtx = document.getElementById('deptChart');
      if (deptCtx && data.department_analysis) {
        if (deptChartInstance) deptChartInstance.destroy();
        const labels = data.department_analysis.map(d => d.department);
        const rates = data.department_analysis.map(d => (d.attrition_rate * 100).toFixed(1));
        deptChartInstance = new Chart(deptCtx, {
          type: 'bar',
          data: {
            labels: labels,
            datasets: [{
              label: 'Attrition Rate (%)',
              data: rates,
              backgroundColor: ['#3b82f6', '#ec4899', '#10b981'],
              borderRadius: 6,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { callback: v => v + '%' }, grid: { color: 'rgba(255,255,255,0.05)' } },
              x: { grid: { display: false } }
            }
          }
        });
      }

      const tenureCtx = document.getElementById('tenureChart');
      if (tenureCtx && data.tenure_bands) {
        if (tenureChartInstance) tenureChartInstance.destroy();
        const tLabels = data.tenure_bands.map(t => t.band);
        const tRates = data.tenure_bands.map(t => (t.attrition_rate * 100).toFixed(1));
        tenureChartInstance = new Chart(tenureCtx, {
          type: 'line',
          data: {
            labels: tLabels,
            datasets: [{
              label: 'Turnover Rate (%)',
              data: tRates,
              borderColor: '#f59e0b',
              backgroundColor: 'rgba(245, 158, 11, 0.15)',
              fill: true,
              tension: 0.35,
              pointRadius: 5,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, ticks: { callback: v => v + '%' }, grid: { color: 'rgba(255,255,255,0.05)' } },
              x: { grid: { display: false } }
            }
          }
        });
      }
      chartJsSuccess = true;
    } catch (e) {
      console.warn('Chart.js render failed, falling back to native bars:', e);
    }
  }

  // Fallback to Native Responsive HTML5 Bar Component (100% offline & ad-block proof)
  if (!chartJsSuccess) {
    renderNativeCharts(data);
  }
}

function renderNativeCharts(data) {
  const deptWrap = document.getElementById('deptChartWrap');
  if (deptWrap && data.department_analysis) {
    deptWrap.innerHTML = `
      <div class="native-chart-wrap">
        ${data.department_analysis.map(d => {
          const pct = (d.attrition_rate * 100).toFixed(1);
          const colorClass = d.attrition_rate >= 0.20 ? 'danger' : (d.attrition_rate >= 0.15 ? 'warning' : 'primary');
          const widthPct = Math.min(100, Math.max(10, d.attrition_rate * 350));
          return `
            <div class="native-bar-row">
              <div class="native-bar-header">
                <span class="native-bar-title">${d.department} <span class="native-bar-badge">(${d.headcount} employees)</span></span>
                <span class="native-bar-pct text-${colorClass}">${pct}%</span>
              </div>
              <div class="native-bar-track">
                <div class="native-bar-fill ${colorClass}" style="width: ${widthPct}%"></div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  const tenureWrap = document.getElementById('tenureChartWrap');
  if (tenureWrap && data.tenure_bands) {
    tenureWrap.innerHTML = `
      <div class="native-chart-wrap">
        ${data.tenure_bands.map(t => {
          const pct = (t.attrition_rate * 100).toFixed(1);
          const colorClass = t.attrition_rate >= 0.25 ? 'danger' : (t.attrition_rate >= 0.15 ? 'warning' : 'success');
          const widthPct = Math.min(100, Math.max(8, t.attrition_rate * 250));
          return `
            <div class="native-bar-row">
              <div class="native-bar-header">
                <span class="native-bar-title">${t.band} <span class="native-bar-badge">(${t.count} records)</span></span>
                <span class="native-bar-pct text-${colorClass}">${pct}%</span>
              </div>
              <div class="native-bar-track">
                <div class="native-bar-fill ${colorClass}" style="width: ${widthPct}%"></div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }
}

// Load Sample Profiles
async function loadSampleProfiles() {
  try {
    const res = await fetch('/api/sample_employees');
    sampleProfiles = await res.json();
  } catch (err) {
    console.error('Error loading sample profiles:', err);
  }
}

function loadPersona(index) {
  if (!sampleProfiles || !sampleProfiles[index]) return;
  const p = sampleProfiles[index];
  const d = p.data;

  document.getElementById('inp-dept').value = d.Department;
  document.getElementById('inp-role').value = d.JobRole;
  document.getElementById('inp-joblevel').value = d.JobLevel;
  document.getElementById('inp-income').value = d.MonthlyIncome;
  document.getElementById('inp-tenure').value = d.YearsAtCompany;
  document.getElementById('inp-promo').value = d.YearsSinceLastPromotion;
  document.getElementById('inp-mgr').value = d.YearsWithCurrManager;
  document.getElementById('inp-exp').value = d.TotalWorkingYears;
  document.getElementById('inp-stock').value = d.StockOptionLevel;
  document.getElementById('inp-overtime').value = d.OverTime;
  document.getElementById('inp-rating').value = d.PerformanceRating;
  document.getElementById('inp-involvement').value = d.JobInvolvement;
  document.getElementById('inp-jobsat').value = d.JobSatisfaction;
  document.getElementById('inp-wlb').value = d.WorkLifeBalance;
  document.getElementById('inp-travel').value = d.BusinessTravel;

  // Trigger prediction immediately
  document.getElementById('employee-form').dispatchEvent(new Event('submit'));
}

// Predict Form Handler
document.getElementById('employee-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = document.getElementById('btn-predict');
  btn.disabled = true;
  btn.textContent = 'Analyzing Flight Risk & Drivers…';

  const formData = new FormData(e.target);
  const record = Object.fromEntries(formData.entries());

  // Cast numeric fields
  ['JobLevel', 'MonthlyIncome', 'YearsAtCompany', 'YearsSinceLastPromotion',
   'YearsWithCurrManager', 'TotalWorkingYears', 'StockOptionLevel',
   'PerformanceRating', 'JobInvolvement', 'JobSatisfaction', 'WorkLifeBalance'].forEach(k => {
    record[k] = Number(record[k]);
  });

  currentEmployeeRecord = record;

  try {
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record)
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Server returned ${res.status}`);
    }

    const result = await res.json();
    renderDiagnosticResults(result);

    // 1. Display quick status banner below submit button
    const quickEl = document.getElementById('btn-quick-result');
    if (quickEl) {
      quickEl.style.display = 'block';
      const colorClass = result.risk_tier === 'High' ? 'danger' : (result.risk_tier === 'Medium' ? 'warning' : 'success');
      quickEl.className = `btn-quick-result ${colorClass}`;
      quickEl.innerHTML = `
        <strong>Diagnostic Complete:</strong> ${result.risk_tier.toUpperCase()} FLIGHT RISK (${(result.probability * 100).toFixed(1)}%)
        <br><span style="font-size:11.5px; opacity:0.9;">Quadrant: ${result.matrix_evaluation.quadrant} &middot; Detailed breakdown loaded 👉</span>
      `;
    }

    // 2. Pulse highlight & auto-scroll right to the results card
    const resBox = document.getElementById('result-box');
    if (resBox) {
      resBox.classList.remove('highlight-pulse');
      void resBox.offsetWidth; // force DOM reflow
      resBox.classList.add('highlight-pulse');
      resBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  } catch (err) {
    console.error('Prediction failed:', err);
    const quickEl = document.getElementById('btn-quick-result');
    if (quickEl) {
      quickEl.style.display = 'block';
      quickEl.className = 'btn-quick-result danger';
      quickEl.innerHTML = `<strong>Error:</strong> ${err.message || 'Could not connect to model server.'}`;
    }
  } finally {
    btn.disabled = false;
    btn.textContent = '⚡ Run AI Flight Risk Diagnostic';
  }
});

// Render Diagnostic Outputs
function renderDiagnosticResults(data) {
  const prob = (data.probability * 100).toFixed(1);
  document.getElementById('res-prob').textContent = `${prob}%`;
  document.getElementById('res-bar').style.width = `${Math.min(100, data.probability * 100)}%`;

  const tierPill = document.getElementById('res-tier-pill');
  tierPill.textContent = `${data.risk_tier.toUpperCase()} FLIGHT RISK`;
  tierPill.className = `risk-badge ${data.risk_tier.toLowerCase()}`;

  document.getElementById('res-val-score').textContent = `${data.employee_value.score} / 100`;
  document.getElementById('res-val-tier').textContent = data.employee_value.tier;
  document.getElementById('res-cost').textContent = `$${data.estimated_replacement_cost.toLocaleString()}`;

  // 9-Box Matrix placement
  const m = data.matrix_evaluation;
  document.getElementById('matrix-quadrant-title').textContent = m.quadrant;
  document.getElementById('matrix-quadrant-desc').textContent = m.description;
  document.getElementById('matrix-stance').innerHTML = `<strong>HR Recommended Stance:</strong> <span>${m.recommended_stance}</span>`;

  // Root Causes
  const causesList = document.getElementById('root-causes-list');
  if (data.root_causes && data.root_causes.length > 0) {
    causesList.innerHTML = data.root_causes.map(c => `
      <li><strong>${c.factor}:</strong> ${c.detail}</li>
    `).join('');
  } else {
    causesList.innerHTML = `<li>No severe turnover risk factors detected.</li>`;
  }

  // Retention Anchors
  const anchorsList = document.getElementById('retention-anchors-list');
  if (data.retention_anchors && data.retention_anchors.length > 0) {
    anchorsList.innerHTML = data.retention_anchors.map(a => `
      <li><strong>${a.factor}:</strong> ${a.detail}</li>
    `).join('');
  } else {
    anchorsList.innerHTML = `<li>Standard retention inertia.</li>`;
  }

  // Prescriptive Action Checklist
  const actionList = document.getElementById('action-list');
  if (data.recommended_actions && data.recommended_actions.length > 0) {
    actionList.innerHTML = data.recommended_actions.map(act => `
      <li>${act}</li>
    `).join('');
  }

  // Reset simulation outcome on new prediction
  document.getElementById('sim-outcome').style.display = 'none';
}

// "What-If" Scenario Simulator
const simHikeSlider = document.getElementById('sim-hike');
if (simHikeSlider) {
  simHikeSlider.addEventListener('input', (e) => {
    document.getElementById('sim-hike-val').textContent = `+${e.target.value}%`;
  });
}

async function runScenarioSimulation() {
  if (!currentEmployeeRecord) {
    alert('Please run a flight risk diagnostic on an employee first!');
    return;
  }

  const btn = document.getElementById('btn-run-simulation');
  btn.disabled = true;
  btn.textContent = 'Simulating Interventions…';

  const interventions = {
    remove_overtime: document.getElementById('sim-overtime').checked,
    promote_employee: document.getElementById('sim-promotion').checked,
    improve_work_life: document.getElementById('sim-wlb').checked,
    salary_hike_pct: Number(document.getElementById('sim-hike').value)
  };

  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        record: currentEmployeeRecord,
        interventions: interventions
      })
    });

    const sim = await res.json();

    document.getElementById('sim-outcome').style.display = 'block';
    document.getElementById('sim-base-prob').textContent = `${(sim.baseline_probability * 100).toFixed(1)}%`;
    document.getElementById('sim-new-prob').textContent = `${(sim.simulated_probability * 100).toFixed(1)}%`;
    document.getElementById('sim-badge').textContent = `-${sim.relative_risk_reduction_pct}% Risk Drop`;
    document.getElementById('sim-savings').textContent = `$${sim.financial_exposure_saved.toLocaleString()}`;
  } catch (err) {
    console.error('Simulation error:', err);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Simulate Retention Interventions ➔';
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  await loadSummary();
  await loadSampleProfiles();
  // Auto-load first star persona for an instant impressive initial state
  loadPersona(0);
});
