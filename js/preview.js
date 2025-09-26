// js/preview.js
import { unmergeAndClean } from './unmergeClean.js';

(function() {
  window.addEventListener('excel-loaded', function(e) {
    if (e.detail.type !== 'data') return;
    const workbook = e.detail.workbook;

    unmergeAndClean(workbook);

    const ws = workbook.worksheets[0];
    const container = document.getElementById('preview');
    container.innerHTML = '<h3>Preview</h3>';

    const table = document.createElement('table');
    table.className = 'preview-table';
    container.appendChild(table);

    let count = 0;
    ws.eachRow({ includeEmpty: false }, row => {
      if (count++ >= 20) return;
      const tr = document.createElement('tr');
      row.eachCell({ includeEmpty: true }, cell => {
        const td = document.createElement('td');
        td.textContent = cell.text || cell.value || '';
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });
  });
})();
