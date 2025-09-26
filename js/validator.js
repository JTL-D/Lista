// js/validator.js

const requiredCols = ['Κωδ.Πελάτη','Συνεργάτης','Οδός'];

/**
 * Ελέγχει ότι το master workbook έχει τις υποχρεωτικές στήλες
 * στο πρώτο φύλλο, με trim και αφαίρεση κενών τιμών.
 * @param {{context:{workbookMaster:ExcelJS.Workbook}}} ctx
 * @returns {{context}} ctx
 * @throws Error με αναλυτικό μήνυμα αν λείπουν στήλες
 */
export function validateMaster(ctx) {
  const ws = ctx.context.workbookMaster.worksheets[0];
  const header = ws
    .getRow(1)
    .values
    .slice(1)
    .map(v => (typeof v === 'string' ? v.trim() : v))
    .filter(v => v != null && v !== '');

  const missing = requiredCols.filter(col => !header.includes(col));
  if (missing.length) {
    throw new Error(
      `Λείπουν στήλες: ${missing.join(', ')}. ` +
      `Απαιτούμενες: ${requiredCols.join(', ')}.`
    );
  }
  return ctx;
}
