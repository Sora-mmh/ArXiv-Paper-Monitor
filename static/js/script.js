let currentCategory = 'all';
let papers = [];
let categories = new Set();

async function loadPapers() {
    try {
        const response = await fetch('/api/papers');
        const data = await response.json();
        papers = data;
        
        // Extract unique categories
        categories.clear();
        papers.forEach(paper => {
            paper.categories.forEach(cat => categories.add(cat));
        });
        
        updateCategoryChips();
        displayPapers();
        updateStatus();
    } catch (error) {
        console.error('Error loading papers:', error);
        document.getElementById('papersContainer').innerHTML = 
            '<div class="error">Error loading papers: ' + error.message + '</div>';
    }
}

function updateCategoryChips() {
    const container = document.getElementById('categoryChips');
    let html = '<div class="chip active" onclick="filterByCategory(\'all\')">All</div>';
    
    Array.from(categories).sort().forEach(cat => {
        html += `<div class="chip" onclick="filterByCategory('${cat}')">${cat}</div>`;
    });
    
    container.innerHTML = html;
}

function filterByCategory(category) {
    currentCategory = category;
    
    // Update active chip
    document.querySelectorAll('.chip').forEach(chip => {
        chip.classList.remove('active');
        if (chip.textContent === category || (category === 'all' && chip.textContent === 'All')) {
            chip.classList.add('active');
        }
    });
    
    displayPapers();
}

function displayPapers() {
    const container = document.getElementById('papersContainer');
    
    let filteredPapers = papers;
    if (currentCategory !== 'all') {
        filteredPapers = papers.filter(p => p.categories.includes(currentCategory));
    }
    
    if (filteredPapers.length === 0) {
        container.innerHTML = '<div class="no-papers">No papers found in this category</div>';
        return;
    }
    
    container.innerHTML = filteredPapers.map(paper => `
        <div class="paper-card ${paper.is_new ? 'new' : ''}">
            <h3 class="paper-title">${paper.title}</h3>
            <div class="paper-authors">${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' et al.' : ''}</div>
            
            <div class="paper-abstract" id="abstract-${paper.id}">
                ${paper.abstract}
            </div>
            <div class="expand-btn" onclick="toggleAbstract('${paper.id}')">Show more ▼</div>
            
            <div class="paper-meta">
                <span class="meta-item">📅 ${new Date(paper.published).toLocaleDateString()}</span>
                <span class="meta-item">🔄 ${new Date(paper.updated).toLocaleDateString()}</span>
                ${paper.categories.slice(0, 3).map(cat => 
                    `<span class="meta-item">#${cat}</span>`
                ).join('')}
            </div>
            
            <div class="paper-links">
                <a href="${paper.arxiv_url}" target="_blank" class="arxiv-link">📄 ArXiv</a>
                <a href="${paper.pdf_url}" target="_blank" class="pdf-link">📑 PDF</a>
            </div>
        </div>
    `).join('');
}

function toggleAbstract(paperId) {
    const abstract = document.getElementById(`abstract-${paperId}`);
    abstract.classList.toggle('expanded');
    const btn = abstract.nextElementSibling;
    btn.textContent = abstract.classList.contains('expanded') ? 'Show less ▲' : 'Show more ▼';
}

async function fetchNow() {
    try {
        const btn = event.target;
        btn.disabled = true;
        btn.textContent = '⏳ Fetching...';
        
        const response = await fetch('/api/fetch', { method: 'POST' });
        const data = await response.json();
        
        btn.disabled = false;
        btn.textContent = '🔄 Fetch Now';
        
        loadPapers();
    } catch (error) {
        console.error('Error fetching papers:', error);
        alert('Error fetching papers: ' + error.message);
    }
}

async function markAllSeen() {
    try {
        const response = await fetch('/api/mark-all-seen', { method: 'POST' });
        const data = await response.json();
        
        loadPapers();
    } catch (error) {
        console.error('Error marking papers as seen:', error);
    }
}

async function toggleAutoFetch() {
    try {
        const response = await fetch('/api/toggle-auto-fetch', { method: 'POST' });
        const data = await response.json();
        
        const btn = document.getElementById('autoFetchBtn');
        btn.textContent = data.enabled ? '⏸ Pause Auto-Fetch' : '▶ Resume Auto-Fetch';
    } catch (error) {
        console.error('Error toggling auto-fetch:', error);
    }
}

async function clearData() {
    if (confirm('Are you sure you want to clear all data? This cannot be undone.')) {
        try {
            const response = await fetch('/api/clear', { method: 'POST' });
            const data = await response.json();
            
            loadPapers();
        } catch (error) {
            console.error('Error clearing data:', error);
        }
    }
}

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        
        document.getElementById('fetchStatus').textContent = status.status || 'Ready';
        document.getElementById('lastFetch').textContent = 
            status.last_fetch ? new Date(status.last_fetch).toLocaleString() : 'Never';
        document.getElementById('paperCount').textContent = papers.length;
        document.getElementById('newCount').textContent = papers.filter(p => p.is_new).length;
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Load papers on page load
loadPapers();

// Refresh every 30 seconds
setInterval(() => {
    loadPapers();
}, 30000);