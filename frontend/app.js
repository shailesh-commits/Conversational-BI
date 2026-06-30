/**
 * Conversational BI Assistant - Frontend JavaScript
 */

const API_BASE_URL = 'http://localhost:5000';
let sessionCost = 0;
let queryHistory = [];

// DOM Elements
const userInput = document.getElementById('user-input');
const submitBtn = document.getElementById('submit-btn');
const resultsContainer = document.getElementById('results-container');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');
const sampleQueriesList = document.getElementById('sample-queries-list');
const cacheCheckbox = document.getElementById('cache-checkbox');
const sessionCostDisplay = document.getElementById('session-cost');
const queryCostDisplay = document.getElementById('query-cost');
const loadingIndicator = document.getElementById('loading-indicator');
const historyTitle = document.getElementById('history-toggle');
const historyContent = document.getElementById('history-content');
const historyList = document.getElementById('history-list');
const schemaModal = document.getElementById('schema-modal');
const viewSchemaBtn = document.getElementById('view-schema-btn');
const clearCacheBtn = document.getElementById('clear-cache-btn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await checkBackendStatus();
    await loadSampleQueries();
    setupEventListeners();
    setupHistoryToggle();
});

async function checkBackendStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        if (data.success) {
            statusIndicator.classList.add('status-connected');
            statusText.textContent = `Connected (${data.data.sales_records.toLocaleString()} records)`;
        } else {
            setStatusError('Database connection failed');
        }
    } catch (error) {
        setStatusError('Backend unavailable');
        console.error('Status check error:', error);
    }
}

function setStatusError(message) {
    statusIndicator.classList.add('status-error');
    statusText.textContent = message;
}

async function loadSampleQueries() {
    try {
        const response = await fetch(`${API_BASE_URL}/sample-queries`);
        const data = await response.json();
        
        if (data.success) {
            sampleQueriesList.innerHTML = '';
            data.data.queries.forEach(query => {
                const li = document.createElement('li');
                li.textContent = query;
                li.addEventListener('click', () => {
                    userInput.value = query;
                    userInput.focus();
                });
                sampleQueriesList.appendChild(li);
            });
        }
    } catch (error) {
        console.error('Error loading sample queries:', error);
    }
}

function setupEventListeners() {
    submitBtn.addEventListener('click', submitQuery);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') submitQuery();
    });
    
    viewSchemaBtn.addEventListener('click', showSchema);
    clearCacheBtn.addEventListener('click', clearCache);
    
    // Close modal when clicking X
    document.querySelectorAll('.close').forEach(closeBtn => {
        closeBtn.addEventListener('click', () => {
            schemaModal.style.display = 'none';
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === schemaModal) {
            schemaModal.style.display = 'none';
        }
    });
}

function setupHistoryToggle() {
    historyTitle.addEventListener('click', () => {
        historyContent.style.display = 
            historyContent.style.display === 'none' ? 'block' : 'none';
    });
}

async function submitQuery() {
    const question = userInput.value.trim();
    if (!question) return;
    
    loadingIndicator.style.display = 'flex';
    submitBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                use_cache: cacheCheckbox.checked
            })
        });
        
        const data = await response.json();
        
        if (!data.success) {
            showError(data.error || 'Query failed');
            return;
        }
        
        // Process results
        const result = data.data;
        displayResults(result);
        
        // Update costs
        const cost = result.costs.total;
        queryCostDisplay.textContent = `$${cost.toFixed(5)}`;
        sessionCost += cost;
        sessionCostDisplay.textContent = `$${sessionCost.toFixed(5)}`;
        
        // Add to history
        addToHistory({
            question: question,
            timestamp: new Date(),
            cost: cost,
            fromCache: result.from_cache
        });
        
        // Clear input
        userInput.value = '';
        
    } catch (error) {
        showError(`Error: ${error.message}`);
        console.error('Query error:', error);
    } finally {
        loadingIndicator.style.display = 'none';
        submitBtn.disabled = false;
    }
}

