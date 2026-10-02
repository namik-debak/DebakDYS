/* ═══════════════════════════════════════════════════════════════════
   DYS — Doküman Yönetim Sistemi
   JavaScript — Arama, Filtre, Modal, Toast, Tab, Grafik
   ═══════════════════════════════════════════════════════════════════ */

// ── CSRF Koruması ──────────────────────────────────────────────────
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// Tüm POST formlarına gizli csrf_token alanı ekler (form başına elle eklemeye gerek kalmaz).
function initCsrf() {
    const token = getCsrfToken();
    if (!token) return;
    document.querySelectorAll('form').forEach(form => {
        const method = (form.getAttribute('method') || 'get').toLowerCase();
        if (method !== 'post') return;
        if (form.querySelector('input[name="csrf_token"]')) return;
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'csrf_token';
        input.value = token;
        form.appendChild(input);
    });

    // fetch() ile yapılan POST/PUT/DELETE isteklerine CSRF başlığı ekle.
    const originalFetch = window.fetch;
    window.fetch = function (input, init) {
        init = init || {};
        const method = (init.method || 'GET').toUpperCase();
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method)) {
            init.headers = new Headers(init.headers || {});
            if (!init.headers.has('X-CSRFToken')) {
                init.headers.set('X-CSRFToken', token);
            }
        }
        return originalFetch(input, init);
    };
}

// ── Toast Notification System ──────────────────────────────────────
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${icons[type] || icons.info}</span>
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── Tab System (erişilebilir: ARIA + klavye) ───────────────────────
function initTabs() {
    document.querySelectorAll('[data-tab-group]').forEach(group => {
        const tabs = Array.from(group.querySelectorAll('.tab-item'));
        group.setAttribute('role', 'tablist');

        function activate(tab) {
            const targetId = tab.dataset.tab;
            const contentContainer = document.querySelector(`[data-tab-content="${group.dataset.tabGroup}"]`);
            tabs.forEach(t => {
                const isActive = t === tab;
                t.classList.toggle('active', isActive);
                t.setAttribute('aria-selected', isActive ? 'true' : 'false');
                t.setAttribute('tabindex', isActive ? '0' : '-1');
            });
            if (contentContainer) {
                contentContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                const target = contentContainer.querySelector(`#${targetId}`);
                if (target) target.classList.add('active');
            }
        }

        tabs.forEach((tab, idx) => {
            tab.setAttribute('role', 'tab');
            if (tab.dataset.tab) tab.setAttribute('aria-controls', tab.dataset.tab);
            const isActive = tab.classList.contains('active');
            tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
            tab.setAttribute('tabindex', isActive ? '0' : '-1');

            tab.addEventListener('click', () => activate(tab));
            tab.addEventListener('keydown', (e) => {
                let next = null;
                if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = tabs[(idx + 1) % tabs.length];
                else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = tabs[(idx - 1 + tabs.length) % tabs.length];
                else if (e.key === 'Home') next = tabs[0];
                else if (e.key === 'End') next = tabs[tabs.length - 1];
                if (next) { e.preventDefault(); activate(next); next.focus(); }
            });
        });
    });
}

// ── Modal System (erişilebilir: focus tuzağı + ARIA + odak geri yükleme) ──
let _lastFocusedBeforeModal = null;
const _focusableSelector = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

function _trapFocus(e, modal) {
    if (e.key !== 'Tab') return;
    const focusable = Array.from(modal.querySelectorAll(_focusableSelector))
        .filter(el => el.offsetParent !== null);
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first.focus();
    }
}

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    _lastFocusedBeforeModal = document.activeElement;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';

    const dialog = modal.querySelector('.modal') || modal;
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    const title = dialog.querySelector('.modal-title');
    if (title) {
        if (!title.id) title.id = modalId + '-title';
        dialog.setAttribute('aria-labelledby', title.id);
    }

    const focusable = modal.querySelectorAll(_focusableSelector);
    if (focusable.length) focusable[0].focus();

    modal._trapHandler = (e) => _trapFocus(e, modal);
    modal.addEventListener('keydown', modal._trapHandler);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.remove('active');
    document.body.style.overflow = '';
    if (modal._trapHandler) {
        modal.removeEventListener('keydown', modal._trapHandler);
        modal._trapHandler = null;
    }
    if (_lastFocusedBeforeModal && typeof _lastFocusedBeforeModal.focus === 'function') {
        _lastFocusedBeforeModal.focus();
        _lastFocusedBeforeModal = null;
    }
}

