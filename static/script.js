document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const themeToggle = document.querySelector('[data-theme-toggle]');

    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        const applyTheme = (theme) => {
            body.dataset.theme = theme;
            if (icon) {
                icon.className = theme === 'light' ? 'far fa-sun' : 'far fa-moon';
                icon.style.color = theme === 'light' ? '#f59e0b' : '#cbd5e1';
            }
            localStorage.setItem('theme', theme);
        };

        // Force light as the default — clear any old 'dark' default
        const savedTheme = localStorage.getItem('theme') === 'dark' ? 'dark' : 'light';
        applyTheme(savedTheme);

        themeToggle.addEventListener('click', () => {
            const currentTheme = body.dataset.theme === 'light' ? 'dark' : 'light';
            applyTheme(currentTheme);
        });
    }

    // Basic Table Sorting Logic
    const table = document.querySelector('.product-table');
    if (!table) return;

    const headers = table.querySelectorAll('th');

    headers.forEach((header, index) => {
        // Skip Rank column
        if (index === 0) return;

        header.style.cursor = 'pointer';
        header.title = 'Click to sort';

        // Add sort icon placeholder
        header.innerHTML += ' <i class="fas fa-sort" style="font-size: 0.8em; color: #64748b; margin-left: 5px;"></i>';

        header.addEventListener('click', () => {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAscending = header.classList.contains('sort-asc');

            // Clear all sort classes
            headers.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                const icon = h.querySelector('i.fa-sort, i.fa-sort-up, i.fa-sort-down');
                if (icon) {
                    icon.className = 'fas fa-sort';
                    icon.style.color = '#64748b';
                }
            });

            // Set new sort direction
            header.classList.toggle('sort-asc', !isAscending);
            header.classList.toggle('sort-desc', isAscending);

            const newIcon = header.querySelector('i');
            if (newIcon) {
                newIcon.className = !isAscending ? 'fas fa-sort-up' : 'fas fa-sort-down';
                newIcon.style.color = '#38bdf8';
            }

            rows.sort((a, b) => {
                let cellA = a.querySelectorAll('td')[index].innerText.trim();
                let cellB = b.querySelectorAll('td')[index].innerText.trim();

                // Handle numbers and currency
                if (cellA.includes('₹')) {
                    cellA = parseFloat(cellA.replace(/[^0-9.-]+/g, ""));
                    cellB = parseFloat(cellB.replace(/[^0-9.-]+/g, ""));
                } else if (!isNaN(parseFloat(cellA)) && isFinite(cellA)) {
                    cellA = parseFloat(cellA);
                    cellB = parseFloat(cellB);
                }

                if (cellA < cellB) return isAscending ? 1 : -1;
                if (cellA > cellB) return isAscending ? -1 : 1;
                return 0;
            });

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));

            // Update rank pills to maintain visual order 1,2,3...
            const updatedRows = tbody.querySelectorAll('tr');
            updatedRows.forEach((row, i) => {
                const rankPill = row.querySelector('.rank-pill');
                if (rankPill) rankPill.innerText = i + 1;

                // Keep top-row styling on the actual top row
                if (i === 0) row.classList.add('top-row');
                else row.classList.remove('top-row');
            });
        });
    });
});
