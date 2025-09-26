// js/loader.js

/**
 * Φορτώνει ένα Excel workbook από File.
 * @param {File} file
 * @returns {Promise<ExcelJS.Workbook>}
 */
export async function loadWorkbook(file) {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.load(await file.arrayBuffer());
  return wb;
}
