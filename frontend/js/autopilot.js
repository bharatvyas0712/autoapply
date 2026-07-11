/* ================================================================
   AutoJobApply — AI Auto-Pilot Script (js/autopilot.js)
================================================================ */

requireAuth();

let lastMatches = [];

document.addEventListener('DOMContentLoaded', () => {
  injectSidebar('autopilot');
  toggleEasyApplyOption();
});

function toggleEasyApplyOption() {
  const source = document.getElementById('agent-source').value;
  const group = document.getElementById('easy-apply-group');
  group.style.display = (source === 'indeed') ? 'block' : 'none';
  if (source !== 'indeed') document.getElementById('agent-easy-apply').checked = false;
}

async function runAgent() {
  const btn = document.getElementById('agent-run-btn');
  const statusEl = document.getElementById('agent-status');
  const resultsEl = document.getElementById('agent-results');

  const payload = {
    query: document.getElementById('agent-query').value.trim() || undefined,
    location: document.getElementById('agent-location').value.trim() || undefined,
    min_score: parseInt(document.getElementById('agent-minscore').value, 10) || 0,
    source: document.getElementById('agent-source').value,
    easy_apply_only: document.getElementById('agent-source').value === 'indeed'
      && document.getElementById('agent-easy-apply').checked,
  };

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Running...';
  resultsEl.innerHTML = '';
  statusEl.style.display = 'block';
  statusEl.innerHTML = '<span class="spinner" style="margin:0 auto 12px;"></span><br>🤖 Reading your resume, searching & scoring matches… (this reads each job\'s full description for accurate scoring, can take 1–3 min)';

  try {
    const res = await api.post('/agent/run', payload);
    statusEl.style.display = 'none';

    if (!res.success) {
      resultsEl.innerHTML = emptyBox('⚠️', 'Agent could not run', res.message || 'Unknown error.');
      return;
    }
    if (!res.matches || res.matches.length === 0) {
      resultsEl.innerHTML = emptyBox('🔍', 'No strong matches', res.message ||
        `Searched but nothing crossed your ${payload.min_score}% threshold. Try lowering it or changing the role.`);
      return;
    }
    lastMatches = res.matches;
    renderMatches(res);
  } catch (err) {
    statusEl.style.display = 'none';
    resultsEl.innerHTML = emptyBox('🔌', 'Connection Error', 'Could not reach the server.');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '⚡ Run Agent';
  }
}

