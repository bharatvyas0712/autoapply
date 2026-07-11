/* ================================================================
   AutoJobApply — Application History Script (js/history.js)
================================================================ */

requireAuth();

let allApps = [];

document.addEventListener('DOMContentLoaded', () => {
  injectSidebar('history');
  loadHistory();
});

async function loadHistory() {
  const tbody = document.getElementById('history-tbody');
  try {
    const res = await api.get('/applications?limit=100');
    if (res.success) {
      allApps = res.applications || [];
      renderHistory(allApps);
    } else {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--status-error-text); padding:24px;">${res.message}</td></tr>`;
    }
  } catch (err) {
    console.error(err);
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--status-error-text); padding:24px;">Network error loading history.</td></tr>`;
  }
}

function renderHistory(apps) {
  const tbody = document.getElementById('history-tbody');
  if (!apps || apps.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="padding:48px; text-align:center;">
          <div style="font-size:40px; margin-bottom:12px;">📋</div>
          <h3 style="font-weight:700; font-size:16px;">No Applications Yet</h3>
          <p style="color:var(--text-muted); font-size:13px; margin-top:6px;">Applications you submit will appear here.</p>
          <a href="jobs.html" class="btn btn-primary" style="margin-top:16px;">Browse Jobs</a>
        </td>
      </tr>`;
    return;
  }

  const statusBadges = {
    draft: '<span class="badge badge-gray">Draft</span>',
    review: '<span class="badge badge-yellow">Review</span>',
    submitting: '<span class="badge badge-blue">Submitting</span>',
    submitted: '<span class="badge badge-green">✓ Submitted</span>',
    failed: '<span class="badge badge-red">✗ Failed</span>'
  };

  tbody.innerHTML = '';
  apps.forEach((app, idx) => {
    const submittedDate = app.submitted_at
      ? new Date(app.submitted_at).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
      : '—';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="color:var(--text-muted); font-size:12px; width:50px;">${idx + 1}</td>
      <td style="font-weight:600; color:var(--text-primary);">${app.title || '—'}</td>
      <td>${app.company || '—'}</td>
      <td>${statusBadges[app.status] || `<span class="badge badge-gray">${app.status}</span>`}</td>
      <td style="font-size:12px; color:var(--text-muted);">${submittedDate}</td>
      <td>
        <div style="display:flex; gap:6px;">
          <button class="btn btn-secondary btn-sm" onclick="openDetailModal(${app.id})">View</button>
          ${app.status !== 'submitting' ? `<button class="btn btn-ghost btn-sm" onclick="openEdit(${app.id})">Edit</button>` : ''}
          <button class="btn btn-danger btn-sm" onclick="deleteApp(${app.id})">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterHistory() {
  const search = document.getElementById('hist-search').value.toLowerCase();
  const status = document.getElementById('hist-status-filter').value;
  const filtered = allApps.filter(a => {
    const matchSearch = !search || (a.title || '').toLowerCase().includes(search) || (a.company || '').toLowerCase().includes(search);
    const matchStatus = !status || a.status === status;
    return matchSearch && matchStatus;
  });
  renderHistory(filtered);
}

async function openDetailModal(appId) {
  const modal = document.getElementById('detail-modal');
  const body = document.getElementById('detail-modal-body');
  body.innerHTML = `<div style="text-align:center; padding:40px;"><span class="spinner" style="margin:0 auto;"></span></div>`;
  modal.classList.add('open');

  try {
    const res = await api.get(`/applications/${appId}`);
    if (res.success) {
      const app = res.application;
      const fd = app.form_data || {};
      const qa = app.custom_qa || [];

      document.getElementById('detail-modal-title').innerText = `${app.title} — ${app.company}`;
      document.getElementById('detail-reapply-btn').onclick = () => openEdit(appId);

      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:16px;">
          <div>
            <h4 style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:10px;">Submitted Form Data</h4>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px;">
              ${Object.entries(fd).filter(([k]) => k !== 'resume_url').map(([k, v]) => `
                <div style="background:var(--bg-input); border-radius:8px; padding:10px;">
                  <div style="font-size:10px; font-weight:700; color:var(--text-muted); text-transform:uppercase;">${k.replace(/_/g,' ')}</div>
                  <div style="font-size:13px; color:var(--text-primary); margin-top:3px;">${v || '—'}</div>
                </div>
              `).join('')}
            </div>
          </div>

          ${qa.length ? `
          <div>
            <h4 style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:10px;">Q&A Answers</h4>
            ${qa.map(q => `
              <div style="background:var(--bg-input); border-radius:8px; padding:10px; margin-bottom:8px;">
                <div style="font-size:12px; color:var(--text-secondary);">${q.question}</div>
                <div style="font-size:14px; font-weight:600; color:var(--brand-primary); margin-top:4px;">${q.answer || '—'}</div>
              </div>
            `).join('')}
          </div>` : ''}

          ${app.cover_letter ? `
          <div>
            <h4 style="font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:0.8px; color:var(--text-muted); margin-bottom:10px;">Cover Letter</h4>
            <div style="background:var(--bg-input); border-radius:8px; padding:14px; font-size:13px; line-height:1.7; white-space:pre-wrap;">${app.cover_letter}</div>
          </div>` : ''}

          ${app.error_message ? `
          <div style="background:var(--status-error-bg); border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:14px;">
            <h4 style="font-size:12px; font-weight:700; color:var(--status-error-text); margin-bottom:6px;">Error Message</h4>
            <div style="font-size:13px; color:var(--text-secondary);">${app.error_message}</div>
          </div>` : ''}
        </div>
      `;
    }
  } catch (err) {
    body.innerHTML = '<p style="color:var(--status-error-text); text-align:center; padding:24px;">Failed to load application details.</p>';
  }
}

function closeDetailModal() {
  document.getElementById('detail-modal').classList.remove('open');
}

function openEdit(appId) {
  closeDetailModal();
  window.location.href = `apply.html?id=${appId}`;
}

async function deleteApp(appId) {
  if (!confirm('Delete this application record permanently?')) return;
  try {
    const res = await api.delete(`/applications/${appId}`);
    if (res.success) {
      showToast('Application deleted.');
      allApps = allApps.filter(a => a.id !== appId);
      filterHistory();
    } else {
      showToast('Failed to delete application.', 'error');
    }
  } catch (err) {
    console.error(err);
  }
}