// Close modal on overlay click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => closeModal(m.id));
    }
});

// ── Table Filtering ────────────────────────────────────────────────
function filterTable(tableId, filters) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const rows = tbody.querySelectorAll('tr');

    rows.forEach(row => {
        let show = true;

        for (const [key, value] of Object.entries(filters)) {
            if (!value || value === 'all' || value === '') continue;

            const cell = row.querySelector(`[data-filter="${key}"]`);
            if (cell) {
                const cellText = cell.textContent.trim().toLowerCase();
                const filterText = value.toLowerCase();

                if (key === 'search') {
                    // Search across all cells
                    const rowText = row.textContent.trim().toLowerCase();
                    if (!rowText.includes(filterText)) {
                        show = false;
                    }
                } else {
                    if (cellText !== filterText) {
                        show = false;
                    }
                }
            }
        }

        row.style.display = show ? '' : 'none';
    });

    // Update count
    const visibleRows = tbody.querySelectorAll('tr:not([style*="display: none"])').length;
    const countEl = document.getElementById(`${tableId}-count`);
    if (countEl) {
        countEl.textContent = visibleRows;
    }
}

// ── File Upload Handling ───────────────────────────────────────────
function initFileUpload() {
    const uploadAreas = document.querySelectorAll('.file-upload-area');

    uploadAreas.forEach(area => {
        const input = area.querySelector('input[type="file"]');

        area.addEventListener('click', () => {
            if (input) input.click();
        });

        area.addEventListener('dragover', (e) => {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', () => {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', (e) => {
            e.preventDefault();
            area.classList.remove('dragover');
            if (input && e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                updateFileName(area, e.dataTransfer.files[0]);
            }
        });

        if (input) {
            input.addEventListener('change', () => {
                if (input.files.length > 0) {
                    updateFileName(area, input.files[0]);
                }
            });
        }
    });
}

function updateFileName(area, file) {
    const textEl = area.querySelector('.upload-text');
    const hintEl = area.querySelector('.upload-hint');
    if (textEl) {
        textEl.textContent = file.name;
    }
    if (hintEl) {
        const sizeKB = (file.size / 1024).toFixed(1);
        hintEl.textContent = `${sizeKB} KB`;
    }
}

// ── Document Number Generator ──────────────────────────────────────
function generateDocNo(processCode, docType) {
    const tipKisaltma = {
        'Politika': 'PO', 'El Kitabı': 'EK', 'Prosedür': 'PR',
        'Talimat': 'TL', 'Plan': 'PL', 'Spesifikasyon': 'SP',
        'Form': 'FR', 'Liste': 'LS', 'Dış Kaynaklı Doküman': 'DK'
    };
    const kisa = tipKisaltma[docType] || 'XX';
    return `${processCode}-${kisa}-`;
}

function updateDocNo() {
    const processSelect = document.getElementById('surec_id');
    const typeSelect = document.getElementById('dokuman_tipi');
    const docNoInput = document.getElementById('dokuman_no');

    if (!processSelect || !typeSelect || !docNoInput) return;
    // Düzenleme formunda mevcut numara korunur
    if (docNoInput.dataset.locked === 'true') return;

    const selectedOption = processSelect.options[processSelect.selectedIndex];
    const processCode = selectedOption ? selectedOption.dataset.code : '';
    const docType = typeSelect.value;
    const surecId = processSelect.value;

    if (processCode && docType && surecId) {
        if (!docNoInput.value || docNoInput.dataset.autoGenerated === 'true') {
            const base = (window.DYS_BASE || '').replace(/\/$/, '');
            const url = `${base}/api/documents/next-number?surec_id=${encodeURIComponent(surecId)}&tip=${encodeURIComponent(docType)}`;
            fetch(url, { headers: { 'Accept': 'application/json' } })
                .then(r => r.ok ? r.json() : Promise.reject())
                .then(data => {
                    if (data && data.dokuman_no) {
                        docNoInput.value = data.dokuman_no;
                        docNoInput.dataset.autoGenerated = 'true';
                        const elKod = document.getElementById('proc-preview-kod');
                        if (elKod) elKod.textContent = data.dokuman_no;
                    }
                })
                .catch(() => {
                    docNoInput.value = generateDocNo(processCode, docType);
                    docNoInput.dataset.autoGenerated = 'true';
                });
        }
    }
}

// ── Document Level Auto-Set ────────────────────────────────────────
function updateDocLevel() {
    const typeSelect = document.getElementById('dokuman_tipi');
    const levelSelect = document.getElementById('dokuman_seviyesi');
    if (!typeSelect || !levelSelect) return;

    const levelMap = {
        'Politika': '1', 'El Kitabı': '1',
        'Prosedür': '2',
        'Talimat': '3', 'Plan': '3', 'Spesifikasyon': '3',
        'Form': '4', 'Liste': '4',
        'Dış Kaynaklı Doküman': '5'
    };

    const level = levelMap[typeSelect.value];
    if (level) {
        levelSelect.value = level;
    }
}

// ── Confirm Delete ─────────────────────────────────────────────────
function confirmDelete(formId, itemName) {
    const confirmed = confirm(`"${itemName}" silinecek. Onaylıyor musunuz?`);
    if (confirmed) {
        document.getElementById(formId).submit();
    }
}

// ── Sidebar Active State ───────────────────────────────────────────
function initSidebar() {
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-item').forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath === href) {
            item.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            item.classList.add('active');
        }
    });
}

