const fs = require('fs');

async function test(slug) {
    try {
        const jsonString = fs.readFileSync(`data/site/brands/${slug}.json`, 'utf8');
        const brand = JSON.parse(jsonString);
        
        console.log(`Testing ${slug}...`);
        
        // Simulating the script from brand.html
        let out = {};
        
        out.name = brand.name;
        out.price = brand.price_tier || '$$';
        out.cats = (brand.categories || []).join(' • ');
        
        out.grade = brand.grade;
        out.gradeClass = `badge ${brand.grade.toLowerCase()}`;
        out.label = brand.grade_label || 'Overall Score';
        out.scoreValue = brand.overall_score !== null ? brand.overall_score.toFixed(1) + ' / 100' : 'Unranked';
        
        if (brand.report_file) {
            out.report_file = brand.report_file;
            out.href = `https://www.google.com/search?q=${encodeURIComponent(brand.name + ' ' + brand.report_file + ' sustainability report pdf')}`;
        }
        
        if (brand.red_flags && brand.red_flags.length > 0) {
            out.flagsHTML = brand.red_flags.map(f => f.dimension).join('');
        }
        
        if (brand.dimensions) {
            const updateBar = (id, data) => {
                if (!data) return;
                let val = data.score !== null ? `${data.score.toFixed(1)} / 100` : 'Unranked';
                let cls = `progress-bar-fill fill-${data.grade.toLowerCase()}`;
            };
            updateBar('ds-planet', brand.dimensions.planet);
            updateBar('ds-people', brand.dimensions.people);
            updateBar('ds-animals', brand.dimensions.animals);
        }
        
        const highlightsHTML = (brand.highlights || []).map(h => `<li>${h}</li>`).join('');
        const concernsHTML = (brand.concerns || []).map(c => `<li>${c}</li>`).join('');
        const sourcesStr = (brand.data_sources || []).map(s => `<li><code>${s}</code></li>`).join('');
        
    } catch(e) {
        console.error("FAIL", e);
    }
}

test('patagonia');
test('zara');
