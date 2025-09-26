
// js/unmergeClean.js
export function unmergeAndClean(ctx) {
  ctx.context.workbookMaster.worksheets.forEach(ws => {
    ws._merges.forEach(range => ws.unMergeCells(range));
    ws.eachRow(row => {
      row.eachCell(cell => {
        if (typeof cell.value === 'string') {
          cell.value = cell.value.trim().toUpperCase();
        }
      });
    });
  });
  return ctx;
}
