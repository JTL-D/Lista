// js/main.js

import { Loader } from './loader.js';
import { validateMaster } from './validator.js';
import { unmergeAndClean } from './unmergeClean.js';

const requiredCols = ['Κωδ.Πελάτη','Συνεργάτης','Οδός'];
const defaultPreview = `<p>Επέλεξε δύο έγκυρα αρχεία για να φορτωθούν.</p>`;

document.addEventListener('DOMContentLoaded', () => {
  const masterInput    = document.getElementById('masterInput');
  const infoInput      = document.getElementById('infoInput');
  const masterDrop     = document.getElementById('masterDrop');
  const infoDrop       = document.getElementById('infoDrop');
  const masterFileName = document.getElementById('masterFileName');
  const infoFileName   = document.getElementById('infoFileName');
  const preview        = document.getElementById('preview');

  const state = {
    files: { master: null, info: null },
    context: { workbookMaster: null, workbookInfo: null }
  };

  // Helpers από τον inline κώδικα
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

  function showStatus(msg, isError = false) {
    preview.innerHTML = `<p style="color:${isError?'red':'green'};">${msg}</p>`;
  }
  function clearPreview() {
    preview.innerHTML = defaultPreview;
  }

  async function orchestrate() {
    try {
      // Φόρτωμα
      await Loader(state);

      // Έλεγχος υποχρεωτικών στηλών
      validateMaster(state);

      // Unmerge & Clean
      unmergeAndClean(state);

      showStatus('Validation ✓ Unmerge & Clean ✓');
    } catch (err) {
      showStatus(err.message, true);
    }
  }

  masterInput.addEventListener('change', async e => {
    // Καθαρισμός UI
    masterDrop.classList.remove('error','loaded');
    masterFileName.textContent = '';
    clearPreview();

    const file = e.target.files[0] || null;
    state.files.master = null;
    if (!file) return;

    // Αποκλεισμός INFO.xlsx
    if (getBaseName(file).toUpperCase() === 'INFO') {
      masterDrop.classList.add('error');
      showStatus(`Το αρχείο ${file.name} δεν μπορεί να χρησιμοποιηθεί εδώ.`, true);
      return;
    }

    // Έλεγχος extension
    if (!isValidExcel(file)) {
      masterDrop.classList.add('error');
      showStatus(`Μη έγκυρος τύπος αρχείου: ${file.name}`, true);
      return;
    }

    // Όλα ok
    masterDrop.classList.add('loaded');
    masterFileName.textContent = file.name;
    state.files.master = file;

    // Αν υπάρχει και INFO, ξεκινάμε orchestrate
    if (state.files.info) {
      orchestrate();
    }
  });

  infoInput.addEventListener('change', e => {
    // Καθαρισμός UI
    infoDrop.classList.remove('error','loaded');
    infoFileName.textContent = '';
    clearPreview();

    const file = e.target.files[0] || null;
    state.files.info = null;
    if (!file) return;

    // Έλεγχος INFO όνοματος & extension
    if (!isValidExcel(file) || getBaseName(file).toUpperCase() !== 'INFO') {
      infoDrop.classList.add('error');
      showStatus(`Το INFO αρχείο πρέπει να ονομάζεται INFO.xlsx ή INFO.xls`, true);
      return;
    }

    // Όλα ok
    infoDrop.classList.add('loaded');
    infoFileName.textContent = file.name;
    state.files.info = file;

    // Αν υπάρχει και master, ξεκινάμε orchestrate
    if (state.files.master) {
      orchestrate();
    }
  });

  // Initialize preview
  clearPreview();
});
