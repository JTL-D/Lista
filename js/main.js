// js/main.js

import { loadWorkbook } from './loader.js';
import { validateMasterWorkbook, validateInfoWorkbook } from './validator.js';

const masterInput    = document.getElementById('masterInput');
const infoInput      = document.getElementById('infoInput');
const masterDrop     = document.getElementById('masterDrop');
const infoDrop       = document.getElementById('infoDrop');
const masterFileName = document.getElementById('masterFileName');
const infoFileName   = document.getElementById('infoFileName');
const preview        = document.getElementById('preview');

function showError(msg, box) {
  const [first, ...rest] = msg.split('. ');
  preview.innerHTML =
    `<p style="color:red; margin:0;">${first}.</p>` +
    `<p style="color:#555; margin:0 0 1rem;">${rest.join('. ')}</p>`;
  if (box) box.classList.add('error');
}

function clearBox(box) {
  box.classList.remove('error', 'loaded');
  if (box === masterDrop) masterFileName.textContent = '';
  if (box === infoDrop)   infoFileName.textContent   = '';
  preview.innerHTML = `<p>Ονόματα φύλλων θα εμφανιστούν εδώ μόλις ολοκληρωθεί ο έλεγχος.</p>`;
}

async function processFiles() {
  if (!masterInput.files[0] || !infoInput.files[0]) return;
  preview.innerHTML = '<p>Φορτώνω & ελέγχω το INFO αρχείο…</p>';

  try {
    const wbM = await loadWorkbook(masterInput.files[0]);
    validateMasterWorkbook(wbM);

    const wbI = await loadWorkbook(infoInput.files[0]);
    validateInfoWorkbook(wbI);

    const sM = wbM.worksheets.map(ws => ws.name).join(', ');
    const sI = wbI.worksheets.map(ws => ws.name).join(', ');

    preview.innerHTML = `
      <h2>Έλεγχος ΕΠΙΤΥΧΙΑ</h2>
      <p><strong>Master sheets:</strong> ${sM}</p>
      <p><strong>INFO sheets:</strong> ${sI}</p>
    `;
  } catch (err) {
    const targetBox = err.message.includes('Master') ? masterDrop : infoDrop;
    showError(err.message, targetBox);
  }
}

masterInput.addEventListener('change', e => {
  clearBox(masterDrop);
  const f = e.target.files[0];
  if (!f) return;
  masterFileName.textContent = f.name;
  masterDrop.classList.add('loaded');
  processFiles();
});

infoInput.addEventListener('change', e => {
  clearBox(infoDrop);
  const f = e.target.files[0];
  if (!f) return;
  infoFileName.textContent = f.name;
  infoDrop.classList.add('loaded');
  processFiles();
});
