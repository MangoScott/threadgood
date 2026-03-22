const DATA_URL = 'data/site/brands.json';
let allBrands = [];

document.addEventListener('DOMContentLoaded', () => {
    // Only run on directory page
    if (document.getElementById('brands-grid')) {
        initDirectory();
    }
});

async function initDirectory() {
    const grid = document.getElementById('brands-grid');
    const loading = document.getElementById('loading-indicator');
    
    try {
        const response = await fetch(DATA_URL);
        if (!response.ok) throw new Error('Data not found');
        const data = await response.json();
        allBrands = data.brands || data; // Handle both wrapped and raw arrays
        
        loading.style.display = 'none';
        renderBrands(allBrands);
        setupFilters();
    } catch (err) {
        loading.innerHTML = '<p>⚠️ Could not load brand data. Ensure the pipeline has been run.</p>';
        console.error(err);
    }
}

function renderBrands(brands) {
    const grid = document.getElementById('brands-grid');
    const empty = document.getElementById('empty-state');
    
    if (brands.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    
    empty.style.display = 'none';
    
    grid.innerHTML = brands.map(b => `
        <a href="brand.html?slug=${b.slug}" class="brand-card-link fade-up visible">
            <div class="brand-card">
                <div class="bc-header">
                    <div class="bc-badge ${b.grade}">${b.grade}</div>
                    <div class="bc-price">${b.price_tier || ''}</div>
                </div>
                <div class="bc-name">${b.name}</div>
                <div class="bc-cats">${(b.categories || []).join(' • ')}</div>
                <div class="bc-score">
                    Overall Score <span>${b.overall_score !== null ? b.overall_score.toFixed(1) + ' / 100' : 'Unranked'}</span>
                </div>
            </div>
        </a>
    `).join('');
}

function setupFilters() {
    const searchInput = document.getElementById('brand-search');
    const gradeSelect = document.getElementById('filter-grade');
    const priceSelect = document.getElementById('filter-price');
    const sortSelect = document.getElementById('filter-sort');
    const clearBtn = document.getElementById('clear-filters');

    function applyFilters() {
        const search = searchInput.value.toLowerCase();
        const grade = gradeSelect.value;
        const price = priceSelect.value;
        const sort = sortSelect.value;

        let filtered = allBrands.filter(b => {
            const matchesSearch = b.name.toLowerCase().includes(search);
            const matchesGrade = grade === 'all' || b.grade === grade;
            const matchesPrice = price === 'all' || b.price_tier === price;
            return matchesSearch && matchesGrade && matchesPrice;
        });

        if (sort === 'score-desc') {
            filtered.sort((a, b) => (b.overall_score || 0) - (a.overall_score || 0));
        } else if (sort === 'score-asc') {
            filtered.sort((a, b) => (a.overall_score || 0) - (b.overall_score || 0));
        } else if (sort === 'name-asc') {
            filtered.sort((a, b) => a.name.localeCompare(b.name));
        }

        renderBrands(filtered);
    }

    searchInput.addEventListener('input', applyFilters);
    gradeSelect.addEventListener('change', applyFilters);
    priceSelect.addEventListener('change', applyFilters);
    sortSelect.addEventListener('change', applyFilters);

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            gradeSelect.value = 'all';
            priceSelect.value = 'all';
            sortSelect.value = 'default';
            applyFilters();
        });
    }
}
