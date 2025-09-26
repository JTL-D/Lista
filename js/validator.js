// js/validator.js

const requiredCols = ['Κωδ.Πελάτη','Συνεργάτης','Οδός'];

/**
 * Ελέγχει ότι στο πρώτο φύλλο του wb υπάρχουν όλες οι απαιτούμενες στήλες.
 * @param {ExcelJS.Workbook} wb
 * @throws Error αν λείπουν στήλες
 */
export function validateMasterWorkbook(wb) {
  const header = wb
    .worksheets[0]
    .getRow(1)
    .values
    .slice(1)
    .map(v => (typeof v === 'string' ? v.trim() : v));
  const missing = requiredCols.filter(c => !header.includes(c));
  if (missing.length) {
    throw new Error(
      `Λείπουν στήλες: ${missing.join(', ')}. ` +
      `Απαιτούμενες: ${requiredCols.join(', ')}.`
    );
  }
}
