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

function getCellDisplayText(cell) {
    if (!cell) {
        return '';
    }

    const titledElement = cell.querySelector('[title]');
    if (titledElement) {
        return titledElement.getAttribute('title').trim();
    }

    const formField = cell.querySelector('input, textarea, select');
    if (formField) {
        if (formField.type === 'checkbox') {
            return formField.checked ? 'true' : 'false';
        }
        return (formField.value || '').trim();
    }

    return (cell.innerText || '').trim();
}

function cellHasValue(cell) {
    if (!cell) {
        return false;
    }

    const formField = cell.querySelector('input, textarea, select');
    if (formField) {
        if (formField.type === 'checkbox') {
            return formField.checked;
        }
        return Boolean((formField.value || '').trim());
    }

    if (cell.querySelector('img, a')) {
        return true;
    }

    const text = (cell.innerText || '').trim().toLowerCase();
    if (!text || text === 'no image' || text === 'kein bild') {
        return false;
    }

    return true;
}

function getDateComparableValue(cell) {
    const value = getCellDisplayText(cell);
    if (!value) {
        return '';
    }

    const isoDateMatch = value.match(/^\d{4}-\d{2}-\d{2}$/);
    if (isoDateMatch) {
        return isoDateMatch[0];
    }

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) {
        return '';
    }

    return parsed.toISOString().slice(0, 10);
}

function getFilterConfig(label) {
    if (label.includes('actions')) {
        return { type: 'none' };
    }

    if (label.includes('category')) {
        return { type: 'category' };
    }

    if (label.includes('date')) {
        return { type: 'date' };
    }

    if (label.includes('url') || label.includes('image')) {
        return { type: 'presence' };
    }

    return { type: 'text' };
}

