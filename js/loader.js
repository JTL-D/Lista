// js/loader.js

export async function loadWorkbook(file) {
  const buffer = await file.arrayBuffer();
  const workbook = new window.ExcelJS.Workbook();
  await workbook.xlsx.load(buffer);
  return workbook;
}
