// js/loader.js
import ExcelJS from 'exceljs';

window.loadFile = async function(type) {
  const input = document.getElementById(
    type === 'master' ? 'masterDropFile' : 'dataDropFile'
  );
  if (!input.files || !input.files[0]) return;

  const nameId = type === 'master'
    ? 'masterDropFileName' : 'dataDropFileName';
  document.getElementById(nameId).textContent = input.files[0].name;

  const buffer = await input.files[0].arrayBuffer();
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(buffer);

  window.dispatchEvent(new CustomEvent('excel-loaded', {
    detail: { type, workbook }
  }));
};
