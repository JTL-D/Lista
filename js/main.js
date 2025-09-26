// js/main.js
import { Loader } from './loader.js';
import { validateMaster } from './validator.js';
import { unmergeAndClean } from './unmergeClean.js';

document.addEventListener('DOMContentLoaded', () => {
  const masterInput = document.getElementById('masterInput');
  const infoInput   = document.getElementById('infoInput');
  const masterDrop  = document.getElementById('masterDrop');
  const infoDrop    = document.getElementById('infoDrop');
  const preview     = document.getElementById('preview');

  const state = { files: { master: null, info: null }, context: {} };

  function showStatus(msg, error = false) {
    preview.innerHTML = `<p style="color:${error?'red':'green'};">${msg}</p>`;
  }

  async function orchestrate() {
    try {
      await Loader(state);
      validateMaster(state);
      unmergeAndClean(state);
      showStatus('Validation ✓ Unmerge & Clean ✓');
    } catch (err) {
      showStatus(err.message, true);
    }
  }

  masterInput.addEventListener('change', e => {
    state.files.master = e.target.files[0] || null;
    masterDrop.classList.remove('error','loaded');
    if (state.files.master) masterDrop.classList.add('loaded');
    if (state.files.info) orchestrate();
  });

  infoInput.addEventListener('change', e => {
    state.files.info = e.target.files[0] || null;
    infoDrop.classList.remove('error','loaded');
    if (state.files.info) infoDrop.classList.add('loaded');
    if (state.files.master) orchestrate();
  });
});
