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

  const state = { masterFile: null, infoFile: null };

  // Helpers από inline logic
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

  /**
   * Σπάει το msg στο "<br>" και δημιουργεί
   * δύο <p>, το πρώτο κόκκινο (λάθος),
   * το δεύτερο γκρι (προτροπή/απαίτηση).
   */
  function showError(msg, box) {
    const [errLine, reqLine] = msg.split(/<br\s*\/?>/);
    preview.innerHTML =
      `<p style="color:red; margin:0;">${errLine.trim()}</p>` +
      `<p style="color:#555; margin:0 0 1rem;">${reqLine.trim()}</p>`;
    if (box) box.classList.add('error');
  }

  function clearBox(box, nameEl) {
    box.classList.remove('error','loaded');
    nameEl.textContent = '';
    preview.innerHTML = defaultPreview;
  }

  async function processFiles() {
    preview.innerHTML = `<p>Φορτώνω & ελέγχω αρχεία…</p>`;
    try {
      // 1. Φόρτωμα Master, έλεγχος στηλών, unmerge & clean
      const wbM = await loadWorkbook(state.masterFile);
      validateMasterWorkbook(wbM);
      unmergeAndClean(wbM);

      // 2. Φόρτωμα INFO & έλεγχος ονόματος
      const wbI = await loadWorkbook(state.infoFile);
      if (getBaseName(state.infoFile).toUpperCase() !== 'INFO') {
        throw new Error(
          'Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls'
        );
      }

      // 3. Εμφάνιση επιτυχίας
      preview.innerHTML = `
        <h2>Έλεγχος ΕΠΙΤΥΧΙΑ</h2>
        <p><strong>Master sheets:</strong> ${wbM.worksheets.map(ws => ws.name).join(', ')}</p>
        <p><strong>INFO sheets:</strong> ${wbI.worksheets.map(ws => ws.name).join(', ')}</p>
      `;
    } catch (err) {
      showError(err.message, null);
    }
  }

  masterInput.addEventListener('change', e => {
    clearBox(masterDrop, masterFileName);
    const file = e.target.files[0] || null;
    if (!file) return;

    if (getBaseName(file).toUpperCase() === 'INFO') {
      showError(
        `Το αρχείο ${file.name} δεν μπορεί να χρησιμοποιηθεί εδώ.` +
        `<br>Επέλεξε αρχείο πελατών`, 
        masterDrop
      );
      return;
    }
    if (!isValidExcel(file)) {
      showError(
        `Μη έγκυρος τύπος αρχείου: ${file.name}` +
        `<br>Χρησιμοποίησε .xlsx ή .xls`, 
        masterDrop
      );
      return;
    }

    masterDrop.classList.add('loaded');
    masterFileName.textContent = file.name;
    state.masterFile = file;
    if (state.infoFile) processFiles();
  });

  infoInput.addEventListener('change', e => {
    clearBox(infoDrop, infoFileName);
    const file = e.target.files[0] || null;
    if (!file) return;

    if (!isValidExcel(file) || getBaseName(file).toUpperCase() !== 'INFO') {
      showError(
        `Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls` +
        `<br>Μετονόμασέ το σε INFO.xlsx`, 
        infoDrop
      );
      return;
    }

    infoDrop.classList.add('loaded');
    infoFileName.textContent = file.name;
    state.infoFile = file;
    if (state.masterFile) processFiles();
  });

  // init
  preview.innerHTML = defaultPreview;
});
