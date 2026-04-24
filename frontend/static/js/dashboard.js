// DWH Quality Agent Dashboard JavaScript

// Global state passed from template (spRecordsJson is declared in template)
let initialMetrics = [];
let initialCurrentPage = 1;
let pageSize = 15;
let activeView = 'quality';

const tableState = {
    metrics: [],
    currentPage: 1,
    pageSize: 15,
};

function runSpLlmAnalysis() {
    const btn = document.getElementById('spLlmBtn');
    const statusBox = document.getElementById('spStatusBox');
    if (btn) { btn.textContent = 'Analyzing…'; btn.disabled = true; }
    if (statusBox) statusBox.textContent = 'Running AI analysis — this may take a minute…';
    fetch('/api/sp-llm-analyze', { method: 'POST' })
        .then(r => r.json())
        .then(data => {
            if (statusBox) statusBox.textContent = data.success ? `AI analysis complete — ${data.analyzed} SPs analyzed. Refreshing page…` : `Error: ${data.error}`;
            if (data.success) setTimeout(() => window.location.reload(), 1200);
        })
        .catch(err => { if (statusBox) statusBox.textContent = 'AI analysis request failed: ' + err; })
        .finally(() => { if (btn) { btn.textContent = 'Analyze with AI'; btn.disabled = false; } });
}