// ── Mobil Kenar Çubuğu (Drawer) ────────────────────────────────────
function initMobileDrawer() {
    const toggle = document.getElementById('menu-toggle');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!toggle) return;

    const open = () => {
        document.body.classList.add('sidebar-open');
        toggle.setAttribute('aria-expanded', 'true');
    };
    const close = () => {
        document.body.classList.remove('sidebar-open');
        toggle.setAttribute('aria-expanded', 'false');
    };
    const isOpen = () => document.body.classList.contains('sidebar-open');

    toggle.addEventListener('click', () => (isOpen() ? close() : open()));
    if (backdrop) backdrop.addEventListener('click', close);

    // Bir menü öğesine tıklanınca çekmeceyi kapat.
    document.querySelectorAll('.sidebar .nav-item').forEach(item => {
        item.addEventListener('click', () => { if (isOpen()) close(); });
    });

    // Escape ile kapat.
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isOpen()) close();
    });
}

// ── Global Doküman Arama ───────────────────────────────────────────
function initGlobalSearch() {
    const searchInput = document.getElementById('global-search');
    if (!searchInput) return;

    // Uygulama IIS/ARR arkasında /dys gibi bir prefix ile çalışabilir.
    const base = (window.DYS_BASE || '').replace(/\/$/, '');

    const doSearch = () => {
        const query = searchInput.value.trim();
        if (query) {
            window.location.href = `${base}/search?q=${encodeURIComponent(query)}`;
        }
    };

    // Yalnızca Enter ile ara (yazarken kesintiye uğramaması için).
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            doSearch();
        }
    });

    // Arama ikonuna tıklayınca da ara.
    const searchIcon = document.querySelector('.header-search .search-icon');
    if (searchIcon) {
        searchIcon.style.cursor = 'pointer';
        searchIcon.addEventListener('click', doSearch);
    }
}

