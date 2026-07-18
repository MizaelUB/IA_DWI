/* ============================================================
   Swingtails · Dashboard logic
   Preserves the existing API contract:
     POST /api/auth/login
     GET  /api/dashboard/veterinarias
     GET  /api/dashboard/citas     (?veterinary_id=)
     GET  /api/dashboard/mascotas  (?veterinary_id=)
     GET  /api/dashboard/clientes  (?veterinary_id=)
     POST /api/chat/stream         (streaming, X-Conversation-Id)
   ============================================================ */

(function () {
    'use strict';

    /* ---------- Inline icon set (Heroicons-style) ---------- */
    const IC = {
        paw: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 13.2c-2.4 0-4.3 1.7-4.3 3.8 0 1.1.9 1.8 2 1.8.9 0 1.5-.3 2.3-.3s1.4.3 2.3.3c1.1 0 2-.7 2-1.8 0-2.1-1.9-3.8-4.3-3.8Z"/><ellipse cx="6.7" cy="11" rx="1.6" ry="2"/><ellipse cx="17.3" cy="11" rx="1.6" ry="2"/><ellipse cx="9.7" cy="7.6" rx="1.5" ry="1.9"/><ellipse cx="14.3" cy="7.6" rx="1.5" ry="1.9"/></svg>',
        clock: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.5 20.25a7.5 7.5 0 0115 0"/></svg>',
        phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 6.75c0 8.284 6.716 15 15 15h2.25a2.25 2.25 0 002.25-2.25v-1.372c0-.516-.351-.966-.852-1.091l-4.423-1.106c-.44-.11-.902.055-1.173.417l-.97 1.293c-.282.376-.769.542-1.21.38a12.035 12.035 0 01-7.143-7.143c-.162-.441.004-.928.38-1.21l1.293-.97c.363-.271.527-.734.417-1.173L6.963 3.102a1.125 1.125 0 00-1.091-.852H4.5A2.25 2.25 0 002.25 4.5v2.25z"/></svg>',
        mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/></svg>',
        ellipsis: '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="5" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="19" r="1.6"/></svg>',
        calendar: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5"/></svg>'
    };

    const AV_COLORS = [
        ['#D9663C', '#A8461F'], ['#B5512F', '#7A3520'], ['#E89A2F', '#B06A1F'],
        ['#5E9B86', '#3F6B5A'], ['#C2552E', '#8A3A1A'], ['#8A6E5A', '#5A4636'],
        ['#A8743E', '#6E4A23'], ['#6E8A5A', '#465A38']
    ];
    function avColor(name) {
        let h = 0; const s = String(name || '?');
        for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
        return AV_COLORS[h % AV_COLORS.length];
    }
    function initials(name) {
        const s = String(name || '?').trim();
        const parts = s.split(/\s+/);
        if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
        return s.slice(0, 2).toUpperCase();
    }
    function avatarStyle(name) {
        const [a, b] = avColor(name);
        return `style="background:linear-gradient(150deg, ${a}, ${b})"`;
    }
    function escapeHtml(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    /* ---------- Date helpers ---------- */
    function parseFecha(f) {
        if (!f) return null;
        const s = String(f).trim();
        let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
        if (m) return new Date(+m[1], +m[2] - 1, +m[3]);
        m = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/);
        if (m) return new Date(+m[3], +m[2] - 1, +m[1]);
        const d = new Date(s);
        return isNaN(d.getTime()) ? null : d;
    }
    function startOfDay(d) { const x = new Date(d); x.setHours(0, 0, 0, 0); return x; }
    function sameDay(a, b) { return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate(); }
    function padTime(t) {
        if (!t) return '';
        const p = String(t).split(':');
        if (p.length < 2) return String(t);
        return p[0].padStart(2, '0') + ':' + p[1].padStart(2, '0');
    }
    function fmtDate(d) {
        return String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0');
    }
    const WD = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    const WD_FULL = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];

    function estadoKey(estado) {
        const e = String(estado || '').toLowerCase();
        if (e.includes('cancel')) return 'cancelada';
        if (e.includes('pend')) return 'pendiente';
        if (e.includes('confirm')) return 'confirmada';
        if (e.includes('atend') || e.includes('complet') || e.includes('final')) return 'atendida';
        return 'pendiente';
    }
    function estadoLabel(estado) {
        const e = String(estado || '').toLowerCase();
        if (e.includes('cancel')) return 'Cancelada';
        if (e.includes('pend')) return 'Pendiente';
        if (e.includes('confirm')) return 'Confirmada';
        if (e.includes('atend') || e.includes('complet') || e.includes('final')) return 'Atendida';
        return escapeHtml(estado || '—');
    }
    function badgeHtml(estado) {
        return `<span class="status-badge ${estadoKey(estado)}">${estadoLabel(estado)}</span>`;
    }

    /* ---------- DOM ---------- */
    const $ = id => document.getElementById(id);
    const loginOverlay = $('login-overlay');
    const loginForm = $('login-form');
    const loginUsername = $('login-username');
    const loginPassword = $('login-password');
    const loginError = $('login-error');
    const app = $('app');
    const sidebar = $('sidebar');
    const sidebarToggle = $('sidebar-toggle');
    const menuBtn = $('menu-btn');
    const scrim = $('sidebar-scrim');
    const vetSelector = $('vet-selector');
    const viewTitle = $('view-title');
    const content = $('content');
    const navItems = Array.from(document.querySelectorAll('.nav-item'));
    const views = Array.from(document.querySelectorAll('.view'));
    const globalSearch = $('global-search');
    const userMiniName = $('user-mini-name');
    const userMiniClinic = $('user-mini-clinic');
    const userAvatar = $('user-avatar');
    const bellDot = $('bell-dot');
    const navNotifCount = $('nav-notif-count');

    const viewTitles = {
        resumen: 'Resumen', calendario: 'Calendario', citas: 'Gestión de citas',
        pacientes: 'Pacientes', clientes: 'Clientes', notificaciones: 'Notificaciones',
        asistente: 'Asistente IA'
    };

    const state = {
        citas: [], mascotas: [], clientes: [],
        selectedDate: startOfDay(new Date()),
        calStart: startOfDay(new Date()),
        filter: 'todas', search: ''
    };

    /* ============================================================
       Session & login
       ============================================================ */
    function showApp(show) {
        app.hidden = !show;
        loginOverlay.style.display = show ? 'none' : 'flex';
    }

    function checkSession() {
        const session = localStorage.getItem('clinic_session');
        if (session) {
            try {
                const user = JSON.parse(session);
                showApp(true);
                setUser(user);
                setTimeout(() => {
                    vetSelector.value = user.veterinary_id || '';
                    vetSelector.disabled = true;
                    loadData();
                    loadChatHistory();
                }, 200);
            } catch (e) {
                localStorage.removeItem('clinic_session');
                showApp(false);
            }
        } else {
            showApp(false);
        }
    }

    function setUser(user) {
        const name = user.username || user.veterinary_name || 'Administrador';
        userMiniName.textContent = name;
        userMiniClinic.textContent = user.veterinary_name || 'Todas las clínicas';
        userAvatar.textContent = initials(name);
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = loginUsername.value.trim();
        const password = loginPassword.value.trim();
        if (!username || !password) return;
        loginError.textContent = '';
        const btn = $('login-btn');
        btn.disabled = true; btn.textContent = 'Conectando…';
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            if (res.ok && data.status === 'success') {
                localStorage.setItem('clinic_session', JSON.stringify({
                    username: data.username, veterinary_id: data.veterinary_id,
                    veterinary_name: data.veterinary_name
                }));
                loginForm.reset();
                checkSession();
            } else {
                loginError.textContent = data.detail || 'Usuario o contraseña incorrectos.';
            }
        } catch (err) {
            loginError.textContent = 'No se pudo conectar con el servidor.';
        } finally {
            btn.disabled = false; btn.textContent = 'Iniciar sesión';
        }
    });

    $('logout-btn').addEventListener('click', () => {
        localStorage.removeItem('clinic_session');
        vetSelector.disabled = false;
        vetSelector.value = '';
        showApp(false);
    });

    /* ============================================================
       Sidebar
       ============================================================ */
    sidebarToggle.addEventListener('click', () => {
        const collapsed = sidebar.classList.toggle('collapsed');
        sidebarToggle.setAttribute('aria-label', collapsed ? 'Expandir menú' : 'Contraer menú');
    });
    function openMobileSidebar() {
        sidebar.classList.add('open');
        scrim.hidden = false;
    }
    function closeMobileSidebar() {
        sidebar.classList.remove('open');
        scrim.hidden = true;
    }
    menuBtn.addEventListener('click', openMobileSidebar);
    scrim.addEventListener('click', closeMobileSidebar);

    /* ============================================================
       Navigation
       ============================================================ */
    function switchView(target) {
        navItems.forEach(n => n.classList.toggle('active', n.dataset.target === target));
        views.forEach(v => v.classList.toggle('active', v.id === 'view-' + target));
        viewTitle.textContent = viewTitles[target] || '';
        document.body.dataset.view = target;
        content.scrollTop = 0;
        closeMobileSidebar();
        if (target === 'asistente') setTimeout(() => $('chat-input').focus(), 120);
    }
    navItems.forEach(item => item.addEventListener('click', () => switchView(item.dataset.target)));

    document.addEventListener('click', (e) => {
        const go = e.target.closest('[data-goto]');
        if (go) { switchView(go.dataset.goto); return; }
        const ai = e.target.closest('[data-ai]');
        if (ai) { askAI(ai.dataset.ai); }
    });

    /* ============================================================
       Data loading (API)
       ============================================================ */
    async function loadVeterinarias() {
        try {
            const res = await fetch('/api/dashboard/veterinarias');
            const data = await res.json();
            if (data.status === 'success' && Array.isArray(data.data)) {
                vetSelector.innerHTML = '<option value="">Todas las clínicas</option>';
                data.data.forEach(v => {
                    const opt = document.createElement('option');
                    opt.value = v.id;
                    opt.textContent = `${v.name}${v.city ? ' (' + v.city + ')' : ''}`;
                    vetSelector.appendChild(opt);
                });
            }
        } catch (e) { console.error('Error cargando veterinarias', e); }
    }

    async function loadData() {
        const vetId = vetSelector.value;
        const param = vetId ? `?veterinary_id=${vetId}` : '';
        try {
            const [rC, rM, rCl] = await Promise.all([
                fetch(`/api/dashboard/citas${param}`),
                fetch(`/api/dashboard/mascotas${param}`),
                fetch(`/api/dashboard/clientes${param}`)
            ]);
            const [dC, dM, dCl] = await Promise.all([rC.json(), rM.json(), rCl.json()]);
            if (dC.status === 'success') state.citas = Array.isArray(dC.data) ? dC.data : [];
            if (dM.status === 'success') state.mascotas = Array.isArray(dM.data) ? dM.data : [];
            if (dCl.status === 'success') state.clientes = Array.isArray(dCl.data) ? dCl.data : [];
            renderAll();
        } catch (e) { console.error('Error cargando datos', e); }
    }
    vetSelector.addEventListener('change', loadData);

    /* ============================================================
       Stats
       ============================================================ */
    function renderStats() {
        const today = startOfDay(new Date());
        const todays = state.citas.filter(c => {
            const d = parseFecha(c.fecha); return d && sameDay(d, today) && estadoKey(c.estado) !== 'cancelada';
        });
        const pendientes = state.citas.filter(c => estadoKey(c.estado) === 'pendiente');
        const atendidos = state.citas.filter(c => {
            const d = parseFecha(c.fecha);
            return d && sameDay(d, today) && estadoKey(c.estado) === 'atendida';
        });
        $('stat-hoy').textContent = todays.length;
        $('stat-atendidos').textContent = atendidos.length;
        $('stat-pendientes').textContent = pendientes.length;
        $('stat-pacientes').textContent = state.mascotas.length;
    }

    /* ============================================================
       Weekly chart (SVG)
       ============================================================ */
    function renderChart() {
        const counts = [0, 0, 0, 0, 0, 0, 0]; // Mon..Sun
        state.citas.forEach(c => {
            const d = parseFecha(c.fecha); if (!d) return;
            const day = d.getDay();
            counts[day === 0 ? 6 : day - 1]++;
        });
        const labels = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
        const W = 700, H = 220, padX = 8, top = 26, bottom = 28;
        const plotH = H - top - bottom;
        const baseline = top + plotH;
        const max = Math.max(1, ...counts);
        const slot = (W - padX * 2) / 7;
        const bw = 46;

        let bars = '', vals = '', axis = '';
        counts.forEach((c, i) => {
            const x = padX + i * slot + (slot - bw) / 2;
            const h = c > 0 ? Math.max(6, (c / max) * plotH) : 0;
            const y = baseline - h;
            if (c > 0) {
                bars += `<rect class="chart-bar" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw}" height="${h.toFixed(1)}" rx="8"><title>${labels[i]}: ${c} citas</title></rect>`;
                vals += `<text class="chart-val" x="${(x + bw / 2).toFixed(1)}" y="${(y - 8).toFixed(1)}" text-anchor="middle">${c}</text>`;
            } else {
                bars += `<rect class="chart-bar-zero" x="${x.toFixed(1)}" y="${baseline - 3}" width="${bw}" height="4" rx="2"><title>${labels[i]}: 0 citas</title></rect>`;
            }
            axis += `<text class="chart-axis" x="${(x + bw / 2).toFixed(1)}" y="${H - 8}" text-anchor="middle">${labels[i]}</text>`;
        });
        let grid = '';
        [0, 0.33, 0.66].forEach(f => { grid += `<line class="chart-grid" x1="${padX}" y1="${(top + plotH * f).toFixed(1)}" x2="${W - padX}" y2="${(top + plotH * f).toFixed(1)}"/>`; });

        const total = counts.reduce((a, b) => a + b, 0);
        const empty = total === 0
            ? `<text class="chart-axis" x="${W / 2}" y="${H / 2}" text-anchor="middle">Sin citas suficientes para graficar</text>`
            : '';

        $('weekly-chart').innerHTML =
            `<svg class="chart-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Citas por día de la semana">
                <defs><linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stop-color="#D9663C"/><stop offset="1" stop-color="#B5512F"/>
                </linearGradient></defs>
                ${grid}${bars}${axis}${empty}
            </svg>`;
    }

    /* ============================================================
       Mini agenda (overview)
       ============================================================ */
    function renderMiniAgenda() {
        const today = startOfDay(new Date());
        const items = state.citas
            .filter(c => { const d = parseFecha(c.fecha); return d && sameDay(d, today) && estadoKey(c.estado) !== 'cancelada'; })
            .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));
        const el = $('mini-agenda');
        if (items.length === 0) {
            el.innerHTML = `<div class="table-empty" style="padding:36px 16px">
                <p class="empty-title">Sin citas para hoy</p>
                <p class="empty-sub">Crea una cita desde el asistente IA.</p></div>`;
            return;
        }
        el.innerHTML = items.slice(0, 6).map(c => `
            <div class="mini-agenda-item">
                <span class="mini-time">${escapeHtml(padTime(c.hora))}</span>
                <span class="mini-info">
                    <span class="mini-pet">${escapeHtml(c.mascota)}</span>
                    <span class="mini-owner">${escapeHtml(c.dueno)}</span>
                </span>
                ${badgeHtml(c.estado)}
            </div>`).join('');
    }

    /* ============================================================
       Recent appointments table (overview)
       ============================================================ */
    function renderRecentTable() {
        const sorted = state.citas.slice().sort((a, b) => {
            const da = parseFecha(a.fecha), db = parseFecha(b.fecha);
            return (db ? db.getTime() : 0) - (da ? da.getTime() : 0);
        });
        $('dashboard-table-body').innerHTML = sorted.slice(0, 6).map(c => `
            <tr>
                <td class="cell-muted">${escapeHtml(c.fecha)}</td>
                <td class="cell-strong">${escapeHtml(padTime(c.hora))}</td>
                <td><div class="pet-cell"><span class="pet-avatar" ${avatarStyle(c.mascota)}>${initials(c.mascota)}</span><span class="cell-strong">${escapeHtml(c.mascota)}</span></div></td>
                <td>${escapeHtml(c.dueno)}</td>
                <td class="cell-muted">${escapeHtml(c.veterinaria)}</td>
                <td>${badgeHtml(c.estado)}</td>
            </tr>`).join('') || emptyRow(6, 'Aún no hay citas registradas.');
    }
    function emptyRow(cols, msg) {
        return `<tr><td colspan="${cols}" style="text-align:center;color:var(--text-muted);padding:28px">${msg}</td></tr>`;
    }

    /* ============================================================
       Appointments view (filters + search)
       ============================================================ */
    function renderCitas() {
        const q = state.search.trim().toLowerCase();
        const rows = state.citas.filter(c => {
            if (state.filter !== 'todas' && estadoKey(c.estado) !== state.filter) return false;
            if (q) {
                const hay = `${c.mascota} ${c.dueno} ${c.veterinaria} ${c.fecha} ${c.hora} #${c.id}`.toLowerCase();
                if (!hay.includes(q)) return false;
            }
            return true;
        }).sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));

        const empty = $('citas-empty');
        const tbody = $('citas-table-body');
        if (rows.length === 0) {
            tbody.innerHTML = '';
            empty.hidden = false;
        } else {
            empty.hidden = true;
            tbody.innerHTML = rows.map(c => `
                <tr>
                    <td class="cell-id">#${escapeHtml(c.id)}</td>
                    <td><div class="pet-cell"><span class="pet-avatar" ${avatarStyle(c.mascota)}>${initials(c.mascota)}</span><span class="cell-strong">${escapeHtml(c.mascota)}</span></div></td>
                    <td>${escapeHtml(c.dueno)}</td>
                    <td class="cell-muted">${escapeHtml(c.fecha)}</td>
                    <td class="cell-strong">${escapeHtml(padTime(c.hora))}</td>
                    <td class="cell-muted">${escapeHtml(c.veterinaria)}</td>
                    <td>${badgeHtml(c.estado)}</td>
                    <td class="td-end"><button class="icon-btn row-action" data-ai="Muéstrame los detalles de la cita #${escapeHtml(c.id)}" aria-label="Consultar cita #${escapeHtml(c.id)}" style="width:32px;height:32px">${IC.ellipsis}</button></td>
                </tr>`).join('');
        }
    }
    document.querySelectorAll('#filter-chips .chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('#filter-chips .chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.filter = chip.dataset.filter;
            renderCitas();
        });
    });

    /* ============================================================
       Patients & clients
       ============================================================ */
    function renderPacientes() {
        const q = state.search.trim().toLowerCase();
        const list = state.mascotas.filter(m => {
            if (!q) return true;
            return `${m.nombre} ${m.especie} ${m.raza} ${m.dueno}`.toLowerCase().includes(q);
        });
        const el = $('pacientes-grid');
        $('pacientes-empty').hidden = list.length > 0;
        el.innerHTML = list.map(m => `
            <article class="patient-card">
                <div class="patient-head">
                    <span class="patient-avatar" ${avatarStyle(m.nombre)}>${initials(m.nombre)}</span>
                    <div>
                        <div class="patient-name">${escapeHtml(m.nombre)}</div>
                        <div class="patient-species">${escapeHtml(m.especie)}${m.raza ? ' · ' + escapeHtml(m.raza) : ''}</div>
                    </div>
                </div>
                <div class="patient-rows">
                    <div class="patient-row">${IC.user}<span>Dueño: <b>${escapeHtml(m.dueno)}</b></span></div>
                    <div class="patient-row">${IC.paw}<span>ID <b>#${escapeHtml(m.id)}</b></span></div>
                </div>
                <div class="patient-foot">
                    <button class="btn btn-ghost btn-sm" data-ai="Muéstrame el historial de ${escapeHtml(m.nombre)}" style="flex:1">Ver historial</button>
                    <button class="btn btn-primary btn-sm" data-ai="Crea una cita para ${escapeHtml(m.nombre)}" style="flex:1">Cita</button>
                </div>
            </article>`).join('');
    }

    function renderClientes() {
        const q = state.search.trim().toLowerCase();
        const list = state.clientes.filter(c => {
            if (!q) return true;
            return `${c.nombre} ${c.telefono} ${c.email}`.toLowerCase().includes(q);
        });
        const el = $('clientes-grid');
        $('clientes-empty').hidden = list.length > 0;
        el.innerHTML = list.map(c => `
            <article class="client-card">
                <div class="client-head">
                    <span class="patient-avatar" ${avatarStyle(c.nombre)}>${initials(c.nombre)}</span>
                    <div class="client-name">${escapeHtml(c.nombre)}</div>
                </div>
                <div class="client-rows">
                    ${c.telefono ? `<div class="client-row">${IC.phone}<span>${escapeHtml(c.telefono)}</span></div>` : ''}
                    ${c.email ? `<div class="client-row">${IC.mail}<span>${escapeHtml(c.email)}</span></div>` : ''}
                    <div class="client-row">${IC.user}<span>ID <b>#${escapeHtml(c.id)}</b></span></div>
                </div>
            </article>`).join('');
    }

    /* ============================================================
       Calendar / agenda
       ============================================================ */
    function renderDateStrip() {
        const el = $('date-strip');
        const today = startOfDay(new Date());
        let html = '';
        for (let i = 0; i < 14; i++) {
            const d = new Date(state.calStart); d.setDate(d.getDate() + i);
            const count = state.citas.filter(c => { const cd = parseFecha(c.fecha); return cd && sameDay(cd, d); }).length;
            const isToday = sameDay(d, today);
            const isActive = sameDay(d, state.selectedDate);
            html += `<button class="date-pill ${isActive ? 'active' : ''} ${isToday ? 'today' : ''}" data-date="${d.toISOString()}" role="tab" aria-selected="${isActive}">
                <span class="date-pill-dow">${WD[d.getDay()]}</span>
                <span class="date-pill-day">${d.getDate()}</span>
                <span class="date-pill-count">${count} ${count === 1 ? 'cita' : 'citas'}</span>
            </button>`;
        }
        el.innerHTML = html;
        el.querySelectorAll('.date-pill').forEach(p => p.addEventListener('click', () => {
            state.selectedDate = startOfDay(new Date(p.dataset.date));
            renderDateStrip(); renderAgenda();
        }));
    }

    function renderAgenda() {
        const el = $('agenda-list');
        $('agenda-sub').textContent = WD_FULL[state.selectedDate.getDay()] + ' · ' + fmtDate(state.selectedDate);
        const items = state.citas
            .filter(c => { const d = parseFecha(c.fecha); return d && sameDay(d, state.selectedDate); })
            .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));
        if (items.length === 0) {
            el.innerHTML = `<div class="table-empty">
                <span class="empty-icon">${IC.calendar}</span>
                <p class="empty-title">No hay citas este día</p>
                <p class="empty-sub">Selecciona otro día o crea una cita desde el asistente.</p></div>`;
            return;
        }
        el.innerHTML = items.map(c => {
            const k = estadoKey(c.estado);
            return `<div class="agenda-item is-${k}">
                <span class="agenda-time">${escapeHtml(padTime(c.hora))}</span>
                <div class="agenda-body">
                    <div class="agenda-pet">${escapeHtml(c.mascota)}</div>
                    <div class="agenda-meta">${escapeHtml(c.dueno)} · ${escapeHtml(c.veterinaria)}</div>
                </div>
                <div class="agenda-side">${badgeHtml(c.estado)}
                    <button class="icon-btn" data-ai="Muéstrame los detalles de la cita de ${escapeHtml(c.mascota)} el ${escapeHtml(c.fecha)}" aria-label="Consultar" style="width:32px;height:32px">${IC.ellipsis}</button>
                </div>
            </div>`;
        }).join('');
    }
    $('date-prev').addEventListener('click', () => { state.calStart.setDate(state.calStart.getDate() - 7); renderDateStrip(); });
    $('date-next').addEventListener('click', () => { state.calStart.setDate(state.calStart.getDate() + 7); renderDateStrip(); });

    /* ============================================================
       Notifications (derived)
       ============================================================ */
    let notifUnread = 0;
    function renderNotifications() {
        const today = startOfDay(new Date());
        const pendientes = state.citas.filter(c => estadoKey(c.estado) === 'pendiente');
        const todays = state.citas
            .filter(c => { const d = parseFecha(c.fecha); return d && sameDay(d, today); })
            .sort((a, b) => padTime(a.hora).localeCompare(padTime(b.hora)));
        const upcoming = state.citas
            .filter(c => { const d = parseFecha(c.fecha); return d && d.getTime() > today.getTime() && estadoKey(c.estado) !== 'cancelada'; })
            .sort((a, b) => (parseFecha(a.fecha)?.getTime() || 0) - (parseFecha(b.fecha)?.getTime() || 0));

        const items = [];
        items.push({ kind: 'info', title: 'Asistente IA disponible', text: 'Consulta citas, historiales o crea turnos conversando con el asistente.', time: 'Sistema' });
        if (pendientes.length > 0) {
            items.push({ kind: 'pending', title: `${pendientes.length} ${pendientes.length === 1 ? 'cita pendiente' : 'citas pendientes'} de confirmación`, text: 'Revisa y confirma los turnos pendientes desde la sección Citas.', time: 'Hoy' });
        }
        todays.slice(0, 4).forEach(c => {
            const k = estadoKey(c.estado);
            items.push({ kind: k, title: `Cita de ${c.mascota}`, text: `${c.dueno} a las ${padTime(c.hora)} · ${c.veterinaria}`, time: 'Hoy' });
        });
        upcoming.slice(0, 3).forEach(c => {
            const d = parseFecha(c.fecha);
            const tomorrow = new Date(today); tomorrow.setDate(tomorrow.getDate() + 1);
            const time = d && sameDay(d, tomorrow) ? 'Mañana' : fmtDate(d);
            items.push({ kind: 'confirmed', title: `Próxima cita: ${c.mascota}`, text: `${c.dueno} · ${time} a las ${padTime(c.hora)}`, time });
        });
        if (state.mascotas.length > 0) {
            items.push({ kind: 'info', title: `${state.mascotas.length} pacientes en base`, text: 'Revisa historiales y gestiona citas desde Pacientes.', time: 'Sistema' });
        }

        const icMap = { pending: IC.clock, confirmed: IC.check, cancelled: IC.x, info: IC.paw };
        notifUnread = Math.min(3, items.length);
        const list = items.slice(0, 8);
        $('notificaciones-list').innerHTML = list.map((n, i) => `
            <div class="notif-item ${i < notifUnread ? 'unread' : ''}">
                <span class="notif-ic ${n.kind}">${icMap[n.kind] || IC.paw}</span>
                <div class="notif-body">
                    <div class="notif-title">${escapeHtml(n.title)}</div>
                    <div class="notif-text">${escapeHtml(n.text)}</div>
                    <div class="notif-time">${escapeHtml(n.time)}</div>
                </div>
                <span class="notif-dot"></span>
            </div>`).join('');
        $('notif-empty').hidden = list.length > 0;
        updateNotifBadges();
    }
    function updateNotifBadges() {
        const unread = document.querySelectorAll('.notif-item.unread').length;
        bellDot.hidden = unread === 0;
        if (unread > 0) { navNotifCount.textContent = unread; navNotifCount.hidden = false; }
        else navNotifCount.hidden = true;
    }
    $('notif-clear').addEventListener('click', () => {
        document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
        updateNotifBadges();
    });
    $('bell-btn').addEventListener('click', () => switchView('notificaciones'));

    /* ============================================================
       Global search
       ============================================================ */
    globalSearch.addEventListener('input', (e) => {
        state.search = e.target.value;
        const v = document.body.dataset.view;
        if (v === 'citas') renderCitas();
        else if (v === 'pacientes') renderPacientes();
        else if (v === 'clientes') renderClientes();
    });

    /* ============================================================
       Render orchestrator
       ============================================================ */
    function renderAll() {
        renderStats();
        renderChart();
        renderMiniAgenda();
        renderRecentTable();
        renderCitas();
        renderPacientes();
        renderClientes();
        renderDateStrip();
        renderAgenda();
        renderNotifications();
    }

    /* ============================================================
       AI Assistant (streaming chat — API preserved)
       ============================================================ */
    const chatContainer = $('chat-container');
    const chatInput = $('chat-input');
    const chatForm = $('chat-form');
    const sendBtn = $('send-btn');
    const WELCOME = chatContainer.innerHTML;
    let conversationId = localStorage.getItem('conversation_id');
    let streaming = false;
    let currentAbortController = null;

    async function loadChatHistory() {
        chatContainer.innerHTML = '';
        const sessionStr = localStorage.getItem('clinic_session');
        if (!sessionStr) {
            chatContainer.innerHTML = WELCOME;
            return;
        }
        let query = '';
        try {
            const sessionObj = JSON.parse(sessionStr);
            const vetId = sessionObj.veterinary_id;
            query = `?veterinary_id=${vetId}&user_id=1`;
        } catch (e) {
            chatContainer.innerHTML = WELCOME;
            return;
        }
        if (conversationId) {
            query = `?conversation_id=${encodeURIComponent(conversationId)}`;
        }
        try {
            const res = await fetch(`/api/chat/history${query}`);
            if (res.ok) {
                const data = await res.json();
                if (data.conversation_id) {
                    conversationId = data.conversation_id;
                    localStorage.setItem('conversation_id', conversationId);
                }
                if (data.history && data.history.length > 0) {
                    chatContainer.innerHTML = '';
                    data.history.forEach(msg => {
                        const sender = msg.role === 'assistant' ? 'bot' : 'user';
                        addMessage(msg.content, sender, sender === 'bot');
                    });
                } else {
                    chatContainer.innerHTML = WELCOME;
                }
            } else {
                chatContainer.innerHTML = WELCOME;
            }
        } catch (e) {
            console.error('Error al cargar historial', e);
            chatContainer.innerHTML = WELCOME;
        }
    }

    function addMessage(text, sender, isMarkdown) {
        const wrap = document.createElement('div');
        wrap.className = `message ${sender}`;
        if (sender === 'bot') {
            wrap.innerHTML = `<span class="msg-avatar"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09ZM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.456-2.456L14.25 6l1.035-.259a3.375 3.375 0 002.456-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456Z"/></svg></span>
                <div class="msg-body">${isMarkdown ? marked.parse(text) : `<p>${escapeHtml(text)}</p>`}</div>`;
        } else {
            wrap.innerHTML = `<div class="msg-body">${escapeHtml(text)}</div>`;
        }
        chatContainer.appendChild(wrap);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return wrap;
    }

    function showToolIndicator(label) {
        hideToolIndicators();
        const indicator = document.createElement('div');
        indicator.className = 'tool-indicator';
        indicator.id = 'activeToolIndicator';
        indicator.innerHTML = `
            <div class="tool-spinner"></div>
            <span class="tool-label">${escapeHtml(label)}</span>
        `;
        chatContainer.appendChild(indicator);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function hideToolIndicators() {
        const existing = document.getElementById('activeToolIndicator');
        if (existing) existing.remove();
    }

    function appendStreamingMessage() {
        const msgId = 'stream-' + Date.now();
        const msgWrap = document.createElement('div');
        msgWrap.className = 'message bot';
        msgWrap.id = msgId;
        msgWrap.innerHTML = `
            <span class="msg-avatar"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09ZM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.456-2.456L14.25 6l1.035-.259a3.375 3.375 0 002.456-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456Z"/></svg></span>
            <div class="msg-body">
                <div class="message-bubble streaming-bubble"><span class="streaming-cursor"></span></div>
            </div>`;
        chatContainer.appendChild(msgWrap);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return msgId;
    }

    function updateStreamBubble(msgId, text) {
        const msgDiv = document.getElementById(msgId);
        if (!msgDiv) return;
        const bubble = msgDiv.querySelector('.streaming-bubble');
        if (!bubble) return;
        bubble.textContent = text;
        bubble.innerHTML += '<span class="streaming-cursor"></span>';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function finalizeStreamBubble(msgId, text) {
        const msgDiv = document.getElementById(msgId);
        if (!msgDiv) return;
        const bubble = msgDiv.querySelector('.streaming-bubble');
        if (!bubble) return;
        bubble.classList.remove('streaming-bubble');
        bubble.innerHTML = marked.parse(text);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    async function sendMessage(textOverride) {
        const text = (textOverride != null ? textOverride : chatInput.value).trim();
        if (!text || streaming) return;
        if (textOverride == null) chatInput.value = '';
        addMessage(text, 'user');

        streaming = true;
        sendBtn.disabled = true;
        
        // Crear la burbuja vacía con cursor parpadeando inmediatamente
        const streamMsgId = appendStreamingMessage();

        const payload = {
            question: text,
            conversation_id: conversationId,
            veterinary_id: vetSelector.value ? parseInt(vetSelector.value, 10) : null
        };

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) throw new Error('Network error');

            const newConvId = response.headers.get('X-Conversation-Id');
            if (newConvId) { conversationId = newConvId; localStorage.setItem('conversation_id', conversationId); }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            let acc = '';
            let currentEvent = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Guardar línea incompleta

                for (const line of lines) {
                    if (line.startsWith('event: ')) {
                        currentEvent = line.slice(7).trim();
                    } else if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6).trim();
                        if (!jsonStr || !currentEvent) continue;
                        
                        try {
                            const data = JSON.parse(jsonStr);
                            if (currentEvent === 'tool_start') {
                                showToolIndicator(data.label || data.tool || '');
                            } else if (currentEvent === 'token') {
                                acc += data.token;
                                updateStreamBubble(streamMsgId, acc);
                            } else if (currentEvent === 'done') {
                                finalizeStreamBubble(streamMsgId, acc);
                            } else if (currentEvent === 'error') {
                                acc = data.message;
                                const bubble = document.getElementById(streamMsgId).querySelector('.msg-body .message-bubble');
                                bubble.innerHTML = `<p style="color:#B23B30">${escapeHtml(data.message)}</p>`;
                            }
                        } catch (parseErr) {
                            // Ignorar
                        }
                        currentEvent = '';
                    }
                }
            }
            if (!acc.trim()) {
                const bubble = document.getElementById(streamMsgId).querySelector('.msg-body .message-bubble');
                bubble.classList.remove('streaming-bubble');
                bubble.innerHTML = '<p>No recibí respuesta. Intenta reformular la consulta.</p>';
            }

            loadData();
        } catch (err) {
            const bubble = document.getElementById(streamMsgId).querySelector('.msg-body .message-bubble');
            bubble.classList.remove('streaming-bubble');
            bubble.innerHTML = '<p style="color:#B23B30">Ocurrió un error al procesar tu solicitud. Revisa la conexión e inténtalo de nuevo.</p>';
        } finally {
            streaming = false;
            sendBtn.disabled = false;
            hideToolIndicators();
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    function askAI(prompt) {
        switchView('asistente');
        setTimeout(() => sendMessage(prompt), 200);
    }

    chatForm.addEventListener('submit', (e) => { e.preventDefault(); sendMessage(); });

    document.querySelectorAll('#suggest-row .suggest, #side-prompts .side-prompt').forEach(b => {
        b.addEventListener('click', () => askAI(b.dataset.prompt));
    });

    $('new-conversation').addEventListener('click', async () => {
        const sessionStr = localStorage.getItem('clinic_session');
        let query = '';
        if (conversationId) {
            query = `?conversation_id=${encodeURIComponent(conversationId)}`;
        } else if (sessionStr) {
            try {
                const sessionObj = JSON.parse(sessionStr);
                query = `?veterinary_id=${sessionObj.veterinary_id}&user_id=1`;
            } catch (e) {}
        }
        
        try {
            await fetch(`/api/chat/history${query}`, { method: 'DELETE' });
        } catch (e) {
            console.error('Error al borrar historial en el servidor', e);
        }

        conversationId = null;
        localStorage.removeItem('conversation_id');
        chatContainer.innerHTML = WELCOME;
        chatInput.focus();
    });

    /* ============================================================
       Init
       ============================================================ */
    loadVeterinarias().then(checkSession);
})();