function renderMatches(res) {
  const resultsEl = document.getElementById('agent-results');
  const header = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:12px;">
      <div style="font-weight:700;">
        ✅ ${res.shortlisted} matches for “${escapeHtml(res.query)}” in ${escapeHtml(res.location)}
        <span style="color:var(--text-muted); font-weight:400; font-size:13px;">(scanned ${res.searched})</span>
      </div>
      <div style="display:flex; gap:8px; align-items:center;">
        <button class="btn btn-ghost btn-sm" onclick="toggleSelectAll(true)">Select all</button>
        <button class="btn btn-primary btn-sm" id="batch-apply-btn" onclick="batchAutoApply()">⚡ Auto-Apply Selected (0)</button>
      </div>
    </div>`;

  const cards = res.matches.map((m, i) => {
    const ringColor = m.fit_score >= 70 ? '#2ea043' : m.fit_score >= 50 ? '#FF9900' : '#d29922';
    const matchedChips = (m.matched_skills || []).slice(0, 12)
      .map(s => `<span class="skill-chip chip-match">✓ ${escapeHtml(s)}</span>`).join('') || '<span style="font-size:12px;color:var(--text-muted);">No overlapping skills detected</span>';
    const missingChips = (m.missing_skills || []).slice(0, 8)
      .map(s => `<span class="skill-chip chip-miss">${escapeHtml(s)}</span>`).join('');

    return `
      <div class="card" style="margin-bottom:14px;" id="match-card-${i}" data-job-id="${m.job_id}">
        <div style="display:flex; gap:16px; align-items:flex-start;">
          <input type="checkbox" class="match-check" data-idx="${i}" onchange="updateBatchCount()" style="width:18px; height:18px; margin-top:4px; cursor:pointer;">
          <div class="fit-ring" style="--pct:${m.fit_score}; --ring-color:${ringColor};">
            <span>${m.fit_score}%</span>
          </div>
          <div style="flex:1; min-width:0;">
            <div style="font-weight:700; font-size:15px;">${escapeHtml(m.title)}</div>
            <div style="font-size:13px; color:var(--text-secondary);">${escapeHtml(m.company)} • ${escapeHtml(m.location)}</div>
            ${m.description ? `<p style="font-size:12px; color:var(--text-muted); margin:8px 0 0; line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">${escapeHtml(m.description)}</p>` : ''}
            <div style="margin-top:10px;">${matchedChips}</div>
            ${missingChips ? `<div style="margin-top:6px;"><span style="font-size:11px; color:var(--text-muted);">Job also wants:</span> ${missingChips}</div>` : ''}
          </div>
        </div>
        <div class="job-card-footer" style="margin-top:14px;">
          <span class="status-slot">${m.already_tracked ? '<span class="badge badge-blue">already tracked</span>' : ''} ${m.easy_apply ? '<span class="badge badge-green">⚡ Easy Apply</span>' : ''}</span>
          <div style="display:flex; gap:8px;">
            <a href="${m.job_url}" target="_blank" class="btn btn-ghost btn-sm" title="View job">🔗 View</a>
            <button class="btn btn-secondary btn-sm" onclick="skipJob(${i})">Skip</button>
            <button class="btn btn-primary btn-sm" onclick="approveAndApply(${m.job_id}, this)">⚡ AI Auto-Apply</button>
          </div>
        </div>
      </div>`;
  }).join('');

  resultsEl.innerHTML = header + cards;
  updateBatchCount();
}

// ── Single job: go through the manual review screen ──────────────
async function approveAndApply(jobId, btn) {
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Preparing…';
  try {
    const res = await api.post('/applications/auto-submit', { job_id: jobId });
    if (res.success && res.application_id) {
      window.location.href = `apply.html?id=${res.application_id}`;
    } else {
      showToast(res.message || 'Could not prepare application.', 'error');
      btn.disabled = false;
      btn.innerHTML = '⚡ AI Auto-Apply';
    }
  } catch (err) {
    showToast('Network error while starting auto-apply.', 'error');
    btn.disabled = false;
    btn.innerHTML = '⚡ AI Auto-Apply';
  }
}

// ── Selection helpers ────────────────────────────────────────────
function getSelectedIdxs() {
  return [...document.querySelectorAll('.match-check:checked')].map(c => parseInt(c.dataset.idx, 10));
}

function updateBatchCount() {
  const n = getSelectedIdxs().length;
  const btn = document.getElementById('batch-apply-btn');
  if (btn) {
    btn.textContent = `⚡ Auto-Apply Selected (${n})`;
    btn.disabled = n === 0;
  }
}

function toggleSelectAll(state) {
  document.querySelectorAll('.match-check').forEach(c => {
    if (!c.disabled) c.checked = state;
  });
  updateBatchCount();
}

function skipJob(idx) {
  const card = document.getElementById(`match-card-${idx}`);
  if (!card) return;
  card.style.opacity = '0.4';
  const chk = card.querySelector('.match-check');
  if (chk) { chk.checked = false; chk.disabled = true; }
  card.querySelectorAll('.job-card-footer button').forEach(b => b.disabled = true);
  updateBatchCount();
}

// ── Batch: prepare + auto-submit each selected job in the background ──
async function batchAutoApply() {
  const idxs = getSelectedIdxs();
  if (!idxs.length) return;

  if (!confirm(`Auto-apply to ${idxs.length} selected job(s)? This fills & submits each form via the automation browser WITHOUT the manual review step.`)) return;

  const runBtn = document.getElementById('batch-apply-btn');
  const selBtn = runBtn.previousElementSibling;
  runBtn.disabled = true; if (selBtn) selBtn.disabled = true;
  document.querySelectorAll('.match-check').forEach(c => c.disabled = true);

  let ok = 0, fail = 0;
  for (const idx of idxs) {
    const card = document.getElementById(`match-card-${idx}`);
    const slot = card ? card.querySelector('.status-slot') : null;
    const jobId = card ? parseInt(card.dataset.jobId, 10) : null;
    if (!jobId) continue;

    if (slot) slot.innerHTML = '<span class="spinner" style="width:14px;height:14px;"></span> submitting…';
    try {
      const sub = await api.post('/applications/auto-submit', { job_id: jobId });
      if (!sub.success || !sub.application_id) throw new Error(sub.message || 'submit failed');

      ok++;
      if (slot) slot.innerHTML = '<span class="badge badge-green">submitted →</span> <a href="apply.html?id=' + sub.application_id + '" style="font-size:12px;">track</a>';
    } catch (err) {
      fail++;
      if (slot) slot.innerHTML = `<span class="badge badge-red">failed</span> <span style="font-size:11px;color:var(--text-muted);">${escapeHtml(err.message || '')}</span>`;
    }
  }

  showToast(`Batch done: ${ok} submitted, ${fail} failed.`, fail ? 'warning' : 'success');
  runBtn.textContent = '✅ Batch finished';
}

function emptyBox(icon, title, msg) {
  return `<div class="empty-state"><div class="empty-icon">${icon}</div><h3>${title}</h3><p>${escapeHtml(msg)}</p></div>`;
}

function escapeHtml(str) {
  return String(str || '').replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}