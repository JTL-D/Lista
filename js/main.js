// js/main.js

import { loadWorkbook } from './loader.js';
import { validateMasterWorkbook } from './validator.js';

const masterInput    = document.getElementById('masterInput');
const infoInput      = document.getElementById('infoInput');
const masterDrop     = document.getElementById('masterDrop');
const infoDrop       = document.getElementById('infoDrop');
const masterFileName = document.getElementById('masterFileName');
const infoFileName   = document.getElementById('infoFileName');
const preview        = document.getElementById('preview');

const state = {
  files: { master: null, info: null },
  context: {}
};

function getExt(file) {
  const idx = file.name.lastIndexOf('.');
  return idx > -1 ? file.name.slice(idx + 1).toLowerCase() : '';
}
function getBaseName(file) {
  const idx = file.name.lastIndexOf('.');
  return idx > -1 ? file.name.slice(0, idx) : file.name;
}
function isValidExcel(file) {
  const ext = getExt(file);
  return ext === 'xlsx' || ext === 'xls';
}
function showError(msg, box) {
  preview.innerHTML = `<p style="color:red;">${msg}</p>`;
  if (box) box.classList.add('error');
}
function clearBoxUI(box) {
  box.classList.remove('error','loaded');
  if (box === masterDrop) masterFileName.textContent = '';
  if (box === infoDrop)   infoFileName.textContent   = '';
  preview.innerHTML = `<p>Ονόματα φύλλων θα εμφανιστούν εδώ μόλις ολοκληρωθεί ο έλεγχος.</p>`;
}

async function tryLoadWorkbooks() {
  if (!state.files.master || !state.files.info) return;

  preview.innerHTML = '<p>Φορτώνω & ελέγχω το INFO αρχείο…</p>';
  try {
    const wbM = await loadWorkbook(state.files.master);
    const wbI = await loadWorkbook(state.files.info);
    state.context.workbookMaster = wbM;
    state.context.workbookInfo   = wbI;

    if (getBaseName(state.files.info).toUpperCase() !== 'INFO') {
      showError(`Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls`, infoDrop);
      return;
    }

    const sheetsM = wbM.worksheets.map(ws => ws.name);
    const sheetsI = wbI.worksheets.map(ws => ws.name);
    preview.innerHTML = `
      <h2>Έλεγχος ΕΠΙΤΥΧΙΑ</h2>
      <p><strong>Πελάτες sheets:</strong> ${sheetsM.join(', ')}</p>
      <p><strong>INFO sheets:</strong> ${sheetsI.join(', ')}</p>
    `;
  } catch (err) {
    showError(`Σφάλμα κατά την επεξεργασία: ${err.message}`);
  }
}

masterInput.addEventListener('change', async e => {
  clearBoxUI(masterDrop);
  const file = e.target.files[0] || null;
  state.files.master = null;
  if (!file) return;

  if (getBaseName(file).toUpperCase() === 'INFO') {
    showError(`Το αρχείο ${file.name} δεν μπορεί να χρησιμοποιηθεί εδώ.`, masterDrop);
    return;
  }
  if (!isValidExcel(file)) {
    showError(`Μη έγκυρος τύπος αρχείου: ${file.name}`, masterDrop);
    return;
  }

  try {
    const wb = await loadWorkbook(file);
    validateMasterWorkbook(wb);
  } catch (err) {
    showError(err.message, masterDrop);
    return;
  }

  masterDrop.classList.add('loaded');
  masterFileName.textContent = file.name;
  state.files.master = file;
  tryLoadWorkbooks();
});

infoInput.addEventListener('change', async e => {
  clearBoxUI(infoDrop);
  const file = e.target.files[0] || null;
  state.files.info = null;
  if (!file) return;

  if (!isValidExcel(file) || getBaseName(file).toUpperCase() !== 'INFO') {
    showError(`Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls`, infoDrop);
    return;
  }

  infoDrop.classList.add('loaded');
  infoFileName.textContent = file.name;
  state.files.info = file;
  tryLoadWorkbooks();
});
