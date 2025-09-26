// js/main.js

import { loadWorkbook } from './loader.js';
import { validateMasterWorkbook } from './validator.js';
import { unmergeAndClean } from './unmergeClean.js';

const defaultPreview = `<p>Επέλεξε δύο έγκυρα αρχεία για να φορτωθούν.</p>`;

document.addEventListener('DOMContentLoaded', () => {
  const masterInput    = document.getElementById('masterInput');
  const infoInput      = document.getElementById('infoInput');
  const masterDrop     = document.getElementById('masterDrop');
  const infoDrop       = document.getElementById('infoDrop');
  const masterFileName = document.getElementById('masterFileName');
  const infoFileName   = document.getElementById('infoFileName');
  const preview        = document.getElementById('preview');

  const state = { masterWb: null, infoWb: null };

  // Helpers
  function getExt(file) {
    const idx = file.name.lastIndexOf('.');
    return idx > -1 ? file.name.slice(idx+1).toLowerCase() : '';
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
    const parts = msg.split(/<br\s*\/?>/);
    preview.innerHTML = parts
      .map(line => `<p style="color:red;">${line.trim()}</p>`)
      .join('');
    if (box) box.classList.add('error');
  }
  function clearBoxUI(box, nameEl) {
    box.classList.remove('error','loaded');
    nameEl.textContent = '';
    preview.innerHTML = defaultPreview;
  }

  async function tryProcess() {
    preview.innerHTML = `<p>Φορτώνω & ελέγχω αρχεία…</p>`;
    try {
      // master
      const wbM = await loadWorkbook(state.masterWb);
      validateMasterWorkbook(wbM);
      unmergeAndClean(wbM);

      // INFO
      const wbI = await loadWorkbook(state.infoWb);
      if (getBaseName(state.infoWb).toUpperCase() !== 'INFO') {
        throw new Error('Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls');
      }

      preview.innerHTML = `
        <h2>Έλεγχος ΕΠΙΤΥΧΙΑ</h2>
        <p><strong>Master sheets:</strong> ${wbM.worksheets.map(ws=>ws.name).join(', ')}</p>
        <p><strong>INFO sheets:</strong> ${wbI.worksheets.map(ws=>ws.name).join(', ')}</p>
      `;
    } catch (err) {
      showError(err.message, null);
    }
  }

  masterInput.addEventListener('change', e => {
    clearBoxUI(masterDrop, masterFileName);
    const file = e.target.files[0] || null;
    if (!file) return;

    if (getBaseName(file).toUpperCase() === 'INFO') {
      showError(`Το αρχείο ${file.name} δεν μπορεί να χρησιμοποιηθεί εδώ.`, masterDrop);
      return;
    }
    if (!isValidExcel(file)) {
      showError(`Μη έγκυρος τύπος αρχείου: ${file.name}`, masterDrop);
      return;
    }

    masterDrop.classList.add('loaded');
    masterFileName.textContent = file.name;
    state.masterWb = file;
    if (state.infoWb) tryProcess();
  });

  infoInput.addEventListener('change', e => {
    clearBoxUI(infoDrop, infoFileName);
    const file = e.target.files[0] || null;
    if (!file) return;

    if (!isValidExcel(file) || getBaseName(file).toUpperCase() !== 'INFO') {
      showError('Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls', infoDrop);
      return;
    }

    infoDrop.classList.add('loaded');
    infoFileName.textContent = file.name;
    state.infoWb = file;
    if (state.masterWb) tryProcess();
  });

  // init
  preview.innerHTML = defaultPreview;
});