// ── Doküman Tipi Bazlı Şablon Gösterimi ────────────────────────────
function initDocTemplate() {
    const typeSelect = document.getElementById('dokuman_tipi');
    const container = document.getElementById('sablon-container');
    if (!typeSelect || !container) return;

    function syncProcedurePreview() {
        const kod = document.getElementById('dokuman_no');
        const baslik = document.getElementById('baslik');
        const surec = document.getElementById('surec_id');
        const elKod = document.getElementById('proc-preview-kod');
        const elBaslik = document.getElementById('proc-preview-baslik');
        const elSurec = document.getElementById('proc-preview-surec');
        if (elKod && kod) elKod.textContent = kod.value || '—';
        if (elBaslik && baslik) elBaslik.textContent = baslik.value || 'Prosedür Başlığı';
        if (elSurec && surec && surec.selectedOptions[0]) {
            const opt = surec.selectedOptions[0];
            elSurec.textContent = (opt.textContent || '').trim().toUpperCase() || '—';
        }
    }

    function toggleTemplate() {
        const selected = typeSelect.value;
        let anyVisible = false;
        container.querySelectorAll('[data-sablon-tip]').forEach(block => {
            const match = block.dataset.sablonTip === selected;
            block.style.display = match ? 'block' : 'none';
            // Görünmeyen blokların alanlarını devre dışı bırak ki forma gönderilmesin.
            block.querySelectorAll('textarea, input').forEach(f => { f.disabled = !match; });
            if (match) anyVisible = true;
        });
        const hint = document.getElementById('sablon-hint');
        if (hint) hint.style.display = anyVisible ? 'none' : 'block';
        if (selected === 'Prosedür') syncProcedurePreview();
    }

    typeSelect.addEventListener('change', toggleTemplate);
    ['dokuman_no', 'baslik', 'surec_id'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', syncProcedurePreview);
        if (el) el.addEventListener('change', syncProcedurePreview);
    });
    initDocPickers(container);
    toggleTemplate();
}

// ── Prosedür 6.0 / 7.0 aramalı doküman seçici ───────────────────────
function initDocPickers(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-doc-picker]').forEach(initOneDocPicker);
}

