/**
 * CvJachai Master Control Dashboard — main.js
 * Handles: auth (email/password), server toggle, live data, all CRUD actions
 */

// ─── Config ───────────────────────────────────────────────────────────────────
const GOOGLE_CLIENT_ID = "1036628247859-0o1d664qrn16suiub66j1lv5lm6lle4t.apps.googleusercontent.com";
const API_BASE = '/api';
const ADMIN_BASE = `${API_BASE}/master`;
const REFRESH_INTERVAL_MS = 30000; // auto-refresh every 30s


// ─── State ────────────────────────────────────────────────────────────────────
let accessToken = null;
let refreshIntervalId = null;
let modalConfirmCallback = null;

// ─── DOM refs ─────────────────────────────────────────────────────────────────
const authGate      = () => document.getElementById('auth-gate');
const accessDenied  = () => document.getElementById('access-denied');
const appLayout     = () => document.getElementById('app-layout');

// ═══════════════════════════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════════════════════════
window.onload = function () {
    // Check for existing session
    const token = localStorage.getItem('access_token');
    if (token) {
        accessToken = token;
        bootDashboard();
    } else {
        showView('auth');
    }
};

// ─── Email / Password Login ───────────────────────────────────────────────────
async function handleLogin(event) {
    event.preventDefault();

    const email    = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const btn      = document.getElementById('login-btn');
    const errEl    = document.getElementById('auth-error');

    errEl.classList.add('hidden');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing in...';

    try {
        const res = await fetch(`${ADMIN_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Login failed');

        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        accessToken = data.access;

        const name = data.user?.full_name || data.user?.email || 'Admin';
        document.getElementById('sidebar-name').textContent = name;

        bootDashboard();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.classList.remove('hidden');
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-right-to-bracket"></i> Sign In';
    }
}


function bootDashboard() {
    showView('app');
    switchSection('overview');
    refreshAll();
    // Auto-refresh every 30 seconds
    if (refreshIntervalId) clearInterval(refreshIntervalId);
    refreshIntervalId = setInterval(refreshAll, REFRESH_INTERVAL_MS);
}

function doLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    accessToken = null;
    if (refreshIntervalId) clearInterval(refreshIntervalId);
    location.reload();
}

// ─── View switcher ────────────────────────────────────────────────────────────
function showView(view) {
    authGate().classList.add('hidden');
    accessDenied().classList.add('hidden');
    appLayout().classList.add('hidden');

    if (view === 'auth')   authGate().classList.remove('hidden');
    if (view === 'denied') accessDenied().classList.remove('hidden');
    if (view === 'app')    appLayout().classList.remove('hidden');
}

// ─── Section nav ──────────────────────────────────────────────────────────────
function switchSection(name) {
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));

    const section = document.getElementById(`section-${name}`);
    const navLink = document.getElementById(`nav-${name}`);
    if (section) section.classList.add('active');
    if (navLink) navLink.classList.add('active');

    // Lazy-load section data on first visit
    if (name === 'users')        loadUsers();
    if (name === 'jobs')         loadJobs();
    if (name === 'applications') loadApplications();
}

// ═══════════════════════════════════════════════════════════════════════════════
// API HELPER
// ═══════════════════════════════════════════════════════════════════════════════
async function apiFetch(path, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
        ...(options.headers || {})
    };
    const res = await fetch(path, { ...options, headers });
    return res;
}

// ═══════════════════════════════════════════════════════════════════════════════
// REFRESH ALL (overview)
// ═══════════════════════════════════════════════════════════════════════════════
async function refreshAll() {
    const btn = document.getElementById('refresh-btn');
    if (btn) btn.classList.add('spinning');

    try {
        await loadStatus();
        document.getElementById('last-refresh-time').textContent =
            'Last refreshed: ' + new Date().toLocaleTimeString();
    } finally {
        if (btn) btn.classList.remove('spinning');
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SERVER STATUS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadStatus() {
    const pingStart = Date.now();
    try {
        const res = await apiFetch(`${ADMIN_BASE}/status`);
        const latency = Date.now() - pingStart;

        if (!res.ok) {
            if (res.status === 401 || res.status === 403) {
                toast('Session expired. Please log in again.', 'error');
                doLogout();
                return;
            }
            throw new Error(`Status ${res.status}`);
        }

        const d = await res.json();
        renderStatus(d, latency);
    } catch (err) {
        console.error('loadStatus error:', err);
        setMCOffline('Could not reach server — ' + err.message);
    }
}

function renderStatus(d, latency) {
    const enabled = d.api_enabled;

    // Master control card
    const card = document.getElementById('master-control-card');
    const indicator = document.getElementById('mc-indicator');
    const statusText = document.getElementById('mc-status-text');
    const subText = document.getElementById('mc-sub-text');
    const toggle = document.getElementById('server-toggle');
    const toggleLabel = document.getElementById('toggle-label-text');

    card.classList.remove('state-online', 'state-offline');
    indicator.classList.remove('offline');

    if (enabled) {
        card.classList.add('state-online');
        statusText.textContent = 'API Online';
        statusText.style.color = 'var(--success)';
        subText.textContent = 'All endpoints accepting connections';
        toggleLabel.textContent = 'ONLINE';
    } else {
        card.classList.add('state-offline');
        indicator.classList.add('offline');
        statusText.textContent = 'Maintenance Mode';
        statusText.style.color = 'var(--danger)';
        subText.textContent = d.maintenance_message || 'API is offline to callers';
        toggleLabel.textContent = 'OFFLINE';
    }

    toggle.checked = enabled;

    // Last toggle time
    if (d.last_toggled) {
        const dt = new Date(d.last_toggled);
        document.getElementById('last-toggle-val').textContent = dt.toLocaleTimeString();
    }

    // Groq
    const groqEl = document.getElementById('groq-status-val');
    const groqModel = document.getElementById('groq-model-val');
    if (d.groq.status === 'operational') {
        groqEl.textContent = 'Operational';
        groqEl.className = 'mini-value groq-ok';
        groqModel.textContent = d.groq.model;
    } else {
        groqEl.textContent = 'Unavailable';
        groqEl.className = 'mini-value groq-fail';
        groqModel.textContent = 'No API key / unreachable';
    }

    // Latency
    const latEl = document.getElementById('latency-val');
    latEl.textContent = `${latency}ms`;
    latEl.style.color = latency < 200 ? 'var(--success)' : latency < 600 ? 'var(--warning)' : 'var(--danger)';

    // Stats
    const s = d.stats;
    document.getElementById('sv-users').textContent = s.total_users.toLocaleString();
    document.getElementById('sv-jobs').textContent = s.total_jobs.toLocaleString();
    document.getElementById('sv-active-jobs').textContent = `${s.active_jobs} active`;
    document.getElementById('sv-apps').textContent = s.total_applications.toLocaleString();
    const analyzedPct = s.total_applications > 0
        ? Math.round((s.analyzed_applications / s.total_applications) * 100)
        : 0;
    document.getElementById('sv-analyzed').textContent = s.analyzed_applications.toLocaleString();
    document.getElementById('sv-analyzed-pct').textContent = `${analyzedPct}% of applications`;
}

function setMCOffline(msg) {
    document.getElementById('mc-status-text').textContent = 'Unreachable';
    document.getElementById('mc-status-text').style.color = 'var(--danger)';
    document.getElementById('mc-sub-text').textContent = msg;
}

// ═══════════════════════════════════════════════════════════════════════════════
// SERVER TOGGLE
// ═══════════════════════════════════════════════════════════════════════════════
async function handleServerToggle(checkbox) {
    const wantOnline = checkbox.checked;
    const action = wantOnline ? 'bring the API ONLINE' : 'put the API into MAINTENANCE MODE';

    // Revert visually while we confirm
    checkbox.checked = !wantOnline;

    showModal(
        wantOnline
            ? '<i class="fas fa-plug" style="color:var(--success)"></i>'
            : '<i class="fas fa-plug-circle-xmark" style="color:var(--danger)"></i>',
        wantOnline ? 'Enable API?' : 'Maintenance Mode?',
        `This will ${action}. All API callers will be ${wantOnline ? 'served normally' : 'returned a 503 error'}.`,
        wantOnline ? 'Enable' : 'Disable',
        wantOnline ? '' : 'danger',
        async () => {
            try {
                const res = await apiFetch(`${ADMIN_BASE}/toggle-server`, {
                    method: 'POST',
                    body: JSON.stringify({ api_enabled: wantOnline })
                });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Toggle failed');
                toast(data.message, wantOnline ? 'success' : 'warning');
                await loadStatus();
            } catch (err) {
                toast('Toggle failed: ' + err.message, 'error');
            }
        }
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// USERS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadUsers() {
    const tbody = document.getElementById('users-tbody');
    tbody.innerHTML = `<tr><td colspan="6" class="loading-row"><i class="fas fa-spinner fa-spin"></i> Loading users...</td></tr>`;

    try {
        const res = await apiFetch(`${ADMIN_BASE}/users`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to load users');

        document.getElementById('users-count-sub').textContent =
            `${data.total} registered user${data.total !== 1 ? 's' : ''} in the system`;

        if (data.users.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="loading-row">No users found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.users.map(u => {
            const initials = getInitials(u.full_name || u.email);
            const joinDate = fmtDate(u.date_joined);
            const lastLogin = u.last_login ? fmtDate(u.last_login) : 'Never';
            return `
            <tr id="user-row-${u.id}">
                <td>
                    <div class="user-cell">
                        <div class="user-avatar">${initials}</div>
                        <div>
                            <div class="user-name">${esc(u.full_name || '—')}</div>
                            <div class="user-email">${esc(u.email)}</div>
                        </div>
                    </div>
                </td>
                <td>${joinDate}</td>
                <td>${u.job_count}</td>
                <td>
                    ${u.is_staff
                        ? '<span class="badge badge-purple">Staff</span>'
                        : '<span class="badge badge-gray">User</span>'}
                </td>
                <td>
                    ${u.is_active
                        ? '<span class="badge badge-green">Active</span>'
                        : '<span class="badge badge-red">Inactive</span>'}
                </td>
                <td>
                    <button class="action-btn" title="Toggle staff" onclick="toggleUserStaff(${u.id}, ${u.is_staff})">
                        <i class="fas fa-shield-halved"></i>
                    </button>
                    <button class="action-btn danger" title="Delete user" onclick="deleteUser(${u.id}, '${esc(u.email)}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading-row" style="color:var(--danger)"><i class="fas fa-triangle-exclamation"></i> ${err.message}</td></tr>`;
    }
}

async function toggleUserStaff(userId, currentIsStaff) {
    const newStaff = !currentIsStaff;
    try {
        const res = await apiFetch(`${ADMIN_BASE}/users/${userId}`, {
            method: 'PATCH',
            body: JSON.stringify({ is_staff: newStaff })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed');
        toast(`${data.email} is now ${newStaff ? 'Staff' : 'a regular User'}.`, 'success');
        loadUsers();
    } catch (err) {
        toast(err.message, 'error');
    }
}

async function deleteUser(userId, email) {
    showModal(
        '<i class="fas fa-user-xmark"></i>',
        'Delete User?',
        `Permanently delete <strong>${esc(email)}</strong>? This cannot be undone.`,
        'Delete',
        'danger',
        async () => {
            try {
                const res = await apiFetch(`${ADMIN_BASE}/users/${userId}`, { method: 'DELETE' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed');
                toast(data.message, 'success');
                const row = document.getElementById(`user-row-${userId}`);
                if (row) { row.style.opacity = '0'; setTimeout(() => row.remove(), 300); }
                loadStatus(); // refresh count
            } catch (err) { toast(err.message, 'error'); }
        }
    );
}

async function handleCreateStaff(event) {
    event.preventDefault();
    const emailInput = document.getElementById('staff-email');
    const email = emailInput.value.trim();
    const btn = document.getElementById('create-staff-btn');

    if (!email) return;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';

    try {
        const res = await apiFetch(`${ADMIN_BASE}/users`, {
            method: 'POST',
            body: JSON.stringify({ email })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to create staff');

        toast(data.message || 'Staff account ready!', 'success');
        emailInput.value = '';
        loadUsers(); // Refresh the list
        loadStatus(); // Refresh the total user counts on overview
    } catch (err) {
        toast(err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-plus"></i> Create Staff Account';
    }
}


// ═══════════════════════════════════════════════════════════════════════════════
// JOBS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadJobs() {
    const tbody = document.getElementById('jobs-tbody');
    tbody.innerHTML = `<tr><td colspan="6" class="loading-row"><i class="fas fa-spinner fa-spin"></i> Loading jobs...</td></tr>`;

    try {
        const res = await apiFetch(`${ADMIN_BASE}/jobs`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to load jobs');

        document.getElementById('jobs-count-sub').textContent =
            `${data.total} job${data.total !== 1 ? 's' : ''} in the system`;

        if (data.jobs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="loading-row">No jobs found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.jobs.map(j => `
            <tr id="job-row-${j.id}">
                <td style="font-weight:600">${esc(j.title)}</td>
                <td>${esc(j.company_name)}</td>
                <td><div class="user-email">${esc(j.created_by_email)}</div></td>
                <td>${j.application_count}</td>
                <td>
                    ${j.is_active
                        ? '<span class="badge badge-green">Active</span>'
                        : '<span class="badge badge-red">Inactive</span>'}
                </td>
                <td>
                    <button class="action-btn ${j.is_active ? '' : 'success'}"
                        title="${j.is_active ? 'Deactivate' : 'Activate'} job"
                        onclick="toggleJob('${j.id}', ${j.is_active})">
                        <i class="fas fa-${j.is_active ? 'pause' : 'play'}"></i>
                    </button>
                    <button class="action-btn danger" title="Delete job"
                        onclick="deleteJob('${j.id}', '${esc(j.title)}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="loading-row" style="color:var(--danger)"><i class="fas fa-triangle-exclamation"></i> ${err.message}</td></tr>`;
    }
}

async function toggleJob(jobId, currentActive) {
    try {
        const res = await apiFetch(`${ADMIN_BASE}/jobs/${jobId}`, {
            method: 'PATCH',
            body: JSON.stringify({ is_active: !currentActive })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed');
        toast(`"${data.title}" is now ${data.is_active ? 'Active' : 'Inactive'}.`, 'success');
        loadJobs();
    } catch (err) {
        toast(err.message, 'error');
    }
}

async function deleteJob(jobId, title) {
    showModal(
        '<i class="fas fa-briefcase" style="color:var(--danger)"></i>',
        'Delete Job?',
        `Permanently delete <strong>${esc(title)}</strong> and all its applications?`,
        'Delete',
        'danger',
        async () => {
            try {
                const res = await apiFetch(`${ADMIN_BASE}/jobs/${jobId}`, { method: 'DELETE' });
                const data = await res.json();
                if (!res.ok) throw new Error(data.error || 'Failed');
                toast(data.message, 'success');
                const row = document.getElementById(`job-row-${jobId}`);
                if (row) { row.style.opacity = '0'; setTimeout(() => row.remove(), 300); }
                loadStatus();
            } catch (err) { toast(err.message, 'error'); }
        }
    );
}

// ═══════════════════════════════════════════════════════════════════════════════
// APPLICATIONS
// ═══════════════════════════════════════════════════════════════════════════════
async function loadApplications() {
    const tbody = document.getElementById('apps-tbody');
    tbody.innerHTML = `<tr><td colspan="5" class="loading-row"><i class="fas fa-spinner fa-spin"></i> Loading applications...</td></tr>`;

    try {
        const res = await apiFetch(`${ADMIN_BASE}/applications`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed');

        document.getElementById('apps-count-sub').textContent =
            `${data.total} application${data.total !== 1 ? 's' : ''} across all jobs`;

        if (data.applications.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" class="loading-row">No applications yet.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.applications.map(a => {
            const score = a.match_score;
            const pct = score ? Math.round(score * 100) : null;
            const scoreHtml = pct !== null
                ? `<div class="score-bar-wrap">
                       <div class="score-bar"><div class="score-fill" style="width:${pct}%"></div></div>
                       <span class="score-text">${pct}%</span>
                   </div>`
                : `<span class="badge badge-gray">Not analyzed</span>`;

            const verdictHtml = a.verdict
                ? `<span class="badge ${pct >= 80 ? 'badge-green' : pct >= 60 ? 'badge-yellow' : 'badge-red'}">${esc(a.verdict.slice(0, 30))}</span>`
                : '—';

            return `
            <tr>
                <td>
                    <div class="user-name">${esc(a.candidate_name)}</div>
                    <div class="user-email">${esc(a.candidate_email)}</div>
                </td>
                <td>
                    <div style="font-weight:600;font-size:0.875rem">${esc(a.job_title)}</div>
                    <div class="user-email">${a.job_id}</div>
                </td>
                <td>${fmtDate(a.applied_at)}</td>
                <td>${scoreHtml}</td>
                <td>${verdictHtml}</td>
            </tr>`;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="loading-row" style="color:var(--danger)"><i class="fas fa-triangle-exclamation"></i> ${err.message}</td></tr>`;
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MODAL
// ═══════════════════════════════════════════════════════════════════════════════
function showModal(iconHtml, title, body, confirmText, confirmStyle, callback) {
    document.getElementById('modal-icon').innerHTML = iconHtml;
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = body;
    const btn = document.getElementById('modal-confirm-btn');
    btn.textContent = confirmText;
    btn.className = confirmStyle === 'danger' ? 'btn-danger' : 'btn-primary';
    modalConfirmCallback = callback;
    document.getElementById('confirm-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('confirm-modal').classList.add('hidden');
    modalConfirmCallback = null;
}

// Modal button listeners — set up immediately (DOM is already parsed at this point)
document.getElementById('modal-confirm-btn').addEventListener('click', async () => {
    if (modalConfirmCallback) {
        const callback = modalConfirmCallback; // capture BEFORE closeModal nullifies it
        closeModal();
        await callback();
    }
});

// Close modal on backdrop click
document.getElementById('confirm-modal').addEventListener('click', e => {
    if (e.target.id === 'confirm-modal') closeModal();
});

// Sidebar navigation
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        switchSection(link.dataset.section);
    });
});


// ═══════════════════════════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════════════════════════
function toast(message, type = 'info', durationMs = 4000) {
    const icons = {
        success: 'fa-circle-check',
        error:   'fa-circle-xmark',
        warning: 'fa-triangle-exclamation',
        info:    'fa-circle-info'
    };
    const colors = {
        success: 'var(--success)',
        error:   'var(--danger)',
        warning: 'var(--warning)',
        info:    'var(--primary)'
    };
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.innerHTML = `<i class="fas ${icons[type] || icons.info}" style="color:${colors[type]};font-size:1.1rem;flex-shrink:0"></i><span>${message}</span>`;
    document.getElementById('toast-container').appendChild(el);
    setTimeout(() => {
        el.style.opacity = '0';
        el.style.transition = 'opacity 0.3s';
        setTimeout(() => el.remove(), 300);
    }, durationMs);
}

// ═══════════════════════════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════════════════════════
function esc(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function getInitials(name) {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    return parts.length >= 2
        ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
        : name.slice(0, 2).toUpperCase();
}

function fmtDate(isoStr) {
    if (!isoStr) return '—';
    const d = new Date(isoStr);
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}
