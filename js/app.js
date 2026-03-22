const DATA_URL = 'data/site/brands.json';
let allBrands = [];
let siteMetadata = {};

document.addEventListener('DOMContentLoaded', () => {
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
        allBrands = data.brands || data;
        siteMetadata = data.metadata || {};

        loading.style.display = 'none';
        renderStats(allBrands, siteMetadata);
        renderBrands(allBrands);
        setupFilters();
        setupCompareMode();
    } catch (err) {
        loading.innerHTML = '<p>Could not load brand data. Ensure the pipeline has been run.</p>';
        console.error(err);
    }
}

function renderStats(brands, meta) {
    const statsEl = document.getElementById('stats-dashboard');
    if (!statsEl) return;

    const dist = meta.grade_distribution || {};
    const total = brands.length;
    const avgScore = brands.reduce((sum, b) => sum + (b.overall_score || 0), 0) / total;
    const topBrand = brands.reduce((best, b) => (b.overall_score || 0) > (best.overall_score || 0) ? b : best, brands[0]);
    const withRedFlags = brands.filter(b => b.red_flags && b.red_flags.length > 0).length;

    const gradeColors = { A: 'var(--grade-a)', B: 'var(--grade-b)', C: 'var(--grade-c)', D: 'var(--grade-d)', F: 'var(--grade-f)' };

    let gradeBarHTML = '';
    for (const g of ['A', 'B', 'C', 'D', 'F']) {
        const count = dist[g] || 0;
        const pct = total > 0 ? (count / total * 100) : 0;
        if (pct > 0) {
            gradeBarHTML += `<div class="grade-bar-seg" style="width:${pct}%;background:${gradeColors[g]}" title="${g}: ${count} brands (${pct.toFixed(0)}%)"><span>${g}</span></div>`;
        }
    }

    statsEl.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">${total}</div>
                <div class="stat-label">Brands Rated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">${avgScore.toFixed(1)}</div>
                <div class="stat-label">Average Score</div>
            </div>
            <div class="stat-card">
                <div class="stat-number"><a href="brand.html?slug=${topBrand.slug}" style="color:inherit;text-decoration:none">${topBrand.name}</a></div>
                <div class="stat-label">Top Rated (${topBrand.overall_score?.toFixed(1)}/100)</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color:var(--grade-f)">${withRedFlags}</div>
                <div class="stat-label">Red Flag Brands</div>
            </div>
        </div>
        <div class="grade-distribution-bar">${gradeBarHTML}</div>
        <div class="grade-distribution-legend">
            ${['A','B','C','D','F'].map(g => `<span><span class="legend-dot" style="background:${gradeColors[g]}"></span>${g}: ${dist[g]||0}</span>`).join('')}
        </div>
    `;
    statsEl.style.display = 'block';
}

function getGradeClass(grade) {
    return (grade || 'F').toLowerCase();
}

function renderBrands(brands) {
    const grid = document.getElementById('brands-grid');
    const empty = document.getElementById('empty-state');
    const countEl = document.getElementById('results-count');

    if (countEl) {
        countEl.textContent = `${brands.length} brand${brands.length !== 1 ? 's' : ''}`;
    }

    if (brands.length === 0) {
        grid.innerHTML = '';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';

    grid.innerHTML = brands.map(b => {
        const dims = b.dimensions || {};
        const planet = dims.planet || {};
        const people = dims.people || {};
        const animals = dims.animals || {};
        const hasRedFlags = b.red_flags && b.red_flags.length > 0;

        return `
        <a href="brand.html?slug=${b.slug}" class="brand-card-link">
            <div class="brand-card ${hasRedFlags ? 'has-red-flag' : ''}">
                <div class="bc-header">
                    <div class="bc-badge ${b.grade}">${b.grade}</div>
                    <div class="bc-price">${b.price_tier || ''}</div>
                </div>
                <div class="bc-name">${b.name}</div>
                <div class="bc-cats">${(b.categories || []).join(' \u2022 ')}</div>
                <div class="bc-pillars">
                    <div class="bc-pillar">
                        <span class="bc-pillar-label">Planet</span>
                        <div class="bc-pillar-bar"><div class="bc-pillar-fill fill-${getGradeClass(planet.grade)}" style="width:${planet.score || 0}%"></div></div>
                    </div>
                    <div class="bc-pillar">
                        <span class="bc-pillar-label">People</span>
                        <div class="bc-pillar-bar"><div class="bc-pillar-fill fill-${getGradeClass(people.grade)}" style="width:${people.score || 0}%"></div></div>
                    </div>
                    <div class="bc-pillar">
                        <span class="bc-pillar-label">Animals</span>
                        <div class="bc-pillar-bar"><div class="bc-pillar-fill fill-${getGradeClass(animals.grade)}" style="width:${animals.score || 0}%"></div></div>
                    </div>
                </div>
                ${hasRedFlags ? '<div class="bc-flag-indicator">Forced labor concern</div>' : ''}
                <div class="bc-score">
                    Overall Score <span>${b.overall_score !== null ? b.overall_score.toFixed(1) + ' / 100' : 'Unranked'}</span>
                </div>
                <label class="bc-compare" onclick="event.preventDefault(); event.stopPropagation(); toggleCompare('${b.slug}', '${b.name}')">
                    <input type="checkbox" id="cmp-${b.slug}" class="compare-cb"> Compare
                </label>
            </div>
        </a>`;
    }).join('');
}

// --- Compare mode ---
let compareList = [];

function toggleCompare(slug, name) {
    const idx = compareList.findIndex(c => c.slug === slug);
    if (idx >= 0) {
        compareList.splice(idx, 1);
    } else if (compareList.length < 3) {
        compareList.push({ slug, name });
    } else {
        return; // max 3
    }

    const cb = document.getElementById(`cmp-${slug}`);
    if (cb) cb.checked = compareList.some(c => c.slug === slug);

    updateCompareBar();
}

function updateCompareBar() {
    const bar = document.getElementById('compare-bar');
    if (!bar) return;

    if (compareList.length === 0) {
        bar.style.display = 'none';
        return;
    }

    bar.style.display = 'flex';
    const names = compareList.map(c => c.name).join(', ');
    const slugs = compareList.map(c => c.slug).join(',');
    bar.innerHTML = `
        <span>Comparing: <strong>${names}</strong> (${compareList.length}/3)</span>
        <div>
            <a href="compare.html?brands=${slugs}" class="btn-compare-go" ${compareList.length < 2 ? 'style="opacity:0.5;pointer-events:none"' : ''}>Compare Now</a>
            <button onclick="clearCompare()" class="btn-compare-clear">Clear</button>
        </div>
    `;
}

function clearCompare() {
    compareList = [];
    document.querySelectorAll('.compare-cb').forEach(cb => cb.checked = false);
    updateCompareBar();
}

function setupCompareMode() {
    // Compare bar is in the HTML
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