function initOneDocPicker(wrap) {
    if (wrap.dataset.ready) return;
    wrap.dataset.ready = '1';

    const hidden = wrap.querySelector('.doc-picker-input, input[type="hidden"]');
    const search = wrap.querySelector('.doc-picker-search');
    const results = wrap.querySelector('.doc-picker-results');
    const selectedList = wrap.querySelector('.doc-picker-selected');
    if (!hidden || !search || !results || !selectedList) return;

    let selected = [];
    try {
        let raw = wrap.getAttribute('data-initial') || '[]';
        let parsed = JSON.parse(raw);
        // tojson string olarak çift kodladıysa
        if (typeof parsed === 'string') parsed = JSON.parse(parsed);
        if (Array.isArray(parsed)) {
            selected = parsed.map(normalizePickerItem).filter(Boolean);
        } else if (typeof parsed === 'string' && parsed.trim()) {
            // eski düz metin
            selected = parsed.split('\n').filter(Boolean).map(line => ({
                id: null, dokuman_no: '', baslik: line, label: line
            }));
        }
    } catch (e) {
        selected = [];
    }

    let timer = null;
    let abortCtrl = null;

    function normalizePickerItem(item) {
        if (!item || typeof item !== 'object') return null;
        const no = item.dokuman_no || '';
        const baslik = item.baslik || '';
        if (!no && !baslik) return null;
        return {
            id: item.id || null,
            dokuman_no: no,
            baslik: baslik,
            dokuman_tipi: item.dokuman_tipi || '',
            label: item.label || `${no}${no && baslik ? ' — ' : ''}${baslik}`,
        };
    }

    function syncHidden() {
        hidden.value = JSON.stringify(selected.map(s => ({
            id: s.id, dokuman_no: s.dokuman_no, baslik: s.baslik
        })));
    }

    function renderSelected() {
        selectedList.innerHTML = '';
        selected.forEach((item, idx) => {
            const li = document.createElement('li');
            li.className = 'doc-picker-chip';
            li.innerHTML = `<span class="doc-picker-chip-text"></span>` +
                `<button type="button" class="doc-picker-chip-remove" aria-label="Kaldır">✕</button>`;
            li.querySelector('.doc-picker-chip-text').textContent = item.label;
            li.querySelector('.doc-picker-chip-remove').addEventListener('click', () => {
                selected.splice(idx, 1);
                renderSelected();
                syncHidden();
            });
            selectedList.appendChild(li);
        });
        syncHidden();
    }

    function hideResults() {
        results.hidden = true;
        results.innerHTML = '';
    }

    function showResults(items) {
        results.innerHTML = '';
        if (!items.length) {
            results.innerHTML = `<div class="doc-picker-empty">Sonuç yok</div>`;
            results.hidden = false;
            return;
        }
        items.forEach(item => {
            const already = selected.some(s => (s.id && item.id && s.id === item.id) ||
                (s.dokuman_no && s.dokuman_no === item.dokuman_no));
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'doc-picker-result' + (already ? ' is-selected' : '');
            btn.setAttribute('role', 'option');
            btn.disabled = already;
            btn.innerHTML = `<strong></strong><span></span>`;
            btn.querySelector('strong').textContent = item.dokuman_no;
            btn.querySelector('span').textContent = item.baslik;
            btn.addEventListener('click', () => {
                if (already) return;
                selected.push(normalizePickerItem(item));
                renderSelected();
                search.value = '';
                hideResults();
                search.focus();
            });
            results.appendChild(btn);
        });
        results.hidden = false;
    }

    async function doSearch(q) {
        if (abortCtrl) abortCtrl.abort();
        abortCtrl = new AbortController();
        const root = (window.DYS_BASE || '');
        const url = `${root}/api/documents/lookup?q=${encodeURIComponent(q)}&limit=25`;
        try {
            const resp = await fetch(url, { signal: abortCtrl.signal, credentials: 'same-origin' });
            if (!resp.ok) throw new Error('lookup failed');
            const data = await resp.json();
            showResults(data.results || []);
        } catch (err) {
            if (err.name === 'AbortError') return;
            showResults([]);
        }
    }

    search.addEventListener('input', () => {
        const q = search.value.trim();
        clearTimeout(timer);
        if (q.length < 1) {
            hideResults();
            return;
        }
        timer = setTimeout(() => doSearch(q), 220);
    });

    search.addEventListener('focus', () => {
        if (search.value.trim().length >= 1) doSearch(search.value.trim());
    });

    document.addEventListener('click', (e) => {
        if (!wrap.contains(e.target)) hideResults();
    });

    renderSelected();
}

// ── Distribution Read Confirmation ─────────────────────────────────
function markAsRead(distId) {
    const base = (window.DYS_BASE || '').replace(/\/$/, '');
    fetch(`${base}/api/distribution/${distId}/read`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast('Doküman okundu olarak işaretlendi.', 'success');
                const badge = document.querySelector(`[data-dist-id="${distId}"]`);
                if (badge) {
                    badge.textContent = 'Okundu';
                    badge.className = 'status-badge onayli';
                }
            }
        })
        .catch(() => showToast('İşlem başarısız.', 'error'));
}