function displayResults(result) {
    resultsContainer.innerHTML = '';
    
    // Create result card
    const card = document.createElement('div');
    card.className = 'result-card';
    
    // Header with metadata
    const header = document.createElement('div');
    header.className = 'result-header';
    
    const title = document.createElement('h3');
    title.className = 'result-title';
    title.textContent = '🔍 Query Result';
    
    const metadata = document.createElement('div');
    metadata.className = 'result-metadata';
    
    const info = [
        `<strong>Confidence:</strong> ${result.sql_confidence}%`,
        `<strong>Rows:</strong> ${result.execution.row_count}`,
        `<strong>Cost:</strong> $${result.costs.total.toFixed(5)}`,
        `<strong>Tokens:</strong> ${(result.tokens.sql_generation + result.tokens.narrative).toLocaleString()}`,
    ];
    
    if (result.from_cache) {
        info.push(`<strong style="color: #4CAF50;">✓ From Cache</strong>`);
    }
    
    metadata.innerHTML = info.join(' | ');
    
    header.appendChild(title);
    header.appendChild(metadata);
    card.appendChild(header);
    
    // SQL Query (collapsible)
    const sqlSection = document.createElement('div');
    sqlSection.className = 'result-section';
    
    const sqlToggle = document.createElement('h4');
    sqlToggle.className = 'section-toggle';
    sqlToggle.textContent = '▼ Generated SQL';
    sqlToggle.style.cursor = 'pointer';
    
    const sqlCode = document.createElement('pre');
    sqlCode.className = 'sql-code';
    sqlCode.textContent = result.sql;
    
    sqlToggle.addEventListener('click', () => {
        sqlCode.style.display = sqlCode.style.display === 'none' ? 'block' : 'none';
        sqlToggle.textContent = sqlToggle.textContent.includes('▼') ? '▶ Generated SQL' : '▼ Generated SQL';
    });
    
    sqlSection.appendChild(sqlToggle);
    sqlSection.appendChild(sqlCode);
    card.appendChild(sqlSection);
    
    // Chart
    if (result.chart && result.chart.html) {
        const chartSection = document.createElement('div');
        chartSection.className = 'result-section';
        
        const chartTitle = document.createElement('h4');
        chartTitle.textContent = `📊 ${result.chart.description}`;
        
        const chartContainer = document.createElement('div');
        chartContainer.innerHTML = result.chart.html;

        // Execute any scripts embedded in the Plotly HTML.
        chartContainer.querySelectorAll('script').forEach(oldScript => {
            const newScript = document.createElement('script');
            if (oldScript.src) {
                newScript.src = oldScript.src;
                newScript.async = false;
            } else {
                newScript.textContent = oldScript.textContent;
            }
            oldScript.parentNode.replaceChild(newScript, oldScript);
        });
        
        chartSection.appendChild(chartTitle);
        chartSection.appendChild(chartContainer);
        card.appendChild(chartSection);
    }
    
    // Narrative
    const narrativeSection = document.createElement('div');
    narrativeSection.className = 'result-section narrative-section';
    
    const narrativeTitle = document.createElement('h4');
    narrativeTitle.textContent = '💬 Executive Summary';
    
    const narrativeText = document.createElement('p');
    narrativeText.className = 'narrative-text';
    narrativeText.textContent = result.narrative;
    
    narrativeSection.appendChild(narrativeTitle);
    narrativeSection.appendChild(narrativeText);
    card.appendChild(narrativeSection);
    
    // Data Table (if small result set)
    if (result.execution.row_count <= 20) {
        const tableSection = document.createElement('div');
        tableSection.className = 'result-section';
        
        const tableToggle = document.createElement('h4');
        tableToggle.className = 'section-toggle';
        tableToggle.textContent = '▶ Raw Data';
        tableToggle.style.cursor = 'pointer';
        
        const table = createDataTable(result.execution.columns, result.execution.rows);
        table.style.display = 'none';
        
        tableToggle.addEventListener('click', () => {
            table.style.display = table.style.display === 'none' ? 'table' : 'none';
            tableToggle.textContent = tableToggle.textContent.includes('▼') ? '▶ Raw Data' : '▼ Raw Data';
        });
        
        tableSection.appendChild(tableToggle);
        tableSection.appendChild(table);
        card.appendChild(tableSection);
    }
    
    resultsContainer.appendChild(card);
}

function createDataTable(columns, rows) {
    const table = document.createElement('table');
    table.className = 'data-table';
    
    // Header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Body
    const tbody = document.createElement('tbody');
    rows.forEach((row, idx) => {
        const tr = document.createElement('tr');
        if (idx % 2 === 0) tr.style.backgroundColor = '#f5f5f5';
        
        row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell !== null ? cell : '(null)';
            tr.appendChild(td);
        });
        tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    
    return table;
}

function showError(message) {
    resultsContainer.innerHTML = '';
    const errorCard = document.createElement('div');
    errorCard.className = 'error-card';
    errorCard.innerHTML = `
        <h3>⚠️ Error</h3>
        <p>${message}</p>
        <p class="hint">Check your question or try a sample query from the sidebar.</p>
    `;
    resultsContainer.appendChild(errorCard);
}

async function showSchema() {
    try {
        const response = await fetch(`${API_BASE_URL}/schema`);
        const data = await response.json();
        
        if (!data.success) {
            alert('Failed to load schema');
            return;
        }
        
        const schemaDisplay = document.getElementById('schema-display');
        schemaDisplay.innerHTML = '';
        
        Object.entries(data.data.schema).forEach(([tableName, info]) => {
            const tableDiv = document.createElement('div');
            tableDiv.className = 'schema-table';
            
            const tableTitle = document.createElement('h4');
            tableTitle.textContent = tableName;
            
            const columnsList = document.createElement('ul');
            info.columns.forEach((col, idx) => {
                const li = document.createElement('li');
                li.textContent = `${col} (${info.types[idx]})`;
                columnsList.appendChild(li);
            });
            
            tableDiv.appendChild(tableTitle);
            tableDiv.appendChild(columnsList);
            schemaDisplay.appendChild(tableDiv);
        });
        
        schemaModal.style.display = 'block';
        
    } catch (error) {
        console.error('Error loading schema:', error);
        alert('Failed to load schema');
    }
}

async function clearCache() {
    try {
        await fetch(`${API_BASE_URL}/cache/clear`, { method: 'POST' });
        alert('✓ Cache cleared');
    } catch (error) {
        console.error('Error clearing cache:', error);
    }
}

function addToHistory(entry) {
    queryHistory.push(entry);
    
    // Update history title
    historyTitle.textContent = `📜 Query History (${queryHistory.length})`;
    
    // Add to history list
    const item = document.createElement('div');
    item.className = 'history-item';
    
    const question = document.createElement('div');
    question.className = 'history-question';
    question.textContent = entry.question;
    question.addEventListener('click', () => {
        userInput.value = entry.question;
        userInput.focus();
    });
    
    const details = document.createElement('div');
    details.className = 'history-details';
    details.innerHTML = `
        ${entry.fromCache ? '⚡ ' : ''}
        ${entry.timestamp.toLocaleTimeString()} | 
        $${entry.cost.toFixed(5)}
    `;
    
    item.appendChild(question);
    item.appendChild(details);
    historyList.insertBefore(item, historyList.firstChild);
    
    // Limit history display to 20 items
    while (historyList.children.length > 20) {
        historyList.removeChild(historyList.lastChild);
    }
}
