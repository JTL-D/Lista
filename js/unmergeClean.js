// js/unmergeClean.js

/**
 * Αφαιρεί merged ranges και καθαρίζει κελιά
 * (trim + uppercase) σε όλα τα φύλλα.
 * @param {ExcelJS.Workbook} wb
 */
export function unmergeAndClean(wb) {
  wb.worksheets.forEach(ws => {
    // Unmerge όλων των ranged merges
    ws._merges.forEach(range => ws.unMergeCells(range));
    // Καθαρισμός δεδομένων
    ws.eachRow(row => {
      row.eachCell(cell => {
        if (typeof cell.value === 'string') {
          cell.value = cell.value.trim().toUpperCase();
        }
      });
    });
  });
}