// ── Chart.js Initialization (if charts exist) ──────────────────────
function initDashboardCharts() {
    // Status Distribution Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx && typeof Chart !== 'undefined') {
        const statusData = JSON.parse(statusCtx.dataset.values || '{}');
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(statusData),
                datasets: [{
                    data: Object.values(statusData),
                    backgroundColor: [
                        '#94a3b8', // Taslak
                        '#f59e0b', // İncelemede
                        '#10b981', // Onaylı
                        '#ef4444', // İptal
                        '#64748b', // Eskimiş
                    ],
                    borderWidth: 0,
                    borderRadius: 4,
                    spacing: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Inter', size: 11 },
                            padding: 12,
                            usePointStyle: true,
                            pointStyleWidth: 8,
                        }
                    }
                },
                cutout: '70%',
            }
        });
    }

    // Process Distribution Chart
    const processCtx = document.getElementById('processChart');
    if (processCtx && typeof Chart !== 'undefined') {
        const processData = JSON.parse(processCtx.dataset.values || '{}');
        const labels = Object.keys(processData);
        const values = Object.values(processData);
        const colors = labels.map(l => {
            if (l.startsWith('D')) return '#3b82f6';
            if (l.startsWith('M')) return '#10b981';
            return '#f59e0b';
        });

        new Chart(processCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 0,
                    borderRadius: 4,
                    maxBarThickness: 28,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: '#64748b',
                            font: { family: 'Inter', size: 10 },
                            maxRotation: 45,
                        },
                        border: { display: false },
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: {
                            color: '#64748b',
                            font: { family: 'Inter', size: 10 },
                            stepSize: 1,
                        },
                        border: { display: false },
                        beginAtZero: true,
                    }
                }
            }
        });
    }

    // Standard Distribution Chart
    const stdCtx = document.getElementById('standardChart');
    if (stdCtx && typeof Chart !== 'undefined') {
        const stdData = JSON.parse(stdCtx.dataset.values || '{}');
        new Chart(stdCtx, {
            type: 'polarArea',
            data: {
                labels: Object.keys(stdData),
                datasets: [{
                    data: Object.values(stdData),
                    backgroundColor: [
                        'rgba(139, 92, 246, 0.5)',  // IATF
                        'rgba(16, 185, 129, 0.5)',   // ISO 14001
                        'rgba(245, 158, 11, 0.5)',   // ISO 45001
                        'rgba(59, 130, 246, 0.5)',   // ISO 27001
                    ],
                    borderWidth: 0,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: '#94a3b8',
                            font: { family: 'Inter', size: 11 },
                            padding: 12,
                            usePointStyle: true,
                        }
                    }
                },
                scales: {
                    r: {
                        grid: { color: 'rgba(255,255,255,0.06)' },
                        ticks: { display: false },
                    }
                }
            }
        });
    }
}

// ── Theme Management ───────────────────────────────────────────────
function initTheme() {
    const toggleBtn = document.getElementById('theme-toggle');
    const themeIcon = toggleBtn ? toggleBtn.querySelector('.theme-icon') : null;
    
    const savedTheme = localStorage.getItem('dys-theme');
    if (savedTheme === 'light-glass') {
        document.documentElement.setAttribute('data-theme', 'light-glass');
        if (themeIcon) themeIcon.textContent = '🌙';
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            if (currentTheme === 'light-glass') {
                document.documentElement.removeAttribute('data-theme');
                localStorage.setItem('dys-theme', 'dark');
                if (themeIcon) themeIcon.textContent = '🌞';
            } else {
                document.documentElement.setAttribute('data-theme', 'light-glass');
                localStorage.setItem('dys-theme', 'light-glass');
                if (themeIcon) themeIcon.textContent = '🌙';
            }
        });
    }
}

// ── Initialize on DOM Ready ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initCsrf();
    initTheme();
    initTabs();
    initFileUpload();
    initSidebar();
    initMobileDrawer();
    initGlobalSearch();
    initDocTemplate();
    initDashboardCharts();

    // Auto-update doc number when process or type changes
    const processSelect = document.getElementById('surec_id');
    const typeSelect = document.getElementById('dokuman_tipi');
    if (processSelect) processSelect.addEventListener('change', () => { updateDocNo(); updateDocLevel(); });
    if (typeSelect) typeSelect.addEventListener('change', () => { updateDocNo(); updateDocLevel(); });

    // Flash messages from server
    const flashMessages = document.querySelectorAll('[data-flash]');
    flashMessages.forEach(el => {
        showToast(el.dataset.flash, el.dataset.flashType || 'info');
        el.remove();
    });
});



