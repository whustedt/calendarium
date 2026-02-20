const TABLE_ID = 'sortableTable';
let activeSortColumn = null;
let activeSortDirection = 'asc';
let activeFilters = {};

function getTable() {
    return document.getElementById(TABLE_ID);
}

function getStorageKey() {
    return `admin-table-state:${window.location.pathname}`;
}

function getCellText(cell) {
    if (!cell) {
        return '';
    }

    const formField = cell.querySelector('input, textarea, select');
    if (formField) {
        if (formField.type === 'checkbox') {
            return formField.checked ? 'true' : 'false';
        }
        return (formField.value || '').trim().toLowerCase();
    }

    return (cell.innerText || '').trim().toLowerCase();
}

function persistTableState() {
    const state = {
        sortColumn: activeSortColumn,
        sortDirection: activeSortDirection,
        filters: activeFilters
    };
    localStorage.setItem(getStorageKey(), JSON.stringify(state));
}

function applySortIndicators() {
    const table = getTable();
    if (!table) {
        return;
    }

    const headers = table.querySelectorAll('thead tr:first-child th');
    headers.forEach((header, index) => {
        const baseLabel = header.dataset.baseLabel || header.textContent.replace(' ▲', '').replace(' ▼', '');
        header.dataset.baseLabel = baseLabel;

        if (index === activeSortColumn) {
            header.textContent = `${baseLabel} ${activeSortDirection === 'asc' ? '▲' : '▼'}`;
        } else {
            header.textContent = baseLabel;
        }
    });
}

function applyFilters() {
    const table = getTable();
    if (!table) {
        return;
    }

    const rows = Array.from(table.tBodies[0].rows);

    rows.forEach((row) => {
        let isVisible = true;

        Object.entries(activeFilters).forEach(([columnIndex, filterValue]) => {
            if (!filterValue || !isVisible) {
                return;
            }

            const cell = row.cells[Number(columnIndex)];
            const cellText = getCellText(cell);
            if (!cellText.includes(filterValue)) {
                isVisible = false;
            }
        });

        row.style.display = isVisible ? '' : 'none';
    });
}

function sortRows(column, direction) {
    const table = getTable();
    if (!table) {
        return;
    }

    const tbody = table.tBodies[0];
    const rows = Array.from(tbody.rows);

    rows.sort((rowA, rowB) => {
        const textA = getCellText(rowA.cells[column]);
        const textB = getCellText(rowB.cells[column]);

        if (textA < textB) {
            return direction === 'asc' ? -1 : 1;
        }

        if (textA > textB) {
            return direction === 'asc' ? 1 : -1;
        }

        return 0;
    });

    rows.forEach((row) => tbody.appendChild(row));
}

function applyState() {
    if (activeSortColumn !== null) {
        sortRows(activeSortColumn, activeSortDirection);
    }

    applySortIndicators();
    applyFilters();
    persistTableState();
}

function initializeFilterRow() {
    const table = getTable();
    if (!table || !table.tHead || table.tHead.rows.length === 0) {
        return;
    }

    if (table.querySelector('thead tr.table-filters')) {
        return;
    }

    const headerRow = table.tHead.rows[0];
    const filterRow = document.createElement('tr');
    filterRow.className = 'table-filters';

    Array.from(headerRow.cells).forEach((headerCell, columnIndex) => {
        const filterCell = document.createElement('th');
        const label = headerCell.textContent.trim().toLowerCase();

        if (label.includes('actions')) {
            filterCell.textContent = '—';
        } else {
            const input = document.createElement('input');
            input.type = 'text';
            input.placeholder = 'Filter...';
            input.value = activeFilters[columnIndex] || '';
            input.addEventListener('input', (event) => {
                const value = event.target.value.trim().toLowerCase();
                if (value) {
                    activeFilters[columnIndex] = value;
                } else {
                    delete activeFilters[columnIndex];
                }
                applyFilters();
                persistTableState();
            });
            filterCell.appendChild(input);
        }

        filterRow.appendChild(filterCell);
    });

    table.tHead.appendChild(filterRow);
}

function loadTableState() {
    const rawState = localStorage.getItem(getStorageKey());
    if (!rawState) {
        return;
    }

    try {
        const state = JSON.parse(rawState);
        if (Number.isInteger(state.sortColumn)) {
            activeSortColumn = state.sortColumn;
        }
        if (state.sortDirection === 'asc' || state.sortDirection === 'desc') {
            activeSortDirection = state.sortDirection;
        }
        if (state.filters && typeof state.filters === 'object') {
            activeFilters = state.filters;
        }
    } catch (error) {
        localStorage.removeItem(getStorageKey());
    }
}

function sortTable(column) {
    if (activeSortColumn === column) {
        activeSortDirection = activeSortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        activeSortColumn = column;
        activeSortDirection = 'asc';
    }

    applyState();
}

window.addEventListener('DOMContentLoaded', () => {
    const table = getTable();
    if (!table || !table.tBodies.length) {
        return;
    }

    loadTableState();
    initializeFilterRow();
    applyState();
});
