/* ================================================================
   AutoJobApply — Theme Management Utility
================================================================ */

function initTheme() {
  const localTheme = localStorage.getItem('theme');
  const user = getUserData();
  const theme = localTheme || (user && user.theme_pref) || 'dark';
  setTheme(theme);
}

function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  
  // Update state of toggle switch if it exists
  const themeToggle = document.getElementById('theme-toggle-check');
  if (themeToggle) {
    themeToggle.checked = (theme === 'dark');
  }

  // Update backend if user logged in
  if (isLoggedIn()) {
    api.patch('/auth/theme', { theme }).catch(err => console.error(err));
    // Update local user data cache
    const user = getUserData();
    if (user) {
      user.theme_pref = theme;
      setUserData(user);
    }
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const target = current === 'dark' ? 'light' : 'dark';
  setTheme(target);
}

// Global UI Toast Notifications
function showToast(message, type = 'success', duration = 3000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type} fade-in`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';
  if (type === 'warning') icon = '⚠️';

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-message">${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'fadeIn 0.3s ease reverse both';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// Helper to inject HTML navigation dynamically (to keep templates DRY)
function injectSidebar(activePage) {
  const sidebarEl = document.querySelector('.sidebar');
  if (!sidebarEl) return;

  const user = getUserData() || { full_name: 'Guest User', email: 'guest@autojobapply.com' };
  const initials = user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();

  sidebarEl.innerHTML = `
    <div class="sidebar-logo">
      <div class="logo-icon">a</div>
      <div class="logo-text">AutoJobApply</div>
    </div>
    <div class="sidebar-nav">
      <div class="nav-section-label">General</div>
      <a href="dashboard.html" class="nav-item ${activePage === 'dashboard' ? 'active' : ''}">
        <span class="nav-icon">📊</span> Dashboard
      </a>
      <a href="profile.html" class="nav-item ${activePage === 'profile' ? 'active' : ''}">
        <span class="nav-icon">👤</span> Profile Wizard
      </a>
      <a href="autopilot.html" class="nav-item ${activePage === 'autopilot' ? 'active' : ''}">
        <span class="nav-icon">🤖</span> AI Auto-Pilot
      </a>
      <a href="jobs.html" class="nav-item ${activePage === 'jobs' ? 'active' : ''}">
        <span class="nav-icon">💼</span> Carrier Jobs
      </a>
      <a href="history.html" class="nav-item ${activePage === 'history' ? 'active' : ''}">
        <span class="nav-icon">🕒</span> Application History
      </a>
      <a href="review.html" class="nav-item ${activePage === 'review' ? 'active' : ''}">
        <span class="nav-icon">📋</span> Review Queue
      </a>
      <a href="workflow.html" class="nav-item ${activePage === 'workflow' ? 'active' : ''}">
        <span class="nav-icon">⚙️</span> Workflow Monitor
      </a>
      <a href="memory.html" class="nav-item ${activePage === 'memory' ? 'active' : ''}">
        <span class="nav-icon">🧠</span> Memory Insights
      </a>
      <a href="chat.html" class="nav-item ${activePage === 'chat' ? 'active' : ''}">
        <span class="nav-icon">💬</span> AI Chat Workspace
      </a>
      <a href="admin.html" class="nav-item ${activePage === 'admin' ? 'active' : ''}">
        <span class="nav-icon">📊</span> Admin Dashboard
      </a>
      <a href="copilot.html" class="nav-item ${activePage === 'copilot' ? 'active' : ''}">
        <span class="nav-icon">🚀</span> Career Copilot
      </a>
      
      <div class="nav-section-label">Account</div>
      <a href="settings.html" class="nav-item ${activePage === 'settings' ? 'active' : ''}">
        <span class="nav-icon">⚙️</span> Settings
      </a>
      <button class="nav-item" onclick="logout()" style="color: var(--status-error-text);">
        <span class="nav-icon">🚪</span> Logout
      </button>
    </div>
    <div class="sidebar-footer">
      <div class="sidebar-user" onclick="window.location.href='settings.html'">
        <div class="sidebar-avatar">
          ${user.profile_photo ? `<img src="${user.profile_photo}" alt="Avatar">` : initials}
        </div>
        <div class="sidebar-user-info">
          <div class="user-name">${user.full_name}</div>
          <div class="user-email">${user.email}</div>
        </div>
      </div>
    </div>
  `;
}

// Initial script execution on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
});
