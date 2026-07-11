/* ================================================================
   AutoJobApply — API Wrapper
================================================================ */
const API_BASE = window.location.origin + '/api';

const api = {
  token: localStorage.getItem('token') || null,

  setToken(t) {
    this.token = t;
    if (t) localStorage.setItem('token', t);
    else localStorage.removeItem('token');
  },

  async request(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (this.token) headers['Authorization'] = `Bearer ${this.token}`;

    // Remove Content-Type if FormData
    if (options.body instanceof FormData) delete headers['Content-Type'];

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        credentials: 'include',
        ...options,
        headers
      });

      const data = await res.json().catch(() => ({ success: false, message: 'Invalid response' }));

      if (res.status === 401) {
        this.setToken(null);
        if (!window.location.pathname.includes('index.html') && window.location.pathname !== '/') {
          window.location.href = 'index.html';
        }
        return data;
      }
      return data;
    } catch (err) {
      console.error('API Error:', err);
      return { success: false, message: 'Network error. Please check your connection.' };
    }
  },

  get(endpoint) { return this.request(endpoint); },
  post(endpoint, body) { return this.request(endpoint, { method: 'POST', body: JSON.stringify(body) }); },
  put(endpoint, body) { return this.request(endpoint, { method: 'PUT', body: JSON.stringify(body) }); },
  patch(endpoint, body) { return this.request(endpoint, { method: 'PATCH', body: JSON.stringify(body) }); },
  delete(endpoint) { return this.request(endpoint, { method: 'DELETE' }); },

  upload(endpoint, formData) {
    return this.request(endpoint, { method: 'POST', body: formData, headers: {} });
  }
};

// ── Auth helpers ────────────────────────────────────────────────
function isLoggedIn() { return !!api.token; }

function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = 'index.html';
    return false;
  }
  return true;
}

function getUserData() {
  const d = localStorage.getItem('user');
  return d ? JSON.parse(d) : null;
}
function setUserData(u) { localStorage.setItem('user', JSON.stringify(u)); }

function logout() {
  api.post('/auth/logout');
  api.setToken(null);
  localStorage.removeItem('user');
  window.location.href = 'index.html';
}
