/* ================================================================
   AutoJobApply — Jobs Board Script (js/jobs.js)
================================================================ */

requireAuth();

let allJobs = [];

document.addEventListener('DOMContentLoaded', () => {
  injectSidebar('jobs');
  loadJobs();
});

async function loadJobs() {
  const container = document.getElementById('jobs-container');
  try {
    const res = await api.get('/jobs?limit=50');
    if (res.success) {
      allJobs = res.jobs || [];
      renderJobs(allJobs);
    } else {
      container.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="empty-icon">⚠️</div><h3>Failed to load jobs</h3><p>${res.message}</p></div>`;
    }
  } catch (err) {
    console.error(err);
    container.innerHTML = `<div class="empty-state" style="grid-column:1/-1;"><div class="empty-icon">🔌</div><h3>Connection Error</h3><p>Could not reach the server. Ensure the backend is running.</p></div>`;
  }
}

function renderJobs(jobs) {
  const container = document.getElementById('jobs-container');
  if (!jobs || jobs.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1;">
        <div class="empty-icon">💼</div>
        <h3>No jobs tracked yet</h3>
        <p>Add a custom job URL above, or paste one directly from the Dashboard to begin.</p>
        <button class="btn btn-primary" onclick="openAddJobModal()">+ Add Your First Job</button>
      </div>`;
    return;
  }

  container.innerHTML = '';
  jobs.forEach(job => {
    const card = document.createElement('div');
    card.className = 'job-card fade-in';
    card.innerHTML = `
      <div class="job-card-header">
        <div class="company-logo">${(job.company || 'J')[0].toUpperCase()}</div>
        <div style="flex:1; min-width:0;">
          <div class="job-card-title">${job.title}</div>
          <div class="job-card-company">${job.company || 'Unknown Company'}</div>
        </div>
        ${getStatusBadge(job.status)}
      </div>
      <div class="job-card-meta">
        ${job.location ? `<span class="tag">📍 ${job.location}</span>` : ''}
        ${job.job_type ? `<span class="tag">💼 ${job.job_type}</span>` : ''}
        ${job.salary_range ? `<span class="tag">💰 ${job.salary_range}</span>` : ''}
        <span class="tag">🔗 ${job.source}</span>
      </div>
      ${job.description ? `<p style="font-size:12px; color:var(--text-muted); line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden;">${job.description}</p>` : ''}
      <div class="job-card-footer">
        <span style="font-size:11px; color:var(--text-muted);">${new Date(job.created_at).toLocaleDateString()}</span>
        <div style="display:flex; gap:8px;">
          <a href="${job.job_url}" target="_blank" class="btn btn-ghost btn-sm" title="Open job">🔗</a>
          <button class="btn btn-sm" onclick="startAIAutoApply(${job.id})" style="background: linear-gradient(135deg,#10b981,#059669); color:#fff; border:none; border-radius:6px; cursor:pointer;" title="1-Click AI Apply">⚡ AI Apply</button>
          <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteJob(${job.id})" title="Delete">🗑️</button>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

function getStatusBadge(status) {
  const map = {
    pending: 'badge-yellow',
    saved: 'badge-blue',
    applied: 'badge-green',
    rejected: 'badge-red',
    ignored: 'badge-gray'
  };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

function filterJobs() {
  const search = document.getElementById('job-search').value.toLowerCase();
  const status = document.getElementById('status-filter').value;
  const filtered = allJobs.filter(j => {
    const matchSearch = !search || (j.title || '').toLowerCase().includes(search) || (j.company || '').toLowerCase().includes(search);
    const matchStatus = !status || j.status === status;
    return matchSearch && matchStatus;
  });
  renderJobs(filtered);
}


async function startAIAutoApply(jobId) {
  try {
    showToast('Starting 1-Click AI Auto-Apply...', 'info');
    const res = await api.post('/applications/auto-submit', { job_id: jobId });
    if (res.success && res.application_id) {
      showToast('AI Auto-Apply active! Redirecting to progress window...', 'success');
      setTimeout(() => {
        window.location.href = `apply.html?id=${res.application_id}`;
      }, 1000);
    } else {
      showToast(res.message || 'Failed to start AI Auto-Apply.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Could not trigger AI Auto-Apply.', 'error');
  }
}

async function deleteJob(jobId) {
  if (!confirm('Delete this job listing? This will also remove any applications linked to it.')) return;
  try {
    const res = await api.delete(`/jobs/${jobId}`);
    if (res.success) {
      showToast('Job deleted.');
      allJobs = allJobs.filter(j => j.id !== jobId);
      filterJobs();
    } else {
      showToast('Failed to delete job.', 'error');
    }
  } catch (err) {
    console.error(err);
  }
}

function openAddJobModal() {
  document.getElementById('add-job-modal').classList.add('open');
}
function closeAddJobModal() {
  document.getElementById('add-job-modal').classList.remove('open');
}

async function handleSaveJob(e) {
  e.preventDefault();
  const btn = document.getElementById('save-job-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Saving...';

  const payload = {
    job_url: document.getElementById('add-job-url').value.trim(),
    title: document.getElementById('add-job-title').value.trim() || 'Untitled Job',
    company: document.getElementById('add-job-company').value.trim() || 'Unknown Company',
    location: document.getElementById('add-job-location').value.trim() || 'Not specified',
    source: 'manual'
  };

  try {
    const res = await api.post('/jobs', payload);
    if (res.success) {
      showToast('Job added successfully!', 'success');
      closeAddJobModal();
      document.getElementById('add-job-form').reset();
      loadJobs();
    } else {
      showToast(res.message || 'Failed to add job.', 'error');
    }
  } catch (err) {
    showToast('Error saving job.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Add Job';
  }
}

// ── Source change handler ───────────────────────────────────────────
function onSourceChange() {
  // Easy Apply is only useful for Indeed — show/hide accordingly
  const source = document.getElementById('discover-source').value;
  const wrap = document.getElementById('easy-apply-wrap');
  if (wrap) {
    wrap.style.opacity = (source === 'indeed' || source === 'all') ? '1' : '0.4';
  }
}

async function discoverJobs() {
  const query = document.getElementById('discover-query').value.trim();
  const location = document.getElementById('discover-location').value.trim();
  const experience_level = document.getElementById('discover-experience').value;
  const source = document.getElementById('discover-source').value || 'all';
  const job_type = document.getElementById('discover-jobtype').value;
  const easy_apply_only = document.getElementById('discover-easy-apply')?.checked || false;

  if (!query) {
    showToast('Please enter a job title to search.', 'error');
    return;
  }

  const btn = document.getElementById('discover-btn');
  const resContainer = document.getElementById('discover-results');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Searching...';
  resContainer.style.display = 'block';

  const sourceLabels = { all: 'All Sources', linkedin: 'LinkedIn', indeed: 'Indeed', naukri: 'Naukri', ats: 'ATS (Greenhouse + Lever)' };
  const expLabels = { '': 'Any Level', fresher: 'Fresher/Intern', entry: 'Entry Level', mid: 'Mid Level', senior: 'Senior Level' };
  resContainer.innerHTML = `<div style="text-align:center; padding: 20px; color: var(--text-muted);">
    <span class="spinner" style="margin: 0 auto 12px;"></span><br>
    Searching <strong>${sourceLabels[source] || source}</strong> for <strong>${query}</strong>
    ${experience_level ? ` • ${expLabels[experience_level]}` : ''}
    ${job_type ? ` • ${job_type}` : ''}...<br>
    <span style="font-size: 11px;">This may take 10-30 seconds depending on sources.</span>
  </div>`;

  try {
    const res = await api.post('/jobs/search', {
      query,
      location,
      source,
      experience_level,
      job_type,
      easy_apply_only
    });
    if (res.success && res.jobs && res.jobs.length > 0) {
      renderDiscoverResults(res.jobs, source, experience_level);
    } else {
      resContainer.innerHTML = `<div style="text-align:center; color: var(--status-warning-text); padding: 16px;">
        <span style="font-size: 28px;">🔍</span>
        <p style="margin-top: 8px;">No jobs found matching your filters. Try broadening your search or changing the source.</p>
      </div>`;
    }
  } catch (err) {
    resContainer.innerHTML = `<div style="text-align:center; color: var(--status-error-text); padding: 10px;">Search request failed.</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🚀 Search Jobs';
  }
}

function renderDiscoverResults(jobs, source, experienceLevel) {
  const container = document.getElementById('discover-results');
  const sourceLabels = { all: 'All Sources', linkedin: 'LinkedIn', indeed: 'Indeed', naukri: 'Naukri', ats: 'ATS' };
  const expLabels = { '': '', fresher: 'Fresher/Intern', entry: 'Entry Level', mid: 'Mid Level', senior: 'Senior' };

  container.innerHTML = `<div style="font-size: 13px; font-weight: 600; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
    <span>Found <strong>${jobs.length}</strong> jobs from <strong>${sourceLabels[source] || source}</strong>${experienceLevel ? ` • ${expLabels[experienceLevel]}` : ''}:</span>
  </div>`;
  
  const grid = document.createElement('div');
  grid.style.display = 'flex';
  grid.style.flexDirection = 'column';
  grid.style.gap = '10px';

  const sourceBadgeColors = {
    linkedin_public: { bg: 'rgba(0,119,181,0.12)', color: '#0077B5', label: 'LinkedIn' },
    indeed: { bg: 'rgba(0,91,187,0.12)', color: '#2164f3', label: 'Indeed' },
    naukri: { bg: 'rgba(39,100,238,0.12)', color: '#2764ee', label: 'Naukri' },
    greenhouse: { bg: 'rgba(16,185,129,0.12)', color: '#10b981', label: 'Greenhouse' },
    lever: { bg: 'rgba(255,153,0,0.12)', color: '#ff9900', label: 'Lever' },
  };

  jobs.forEach((job, idx) => {
    const el = document.createElement('div');
    el.style.background = 'var(--bg-input)';
    el.style.padding = '14px 16px';
    el.style.borderRadius = '10px';
    el.style.border = '1px solid var(--border-color)';
    el.style.display = 'flex';
    el.style.justifyContent = 'space-between';
    el.style.alignItems = 'center';
    el.style.gap = '12px';
    el.style.transition = 'border-color 0.2s, transform 0.2s';

    const srcInfo = sourceBadgeColors[job.source] || { bg: 'rgba(107,114,128,0.12)', color: 'var(--text-muted)', label: job.source };
    const easyApplyTag = job.easy_apply ? `<span style="font-size:10px; padding:2px 8px; border-radius:12px; background:rgba(16,185,129,0.15); color:#10b981; font-weight:600;">⚡ Easy Apply</span>` : '';
    
    el.innerHTML = `
      <div style="flex: 1; min-width: 0;">
        <div style="font-weight: 700; font-size: 14px; line-height: 1.3;">${job.title}</div>
        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 3px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
          <span>${job.company}</span> • <span>${job.location}</span>
          <span style="font-size:10px; padding:2px 8px; border-radius:12px; background:${srcInfo.bg}; color:${srcInfo.color}; font-weight:600;">${srcInfo.label}</span>
          ${easyApplyTag}
        </div>
      </div>
      <div style="display: flex; gap: 8px; flex-shrink: 0;">
        <a href="${job.job_url}" target="_blank" class="btn btn-ghost btn-sm" title="View Job">🔗</a>
        <button class="btn btn-primary btn-sm" onclick='oneClickAutoApply(${JSON.stringify(job).replace(/'/g, "&apos;")})' id="auto-btn-${idx}">
          ⚡ Auto-Apply
        </button>
      </div>
    `;
    grid.appendChild(el);
  });
  
  container.appendChild(grid);
}

async function oneClickAutoApply(job) {
  if (!confirm(`Do you want to automatically apply to "${job.title}" at ${job.company}? This will skip manual review.`)) return;
  
  showToast('Starting Auto-Apply flow...', 'info');

  try {
    // 1. Add job to tracking board
    const addRes = await api.post('/jobs', {
      title: job.title,
      company: job.company,
      location: job.location,
      job_url: job.job_url,
      source: 'auto_search'
    });
    
    if (!addRes.success) throw new Error('Failed to save job to board');
    const jobId = addRes.job_id;
    
    // Refresh jobs list to show it pending
    loadJobs();

    // 2. Trigger Auto-Submit immediately (skip review)
    showToast('Submitting application in background...', 'info');
    const subRes = await api.post('/applications/auto-submit', { job_id: jobId });
    
    if (subRes.success) {
      // Redirect to the apply page which will show the polling progress UI since status is 'submitting'
      window.location.href = `apply.html?id=${subRes.application_id}`;
    } else {
      showToast('Failed to start Playwright submission.', 'error');
    }

  } catch (err) {
    showToast(err.message || 'Auto-apply sequence failed.', 'error');
  }
}
