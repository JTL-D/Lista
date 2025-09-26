// js/validator.js

/**
 * Validates the “Master” workbook.
 * - Must have ≥ 1 φύλλο.
 * - Σε κάθε φύλλο, η 1η γραμμή πρέπει να περιέχει στήλες: ID, NAME, DATE.
 * @param {ExcelJS.Workbook} wb
 * @throws {Error} με το κατάλληλο μήνυμα
 */
export function validateMasterWorkbook(wb) {
  if (!wb.worksheets.length) {
    throw new Error('Το Master αρχείο δεν περιέχει κανένα φύλλο.');
  }

  const requiredHeaders = ['ID', 'NAME', 'DATE'];

  wb.worksheets.forEach(ws => {
    const headerRow = ws.getRow(1);
    // slice(1) επειδή row.values[0] είναι undefined
    const headers = headerRow.values.slice(1).map(v => (v + '').trim().toUpperCase());

    requiredHeaders.forEach(col => {
      if (!headers.includes(col)) {
        throw new Error(`Στο φύλλο "${ws.name}" λείπει η στήλη "${col}".`);
      }
    });
  });
}

/**
 * Validates the “INFO” workbook.
 * - Πρέπει να έχει ακριβώς ένα φύλλο με όνομα INFO.
 * - Στο φύλλο INFO, η 1η γραμμή δεν πρέπει να είναι κενή.
 * @param {ExcelJS.Workbook} wb
 * @throws {Error} με το κατάλληλο μήνυμα
 */
export function validateInfoWorkbook(wb) {
  if (wb.worksheets.length !== 1) {
    throw new Error('Το INFO αρχείο πρέπει να περιέχει ακριβώς ένα φύλλο.');
  }

  const ws = wb.worksheets[0];
  if (ws.name.trim().toUpperCase() !== 'INFO') {
    throw new Error('Το φύλλο του INFO αρχείου πρέπει να ονομάζεται "INFO".');
  }

  const headerRow = ws.getRow(1);
  if (headerRow.cellCount === 0 || headerRow.values.slice(1).every(v => !v)) {
    throw new Error('Στο INFO φύλλο η 1η γραμμή πρέπει να περιέχει τουλάχιστον μία στήλη.');
  }
}

/**
 * Δένει τη ροή validation στο event excel-loaded.
 * Όταν φορτώσει ένα αρχείο:
 *  - master → validateMasterWorkbook
 *  - info   → validateInfoWorkbook
 *
 * Σε περίπτωση σφάλματος, κάνει dispatch event
 * "excel-validation-error" με detail { type, message }.
 */
export function bindValidator() {
  window.addEventListener('excel-loaded', e => {
    const { type, workbook } = e.detail;
    try {
      if (type === 'master') {
        validateMasterWorkbook(workbook);
      } else if (type === 'data') {
        validateInfoWorkbook(workbook);
      }
    } catch (err) {
      window.dispatchEvent(new CustomEvent('excel-validation-error', {
        detail: { type, message: err.message }
      }));
    }
  });
}

// Αυτόματα bind μόλις φορτωθεί το module
bindValidator();
