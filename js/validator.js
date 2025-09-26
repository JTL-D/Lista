// js/validator.js

export function validateMasterWorkbook(wb) {
  if (!wb.worksheets.length) {
    throw new Error('Το Master αρχείο δεν περιέχει κανένα φύλλο.');
  }
  const required = ['ID', 'NAME', 'DATE'];
  wb.worksheets.forEach(ws => {
    const headers = ws.getRow(1)
      .values.slice(1)
      .map(v => (v || '').toString().trim().toUpperCase());
    required.forEach(col => {
      if (!headers.includes(col)) {
        throw new Error(`Στο φύλλο "${ws.name}" λείπει η στήλη "${col}".`);
      }
    });
  });
}

export function validateInfoWorkbook(wb) {
  if (wb.worksheets.length !== 1) {
    throw new Error('Το INFO αρχείο πρέπει να περιέχει μόνο ένα φύλλο.');
  }
  const ws = wb.worksheets[0];
  if (ws.name.trim().toUpperCase() !== 'INFO') {
    throw new Error('Το φύλλο του INFO αρχείου πρέπει να ονομάζεται "INFO".');
  }
  const row1 = ws.getRow(1).values.slice(1);
  if (row1.every(v => !v)) {
    throw new Error('Στο INFO φύλλο η 1η γραμμή πρέπει να έχει τουλάχιστον μία τιμή.');
  }
}
