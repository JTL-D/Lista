// js/validator.js

const requiredCols = ['Κωδ.Πελάτη','Συνεργάτης','Οδός'];

/**
 * Ελέγχει ότι στο πρώτο φύλλο υπάρχουν όλες οι
 * απαιτούμενες στήλες. Αν λείπουν, πετάει Error
 * με <br> για διπλή γραμμή.
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
    const firstLine  = `Λείπουν στήλες: ${missing.join(', ')}.`;
    const secondLine = `Απαιτούμενες: ${requiredCols.join(', ')}.`;
    throw new Error(firstLine + '<br>' + secondLine);
  }
}