function exportSpCSV() {
    console.log('exportSpCSV called');
    console.log('spRecordsJson:', spRecordsJson);
    console.log('spRecordsJson length:', spRecordsJson ? spRecordsJson.length : 'undefined');
    
    if (!spRecordsJson || !spRecordsJson.length) {
        console.warn('No SP records to export');
        alert('No data available to export. Please refresh the page first.');
        return;
    }
    const header = ['SP Name','Schema','Last Modified','Params','Quality Score','Code Quality Issues'];
    const rows = spRecordsJson.map(r => {
        const issuesText = Array.isArray(r.issues) ? r.issues.join('; ') : (r.issues || '');
        return [
            '"' + (r.sp_name || '').replace(/"/g, '""') + '"',
            '"' + (r.schema_name || '').replace(/"/g, '""') + '"',
            '"' + (r.last_modified || '').replace(/"/g, '""') + '"',
            r.parameter_count || 0,
            r.quality_score !== null && r.quality_score !== undefined ? r.quality_score : '',
            '"' + issuesText.replace(/"/g, '""') + '"'
        ].join(',');
    });
    const csv = [header.join(','), ...rows].join('\n');
    console.log('CSV generated, rows:', rows.length);
    const a = document.createElement('a');
    a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    a.download = 'sp_analysis.csv';
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    console.log('CSV download triggered');
}

function sortMetrics(metrics) {
    return [...metrics].sort((left, right) => {
        const leftScore = Number.isFinite(Number(left.quality_score)) ? Number(left.quality_score) : Number.POSITIVE_INFINITY;
        const rightScore = Number.isFinite(Number(right.quality_score)) ? Number(right.quality_score) : Number.POSITIVE_INFINITY;
        if (leftScore !== rightScore) {
            return leftScore - rightScore;
        }
        const leftTable = String(left.table || '').toLowerCase();
        const rightTable = String(right.table || '').toLowerCase();
        return leftTable.localeCompare(rightTable);
    });
}

function getSavedColumnWidths() {
    try {
        const saved = localStorage.getItem('dwh-quality-column-widths-v1');
        return saved ? JSON.parse(saved) : null;
    } catch (error) {
        return null;
    }
}

function saveColumnWidths(widths) {
    try {
        localStorage.setItem('dwh-quality-column-widths-v1', JSON.stringify(widths));
    } catch (error) {
        // Ignore storage issues.
    }
}

function applyColumnWidths(widths) {
    const cols = document.querySelectorAll('.quality-table col[data-col-index]');
    cols.forEach((col, index) => {
        if (Array.isArray(widths) && Number.isFinite(Number(widths[index]))) {
            col.style.width = `${Number(widths[index])}px`;
        }
    });
}

function captureColumnWidths() {
    const cols = document.querySelectorAll('.quality-table col[data-col-index]');
    return Array.from(cols).map((col) => Math.max(80, Math.round(col.getBoundingClientRect().width)));
}

function initResizableColumns() {
    const cols = Array.from(document.querySelectorAll('.quality-table col[data-col-index]'));
    const handles = Array.from(document.querySelectorAll('.column-resizer'));
    if (!cols.length || !handles.length) {
        return;
    }

    const savedWidths = getSavedColumnWidths();
    if (Array.isArray(savedWidths) && savedWidths.length === cols.length) {
        applyColumnWidths(savedWidths);
    }

    let activeResize = null;

    handles.forEach((handle) => {
        handle.addEventListener('mousedown', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const index = Number(handle.dataset.colIndex);
            const col = cols[index];
            if (!col) {
                return;
            }
            const width = parseFloat(getComputedStyle(col).width) || col.getBoundingClientRect().width;
            activeResize = {
                index,
                startX: event.clientX,
                startWidth: width,
            };
            document.body.classList.add('is-resizing-columns');
        });
    });

    window.addEventListener('mousemove', (event) => {
        if (!activeResize) {
            return;
        }
        const col = cols[activeResize.index];
        if (!col) {
            return;
        }
        const nextWidth = Math.max(80, Math.round(activeResize.startWidth + (event.clientX - activeResize.startX)));
        col.style.width = `${nextWidth}px`;
        saveColumnWidths(captureColumnWidths());
    });

    window.addEventListener('mouseup', () => {
        if (activeResize) {
            saveColumnWidths(captureColumnWidths());
            activeResize = null;
            document.body.classList.remove('is-resizing-columns');
        }
    });
}

function formatMetricValues(value) {
    if (Array.isArray(value)) {
        const entries = value.map((entry) => {
            if (entry && typeof entry === 'object') {
                return entry.column || entry.name || entry.value || JSON.stringify(entry);
            }
            return entry;
        }).filter(Boolean);
        return entries.length ? entries.join(', ') : '<span class="null-value">—</span>';
    }
    if (value === null || value === undefined) {
        return '<span class="null-value">—</span>';
    }
    const text = String(value).trim();
    if (!text || text === 'None' || text === 'null' || text === 'NULL') {
        return '<span class="null-value">—</span>';
    }
    return text;
}

function formatColumnIssueSummary(columnIssues) {
    if (!columnIssues || typeof columnIssues !== 'object') {
        return '<span class="null-value">—</span>';
    }

    const entries = Object.entries(columnIssues).map(([columnName, problems]) => {
        let problemText = 'Issue detected';
        if (Array.isArray(problems)) {
            const cleaned = problems.map((problem) => String(problem).trim()).filter(Boolean);
            if (cleaned.length) {
                problemText = cleaned.join('; ');
            }
        } else if (problems !== null && problems !== undefined) {
            const text = String(problems).trim();
            if (text) {
                problemText = text;
            }
        }
        return `${columnName} (${problemText})`;
    });

    return entries.length ? entries.join('; ') : '<span class="null-value">—</span>';
}

function formatIssueSummary(item) {
    // Show all issues including duplicates, nulls, PK/FK
    const issues = Array.isArray(item.issues)
        ? item.issues.map((issue) => String(issue).trim()).filter(Boolean)
        : [];
    
    if (issues.length) {
        return issues.join('; ');
    }

    // Check column issues
    const columnIssues = item.column_issues && typeof item.column_issues === 'object' ? item.column_issues : null;
    if (columnIssues && Object.keys(columnIssues).length) {
        return formatColumnIssueSummary(columnIssues);
    }

    return '<span style="color: #22c55e;">Healthy</span>';
}

function csvEscape(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return '"' + text.replace(/"/g, '""') + '"';
}

function exportTableCSV() {
    if (!tableState.metrics.length) {
        document.getElementById('statusBox').textContent = 'No Gold tables available to export.';
        return;
    }

    const header = ['Table', 'Layer', 'Rows', 'Cols', 'PK', 'FK', 'Quality Score', 'Issue Columns', 'Issues'];
    const rows = [header];

    tableState.metrics.forEach((item) => {
        const issueColumns = formatColumnIssueSummary(item.column_issues);
        const issues = formatIssueSummary(item);
        rows.push([
            item.table || '',
            item.layer || 'gold',
            item.rows ?? '',
            item.column_count ?? '',
            formatMetricValues(item.pk_columns),
            formatMetricValues(item.fk_columns),
            item.quality_score ?? '',
            issueColumns,
            issues,
        ]);
    });

    const csv = '\ufeff' + rows.map((row) => row.map(csvEscape).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'dwh_gold_quality_table.csv';
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
        link.remove();
        URL.revokeObjectURL(url);
    }, 1000);
}

function renderRows() {
    const body = document.getElementById('tableBody');
    const pagerInfo = document.getElementById('pagerInfo');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    if (!body || !pagerInfo || !prevBtn || !nextBtn) {
        return;
    }
    const total = tableState.metrics.length;
    const totalPages = total ? Math.ceil(total / tableState.pageSize) : 1;
    const currentPage = Math.min(Math.max(tableState.currentPage, 1), totalPages);
    tableState.currentPage = currentPage;

    const start = (currentPage - 1) * tableState.pageSize;
    const visibleMetrics = tableState.metrics.slice(start, start + tableState.pageSize);

    if (!visibleMetrics.length) {
        body.innerHTML = '<tr><td colspan="8" style="color: var(--muted);">No Gold tables found in the latest run.</td></tr>';
        pagerInfo.textContent = 'Page 0 of 0';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
    }

    body.innerHTML = visibleMetrics.map((item) => {
        const issueColumns = formatColumnIssueSummary(item.column_issues);
        const issues = formatIssueSummary(item);
        const pk = formatMetricValues(item.pk_columns);
        const fk = formatMetricValues(item.fk_columns);
        return `
            <tr>
                <td>${item.table || '—'}</td>
                <td><span class="layer-tag">${item.layer || '—'}</span></td>
                <td>${item.rows ?? '—'}</td>
                <td>${item.column_count ?? '—'}</td>
                <td><div class="pkfk-block"><div><span class="kv-label">PK</span> ${pk}</div><div><span class="kv-label">FK</span> ${fk}</div></div></td>
                <td>${item.quality_score ?? '—'}%</td>
                <td>${issueColumns}</td>
                <td>${issues}</td>
            </tr>
        `;
    }).join('');

    pagerInfo.textContent = `Page ${currentPage} of ${totalPages} — showing ${start + 1}-${Math.min(start + tableState.pageSize, total)} of ${total}`;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
}

function setMetrics(metrics) {
    tableState.metrics = sortMetrics(Array.isArray(metrics) ? metrics : []);
    tableState.currentPage = 1;
    renderRows();
}

function changePage(delta) {
    tableState.currentPage += delta;
    renderRows();
}

function extractGoldMetrics(report) {
    if (!report) return [];

    if (report.report && typeof report.report === 'object') {
        const nestedMetrics = extractGoldMetrics(report.report);
        if (nestedMetrics.length) {
            return nestedMetrics;
        }
    }

    const directMetrics = Array.isArray(report.metrics) ? report.metrics : [];
    if (directMetrics.length) {
        const reportLayer = String(report.layer || report.check_type || '').toLowerCase();
        if (reportLayer === 'gold' || reportLayer === 'comprehensive' || !reportLayer) {
            return directMetrics;
        }
        return directMetrics.filter((item) => String(item.layer || '').toLowerCase() === 'gold');
    }

    const goldLayerReport = report.layer_reports && report.layer_reports.gold;
    if (goldLayerReport && Array.isArray(goldLayerReport.metrics)) {
        return goldLayerReport.metrics;
    }

    return [];
}

function findLatestGoldReport(history) {
    for (const item of history) {
        const report = item && item.report;
        if (extractGoldMetrics(report).length) {
            return { report, checkedAt: item.checked_at };
        }
    }
    return { report: null, checkedAt: null };
}

async function loadGoldTable(forceRun) {
    const statusBox = document.getElementById('statusBox');
    const metaBox = document.getElementById('metaBox');

    try {
        statusBox.textContent = forceRun ? 'Running Gold quality check...' : 'Refreshing Gold DB status...';

        let report = null;
        let checkedAt = null;

        if (forceRun) {
            const response = await fetch('/api/run-now', { method: 'POST' });
            const data = await response.json();
            if (!data.success) {
                throw new Error(data.error || 'Could not load the Gold table');
            }
            report = data.run?.report || null;
            checkedAt = data.run?.checked_at || null;
        } else {
            const response = await fetch('/api/dashboard-state');
            const data = await response.json();
            const latestGold = findLatestGoldReport(data.history || []);
            report = latestGold.report;
            checkedAt = latestGold.checkedAt;
        }

        const goldMetrics = extractGoldMetrics(report);

        setMetrics(goldMetrics);
        statusBox.textContent = goldMetrics.length
            ? `Loaded ${goldMetrics.length} Gold table${goldMetrics.length === 1 ? '' : 's'}.`
            : 'No Gold tables found in the latest run.';
        metaBox.textContent = checkedAt ? `Last checked at: ${checkedAt}` : 'No previous Gold run found.';
    } catch (error) {
        statusBox.textContent = `Unable to load Gold table: ${error.message}`;
        metaBox.textContent = 'Please try again.';
        setMetrics([]);
    }
}

function getSidebarCollapsedState() {
    try { return localStorage.getItem('dwh-sidebar-collapsed-v1') === '1'; } catch(e) { return false; }
}
function setSidebarCollapsedState(collapsed) {
    try { localStorage.setItem('dwh-sidebar-collapsed-v1', collapsed ? '1' : '0'); } catch(e) {}
}
function applySidebarState(collapsed) {
    const sidebar = document.querySelector('.sidebar');
    const toggleIcon = document.getElementById('sidebarToggleIcon');
    if (!sidebar) return;
    if (collapsed) {
        sidebar.classList.add('is-collapsed');
        sidebar.style.width = '72px';
        sidebar.style.paddingLeft = '10px';
        sidebar.style.paddingRight = '10px';
        sidebar.style.overflow = 'hidden';
    } else {
        sidebar.classList.remove('is-collapsed');
        sidebar.style.width = '';
        sidebar.style.paddingLeft = '';
        sidebar.style.paddingRight = '';
        sidebar.style.overflow = '';
    }
    if (toggleIcon) toggleIcon.textContent = collapsed ? '\u2630' : '\u276e';
}
function initSidebarToggle() {
    const btn = document.getElementById('sidebarToggleBtn');
    if (!btn) return;
    applySidebarState(getSidebarCollapsedState());
    btn.addEventListener('click', function() {
        const sidebar = document.querySelector('.sidebar');
        const collapsed = sidebar && !sidebar.classList.contains('is-collapsed');
        setSidebarCollapsedState(collapsed);
        applySidebarState(collapsed);
    });
}

// Note: Server renders first page of rows initially, so we don't call renderRows() on load
// renderRows() is only used when dynamically loading data via API
document.addEventListener('DOMContentLoaded', () => {
    initSidebarToggle();
    if (activeView === 'quality') {
        initResizableColumns();
        // Don't re-render rows - server already rendered first page
        // renderRows() is called only after API data loads
    }
});

// SP Analysis functions
function showSpDetail(spName) {
    // Find the record
    const rec = spRecordsJson.find(r => r.sp_name === spName);
    if (!rec) return;

    // Create modal if it doesn't exist
    let modal = document.getElementById('spDetailModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'spDetailModal';
        modal.className = 'sp-modal-overlay';
        modal.innerHTML = `
            <div class="sp-modal">
                <div class="sp-modal-header">
                    <h2 id="spModalTitle"></h2>
                    <button class="sp-modal-close" onclick="closeSpModal()">×</button>
                </div>
                <div class="sp-modal-body" id="spModalBody"></div>
                <div class="sp-modal-footer">
                    <span id="spModalFooter"></span>
                    <button class="secondary button-link" onclick="closeSpModal()">Close</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Close on overlay click
        modal.addEventListener('click', function(e) {
            if (e.target === modal) closeSpModal();
        });
        
        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('open')) closeSpModal();
        });
    }
    
    // Populate content
    document.getElementById('spModalTitle').textContent = rec.sp_name || 'SP Detail';
    
    const definition = rec.definition || 'No definition available.';
    const llmAnalysis = rec.llm_analysis || {};
    
    let bodyHtml = '<div class="sp-modal-section-title">Definition</div>';
    bodyHtml += '<div class="sp-definition-box">' + escapeHtml(definition) + '</div>';
    
    if (llmAnalysis.recommendations && llmAnalysis.recommendations.length) {
        bodyHtml += '<div class="sp-modal-section-title">AI Recommendations</div>';
        bodyHtml += '<ul class="sp-llm-list">';
        llmAnalysis.recommendations.forEach(rec => {
            bodyHtml += '<li>' + escapeHtml(String(rec)) + '</li>';
        });
        bodyHtml += '</ul>';
    }
    
    if (llmAnalysis.issues && llmAnalysis.issues.length) {
        bodyHtml += '<div class="sp-modal-section-title">Issues</div>';
        bodyHtml += '<ul class="sp-llm-list">';
        llmAnalysis.issues.forEach(issue => {
            bodyHtml += '<li>' + escapeHtml(String(issue)) + '</li>';
        });
        bodyHtml += '</ul>';
    }
    
    document.getElementById('spModalBody').innerHTML = bodyHtml;
    document.getElementById('spModalFooter').textContent = 
        `Score: ${rec.quality_score ?? 'N/A'} | Params: ${rec.parameter_count ?? 0}`;
    
    // Show modal
    modal.classList.add('open');
}

function closeSpModal() {
    const modal = document.getElementById('spDetailModal');
    if (modal) modal.classList.remove('open');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Enhanced DOMContentLoaded handler
document.addEventListener('DOMContentLoaded', () => {
    initSidebarToggle();
    
    if (activeView === 'quality') {
        initResizableColumns();
        // Don't re-render - server already rendered first page
    } else if (activeView === 'intel') {
        initIntelFilters();
    }
});

// Initialize Intel view filters
function initIntelFilters() {
    // Filter buttons use inline onclick handlers in HTML
    // This function is called on load to ensure filters are ready
    const filterBtns = document.querySelectorAll('.intel-filter-btn');
    filterBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            // Prevent default if needed
            e.preventDefault();
        });
    });
}

// Intel search and filter functions
function filterIntelCards() {
    const searchInput = document.getElementById('intelSearch');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const grid = document.getElementById('intelGrid');
    const cards = grid ? grid.querySelectorAll('.intel-card') : [];
    
    cards.forEach(card => {
        const tableName = card.querySelector('.intel-table-name');
        const desc = card.querySelector('.intel-desc');
        const nameText = tableName ? tableName.textContent.toLowerCase() : '';
        const descText = desc ? desc.textContent.toLowerCase() : '';
        
        if (nameText.includes(searchTerm) || descText.includes(searchTerm)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
    
    updateIntelCount();
}

function filterIntelByType(type) {
    console.log('filterIntelByType called with type:', type);
    
    // Update active button state
    const buttons = document.querySelectorAll('.intel-filter-btn');
    console.log('Found filter buttons:', buttons.length);
    buttons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.type === type) {
            btn.classList.add('active');
        }
    });
    
    const grid = document.getElementById('intelGrid');
    console.log('Intel grid found:', !!grid);
    const cards = grid ? grid.querySelectorAll('.intel-card') : [];
    console.log('Total cards found:', cards.length);
    
    let visibleCount = 0;
    cards.forEach(card => {
        const cardType = (card.dataset.type || '').toLowerCase();
        console.log('Card type:', cardType);
        
        if (type === 'all') {
            card.style.display = 'flex';
            visibleCount++;
        } else {
            const isFact = cardType === 'fact';
            const isDim = cardType === 'dimension' || cardType === 'dim';
            
            if ((type === 'fact' && isFact) || (type === 'dim' && isDim)) {
                card.style.display = 'flex';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        }
    });
    
    console.log('Visible cards after filter:', visibleCount);
    updateIntelCount();
}

function updateIntelCount() {
    const grid = document.getElementById('intelGrid');
    const visibleCards = grid ? grid.querySelectorAll('.intel-card[style*="flex"], .intel-card:not([style*="none"])') : [];
    const meta = document.getElementById('intelMeta');
    if (meta) {
        meta.textContent = `${visibleCards.length} tables`;
    }
}
