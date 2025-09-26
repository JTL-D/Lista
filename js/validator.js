// js/validator.js
const requiredCols = ['Κωδ.Πελάτη','Συνεργάτης','Οδός'];

export function validateMasterWorkbook(wb) {
  const header = wb.worksheets[0]
    .getRow(1).values.slice(1)
    .map(v => typeof v==='string' ? v.trim() : v);
  const missing = requiredCols.filter(c => !header.includes(c));
  if (missing.length) {
    // 1η γραμμή + \n + 2η γραμμή
    const msg =
      `Λείπουν στήλες: ${missing.join(', ')}.` +
      `\nΑπαιτούμενες: ${requiredCols.join(', ')}.`;
    throw new Error(msg);
  }
}
