
// js/validator.js
const requiredCols = ['Κωδ.Πελάτη', 'Συνεργάτης', 'Οδός'];

export function validateMaster(ctx) {
  const ws = ctx.context.workbookMaster.worksheets[0];
  const header = ws.getRow(1).values.slice(1);
  const missing = requiredCols.filter(c => !header.includes(c));
  if (missing.length) {
    throw new Error(`Λείπουν στήλες: ${missing.join(', ')}`);
  }
  return ctx;
}
