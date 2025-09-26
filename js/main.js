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

  let masterFile = null;
  let infoFile   = null;

  function getBaseName(file) {
    return file.name.slice(0, file.name.lastIndexOf('.'));
  }
  function getExt(file) {
    return file.name.split('.').pop().toLowerCase();
  }

  /**
   * Σπάει το msg στο "<br>" και δημιουργεί δύο <p>:
   *  κόκκινο για το λάθος και γκρι για την προτροπή.
   */

function showError(msg, box) {
  preview.innerHTML =
    `<p style="color:red; white-space: pre-line; margin:0;">${msg}</p>`;
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
      // Master
      const wbM = await loadWorkbook(masterFile);
      validateMasterWorkbook(wbM);
      unmergeAndClean(wbM);

      // INFO
      const wbI = await loadWorkbook(infoFile);
      if (getBaseName(infoFile).toUpperCase() !== 'INFO') {
        throw new Error(
          'Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls' +
          '<br>Μετονομάστε το σε INFO.xlsx'
        );
      }

      // Επιτυχία
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
    masterFile = null;
    if (!file) return;

    if (getBaseName(file).toUpperCase() === 'INFO') {
      showError(
        `Το αρχείο ${file.name} δεν μπορεί να χρησιμοποιηθεί εδώ.` +
        `<br>Επέλεξε αρχείο πελατών`,
        masterDrop
      );
      return;
    }
    if (!['xlsx','xls'].includes(getExt(file))) {
      showError(
        `Μη έγκυρος τύπος αρχείου: ${file.name}` +
        `<br>Χρησιμοποίησε .xlsx ή .xls`,
        masterDrop
      );
      return;
    }

    masterDrop.classList.add('loaded');
    masterFileName.textContent = file.name;
    masterFile = file;
    if (infoFile) processFiles();
  });

  infoInput.addEventListener('change', e => {
    clearBox(infoDrop, infoFileName);
    const file = e.target.files[0] || null;
    infoFile = null;
    if (!file) return;

    if (getBaseName(file).toUpperCase() !== 'INFO' ||
        !['xlsx','xls'].includes(getExt(file))) {
      showError(
        `Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls` +
        `<br>Μετονομάστε το σε INFO.xlsx`,
        infoDrop
      );
      return;
    }

    infoDrop.classList.add('loaded');
    infoFileName.textContent = file.name;
    infoFile = file;
    if (masterFile) processFiles();
  });

  preview.innerHTML = defaultPreview;
});
