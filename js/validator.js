// js/validator.js
const requiredCols = ['Κωδ.Πελάτη','Συνεργάτης','Οδός'];

/**
 * Ελέγχει ότι το master workbook έχει
 * τις υποχρεωτικές στήλες στο πρώτο φύλλο.
 * Αν λείπουν, πετάει Error με δύο μέρη:
 * 1η γραμμή: τι λείπει
 * 2η γραμμή: ποιες είναι οι απαιτήσεις
 */
export function validateMaster(ctx) {
  const ws = ctx.context.workbookMaster.worksheets[0];
  const header = ws
    .getRow(1)
    .values
    .slice(1)
    .map(v => (typeof v === 'string' ? v.trim() : v));
  const missing = requiredCols.filter(col => !header.includes(col));

  if (missing.length) {
    const msg =
      `Λείπουν στήλες: ${missing.join(', ')}.<br>` +
      `Απαιτούμενες: ${requiredCols.join(', ')}.`;
    throw new Error(msg);
  }
  return ctx;
}
