// js/loader.js
export async function loadWorkbook(file) {
  // console.log('loadWorkbook', file);
  const buffer = await file.arrayBuffer();
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.load(buffer);
  return wb;
}