function normalizeLegacyFilters() {
    const normalized = {};

    Object.entries(activeFilters).forEach(([columnIndex, filterState]) => {
        if (typeof filterState === 'string') {
            normalized[columnIndex] = { type: 'text', value: filterState };
            return;
        }

        if (filterState && typeof filterState === 'object' && typeof filterState.value === 'string') {
            normalized[columnIndex] = filterState;
            return;
        }

        if (
            filterState &&
            typeof filterState === 'object' &&
            filterState.type === 'date' &&
            filterState.value &&
            typeof filterState.value === 'object'
        ) {
            const fromValue = typeof filterState.value.from === 'string' ? filterState.value.from : '';
            const toValue = typeof filterState.value.to === 'string' ? filterState.value.to : '';

            if (fromValue || toValue) {
                normalized[columnIndex] = {
                    type: 'date',
                    value: {
                        from: fromValue,
                        to: toValue
                    }
                };
            }
        }
    });

    activeFilters = normalized;
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

function rowMatchesFilter(cell, filterState) {
    if (!filterState || !filterState.value) {
        return true;
    }

    if (filterState.type === 'category') {
        const selectedCategory = String(filterState.value).trim().toLowerCase();
        const cellCategory = getCellDisplayText(cell).trim().toLowerCase();
        return cellCategory === selectedCategory;
    }

    if (filterState.type === 'date') {
        const filterValue = filterState.value;
        const cellDate = getDateComparableValue(cell);
        if (!cellDate) {
            return false;
        }

        if (typeof filterValue === 'string') {
            return cellDate === filterValue;
        }

        const fromValue = filterValue && typeof filterValue.from === 'string' ? filterValue.from : '';
        const toValue = filterValue && typeof filterValue.to === 'string' ? filterValue.to : '';

        if (fromValue && cellDate < fromValue) {
            return false;
        }
        if (toValue && cellDate > toValue) {
            return false;
        }

        return Boolean(fromValue || toValue);
    }

    if (filterState.type === 'presence') {
        const hasValue = cellHasValue(cell);
        return filterState.value === 'present' ? hasValue : !hasValue;
    }

    const cellText = getCellText(cell);
    return cellText.includes(filterState.value.toLowerCase());
}

function applyFilters() {
    const table = getTable();
    if (!table) {
        return;
    }

    const rows = Array.from(table.tBodies[0].rows);

    rows.forEach((row) => {
        let isVisible = true;

        Object.entries(activeFilters).forEach(([columnIndex, filterState]) => {
            if (!isVisible || !filterState || !filterState.value) {
                return;
            }

            if (filterState.type === 'date' && typeof filterState.value === 'object') {
                const hasRangeValue = Boolean(filterState.value.from || filterState.value.to);
                if (!hasRangeValue) {
                    return;
                }
            }

            const cell = row.cells[Number(columnIndex)];
            if (!rowMatchesFilter(cell, filterState)) {
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

function createCategoryFilter(columnIndex) {
    const table = getTable();
    const select = document.createElement('select');
    const categoriesByKey = new Map();
    const rows = Array.from(table.tBodies[0].rows);

    rows.forEach((row) => {
        const category = getCellDisplayText(row.cells[columnIndex]).trim();
        if (!category) {
            return;
        }

        const key = category.toLowerCase();
        if (!categoriesByKey.has(key)) {
            categoriesByKey.set(key, category);
        }
    });

    select.appendChild(new Option('Alle', ''));
    Array.from(categoriesByKey.values())
        .sort((a, b) => a.localeCompare(b))
        .forEach((category) => {
            select.appendChild(new Option(category, category));
        });

    const savedFilter = activeFilters[columnIndex];
    if (savedFilter && typeof savedFilter.value === 'string') {
        const savedValue = savedFilter.value.trim().toLowerCase();
        const matchingCategory = categoriesByKey.get(savedValue);
        select.value = matchingCategory || '';
    }

    select.addEventListener('change', (event) => {
        const value = event.target.value;
        if (value) {
            activeFilters[columnIndex] = { type: 'category', value };
        } else {
            delete activeFilters[columnIndex];
        }
        applyFilters();
        persistTableState();
    });

    return select;
}

function createDateFilter(columnIndex) {
    const wrapper = document.createElement('div');
    wrapper.className = 'date-range-filter';
    const fromInput = document.createElement('input');
    fromInput.type = 'date';
    fromInput.title = 'Von';
    const toInput = document.createElement('input');
    toInput.type = 'date';
    toInput.title = 'Bis';

    fromInput.placeholder = 'Von';
    toInput.placeholder = 'Bis';

    wrapper.appendChild(fromInput);
    wrapper.appendChild(toInput);

    const savedFilter = activeFilters[columnIndex];
    if (savedFilter && savedFilter.type === 'date') {
        if (typeof savedFilter.value === 'string') {
            fromInput.value = savedFilter.value;
            toInput.value = savedFilter.value;
        } else {
            fromInput.value = savedFilter.value && savedFilter.value.from ? savedFilter.value.from : '';
            toInput.value = savedFilter.value && savedFilter.value.to ? savedFilter.value.to : '';
        }
    }

    const updateRangeFilter = () => {
        const fromValue = fromInput.value;
        const toValue = toInput.value;

        if (fromValue || toValue) {
            activeFilters[columnIndex] = {
                type: 'date',
                value: {
                    from: fromValue,
                    to: toValue
                }
            };
        } else {
            delete activeFilters[columnIndex];
        }

        applyFilters();
        persistTableState();
    };

    fromInput.addEventListener('change', updateRangeFilter);
    toInput.addEventListener('change', updateRangeFilter);

    return wrapper;
}

function createPresenceFilter(columnIndex) {
    const select = document.createElement('select');
    select.appendChild(new Option('Alle', ''));
    select.appendChild(new Option('Vorhanden', 'present'));
    select.appendChild(new Option('Nicht vorhanden', 'missing'));

    const savedFilter = activeFilters[columnIndex];
    select.value = savedFilter ? savedFilter.value : '';

    select.addEventListener('change', (event) => {
        const value = event.target.value;
        if (value) {
            activeFilters[columnIndex] = { type: 'presence', value };
        } else {
            delete activeFilters[columnIndex];
        }
        applyFilters();
        persistTableState();
    });

    return select;
}

function createTextFilter(columnIndex) {
    const input = document.createElement('input');
    input.type = 'text';
    input.placeholder = 'Filter...';

    const savedFilter = activeFilters[columnIndex];
    input.value = savedFilter ? savedFilter.value : '';

    input.addEventListener('input', (event) => {
        const value = event.target.value.trim().toLowerCase();
        if (value) {
            activeFilters[columnIndex] = { type: 'text', value };
        } else {
            delete activeFilters[columnIndex];
        }
        applyFilters();
        persistTableState();
    });

    return input;
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
        const config = getFilterConfig(label);

        if (config.type === 'none') {
            filterCell.textContent = '—';
        } else if (config.type === 'category') {
            filterCell.appendChild(createCategoryFilter(columnIndex));
        } else if (config.type === 'date') {
            filterCell.appendChild(createDateFilter(columnIndex));
        } else if (config.type === 'presence') {
            filterCell.appendChild(createPresenceFilter(columnIndex));
        } else {
            filterCell.appendChild(createTextFilter(columnIndex));
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
            normalizeLegacyFilters();
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
