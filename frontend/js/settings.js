/* ================================================================
   AutoJobApply — Settings Script (js/settings.js)
================================================================ */

requireAuth();

document.addEventListener('DOMContentLoaded', () => {
  injectSidebar('settings');
  loadAccountData();
  loadStats();
  syncThemeToggle();
});

function syncThemeToggle() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const check = document.getElementById('theme-toggle-check');
  const icon = document.getElementById('theme-icon-display');
  const name = document.getElementById('theme-name-display');

  if (current === 'dark') {
    check.checked = true;
    icon.innerText = '🌙';
    name.innerText = 'Dark Mode';
  } else {
    check.checked = false;
    icon.innerText = '☀️';
    name.innerText = 'Light Mode';
  }
}

function handleThemeToggle(checkbox) {
  const theme = checkbox.checked ? 'dark' : 'light';
  setTheme(theme);
  const icon = document.getElementById('theme-icon-display');
  const name = document.getElementById('theme-name-display');
  icon.innerText = theme === 'dark' ? '🌙' : '☀️';
  name.innerText = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
}

async function loadAccountData() {
  try {
    const res = await api.get('/auth/me');
    if (res.success) {
      const u = res.user;
      document.getElementById('settings-name').value = u.full_name || '';
      document.getElementById('settings-email').value = u.email || '';
      document.getElementById('settings-phone').value = u.phone || '';
      document.getElementById('settings-location').value = u.location || '';
    }
  } catch (err) {
    console.error('Error loading account data:', err);
  }
}

async function loadStats() {
  try {
    const res = await api.get('/jobs/stats');
    const container = document.getElementById('settings-stats');
    if (res.success) {
      const { jobs, applications } = res;
      container.innerHTML = `
        ${statRow('💼', 'Total Jobs Tracked', jobs.total_jobs || 0)}
        ${statRow('🚀', 'Applications Submitted', applications.submitted || 0)}
        ${statRow('⏳', 'In Review / Draft', applications.in_review || 0)}
        ${statRow('❌', 'Failed Submissions', applications.failed || 0)}
      `;
    } else {
      container.innerHTML = `<p style="color:var(--text-muted); font-size:13px;">Could not load stats.</p>`;
    }
  } catch (err) {
    document.getElementById('settings-stats').innerHTML = `<p style="color:var(--text-muted); font-size:13px;">Stats unavailable.</p>`;
  }
}

function statRow(icon, label, value) {
  return `
    <div style="display:flex; align-items:center; justify-content:space-between; padding:12px 14px; background:var(--bg-input); border-radius:10px; border:1px solid var(--border-color);">
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:18px;">${icon}</span>
        <span style="font-size:13px; font-weight:500; color:var(--text-secondary);">${label}</span>
      </div>
      <span style="font-size:18px; font-weight:800; color:var(--text-primary);">${value}</span>
    </div>`;
}

async function saveAccountInfo(e) {
  e.preventDefault();
  const btn = document.getElementById('save-account-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Saving...';

  const full_name = document.getElementById('settings-name').value.trim();
  const phone = document.getElementById('settings-phone').value.trim();
  const location = document.getElementById('settings-location').value.trim();

  if (!full_name) {
    showToast('Full Name is required.', 'error');
    btn.disabled = false;
    btn.innerText = 'Save Changes';
    return;
  }

  try {
    // Update user basic info through profile endpoint
    const res = await api.put('/profile', { full_name, phone, location });
    if (res.success) {
      showToast('Account details updated!', 'success');
      // Update local cache
      const user = getUserData();
      if (user) {
        user.full_name = full_name;
        user.phone = phone;
        user.location = location;
        setUserData(user);
      }
      injectSidebar('settings'); // refresh sidebar with new name
    } else {
      showToast(res.message || 'Failed to update account.', 'error');
    }
  } catch (err) {
    showToast('Network error.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Save Changes';
  }
}

async function changePassword(e) {
  e.preventDefault();
  const currPass = document.getElementById('curr-pass').value;
  const newPass = document.getElementById('new-pass').value;
  const confirmPass = document.getElementById('confirm-pass').value;
  const btn = document.getElementById('change-pass-btn');

  if (newPass !== confirmPass) {
    showToast('New passwords do not match.', 'error');
    return;
  }
  if (newPass.length < 6) {
    showToast('New password must be at least 6 characters.', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Updating...';

  try {
    const res = await api.patch('/auth/password', {
      current_password: currPass,
      new_password: newPass
    });
    if (res.success) {
      showToast('Password updated successfully!', 'success');
      document.getElementById('curr-pass').value = '';
      document.getElementById('new-pass').value = '';
      document.getElementById('confirm-pass').value = '';
    } else {
      showToast(res.message || 'Failed to change password.', 'error');
    }
  } catch (err) {
    showToast('Network error.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerText = 'Update Password';
  }
}

async function confirmDeleteAccount() {
  const confirmed = prompt('This will permanently delete all your data. Type DELETE to confirm:');
  if (confirmed !== 'DELETE') {
    showToast('Account deletion cancelled.', 'warning');
    return;
  }
  showToast('Account deletion is not implemented in this demo for safety.', 'warning', 5000);
}
