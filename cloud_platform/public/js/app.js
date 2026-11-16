// RubberGuard AI Frontend Client Helper

const API_BASE = '/api';

// Authentication storage
const Auth = {
  getToken: () => localStorage.getItem('rg_token'),
  getUser: () => {
    try {
      const u = localStorage.getItem('rg_user');
      return u ? JSON.parse(u) : null;
    } catch (e) {
      return null;
    }
  },
  setSession: (token, user) => {
    localStorage.setItem('rg_token', token);
    localStorage.setItem('rg_user', JSON.stringify(user));
  },
  clearSession: () => {
    localStorage.removeItem('rg_token');
    localStorage.removeItem('rg_user');
  },
  isLoggedIn: () => !!localStorage.getItem('rg_token'),
  isAdmin: () => {
    const user = Auth.getUser();
    return user && user.role === 'admin';
  }
};

// API Fetch Helper
async function apiRequest(endpoint, method = 'GET', data = null, needsAuth = true) {
  const headers = { 'Content-Type': 'application/json' };
  if (needsAuth) {
    const token = Auth.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  const options = {
    method,
    headers
  };

  if (data && (method === 'POST' || method === 'PUT')) {
    options.body = JSON.stringify(data);
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    const result = await response.json();
    return { ok: response.ok, status: response.status, data: result };
  } catch (err) {
    console.error(`API Error [${endpoint}]:`, err);
    return { ok: false, status: 0, data: { error: 'Network or server communication failure' } };
  }
}

// Update Top Navbar based on auth state
function updateNavbar() {
  const navContainer = document.getElementById('nav-auth-container');
  if (!navContainer) return;

  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    const isAdmin = Auth.isAdmin();
    navContainer.innerHTML = `
      <span style="color: rgba(255,255,255,0.85); font-size: 0.9rem;">
        Welcome, <strong>${user ? user.fullName.split(' ')[0] : 'User'}</strong>
      </span>
      ${isAdmin ? '<a href="/admin-dashboard" class="btn btn-sm btn-accent">Admin Console</a>' : '<a href="/tester-dashboard" class="btn btn-sm btn-outline">My Portal</a>'}
      <button onclick="handleLogout()" class="btn btn-sm btn-outline" style="border-color: rgba(255,255,255,0.4);">Sign Out</button>
    `;
  } else {
    navContainer.innerHTML = `
      <a href="/login" class="btn btn-sm btn-outline">Sign In</a>
      <a href="/register" class="btn btn-sm btn-accent">Register Tester</a>
    `;
  }
}

// Logout handler
function handleLogout() {
  Auth.clearSession();
  window.location.href = '/login';
}

// Clipboard copy helper
function copyToClipboard(text, btnElement) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      const original = btnElement.innerText;
      btnElement.innerText = 'Copied!';
      btnElement.style.backgroundColor = '#81c784';
      setTimeout(() => {
        btnElement.innerText = original;
        btnElement.style.backgroundColor = '';
      }, 2000);
    });
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    btnElement.innerText = 'Copied!';
    setTimeout(() => {
      btnElement.innerText = 'Copy Code';
    }, 2000);
  }
}

// Show alert banner
function showAlert(elementId, message, type = 'error') {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.className = `alert alert-${type}`;
  el.innerText = message;
  el.style.display = 'block';
}

function hideAlert(elementId) {
  const el = document.getElementById(elementId);
  if (el) el.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
  updateNavbar();
});