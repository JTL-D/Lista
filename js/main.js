// js/main.js
// Legacy functions - δεν πειράζονται

async function uploadMaster() {
  const input = document.getElementById('masterDropFile');
  if (!input.files || !input.files[0]) return;
  document.getElementById('masterDropFileName').textContent =
    input.files[0].name;
  // υπάρχουσα λογική validation για MASTER
}

async function uploadData() {
  const input = document.getElementById('dataDropFile');
  if (!input.files || !input.files[0]) return;
  document.getElementById('dataDropFileName').textContent =
    input.files[0].name;
  // υπάρχουσα λογική data upload (θα αντικατασταθεί από loader.js)
}
