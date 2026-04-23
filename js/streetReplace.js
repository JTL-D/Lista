// js/streetReplace.js

const REQUIRED_INFO_COLS = ['Κωδ.Πελάτη', 'Συνεργάτης', 'Από', 'Σε'];
const INFO_SHEET_NAME = 'Street Name Replace';

/**
 * Κανονικοποίηση για σύγκριση κειμένου:
 *  trim + UPPERCASE + collapse whitespace + αφαίρεση τόνων (NFD).
 */
function normalize(s) {
  if (s == null) return '';
  // Τα cell values του ExcelJS μπορεί να είναι richText objects ή formula results.
  let str;
  if (typeof s === 'object') {
    if (Array.isArray(s.richText)) str = s.richText.map(r => r.text).join('');
    else if ('result' in s) str = s.result;
    else if ('text' in s) str = s.text;
    else str = String(s);
  } else {
    str = String(s);
  }
  return str
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toUpperCase()
    .replace(/\s+/g, ' ');
}

/** Κωδικός πελάτη: κρατάμε ως string (χωρίς UPPERCASE) για να μη χαθούν leading zeros. */
function normalizeCode(s) {
  if (s == null) return '';
  if (typeof s === 'object') {
    if ('result' in s) s = s.result;
    else if ('text' in s) s = s.text;
  }
  return String(s).trim();
}

function getHeaderMap(ws) {
  const header = ws.getRow(1).values.slice(1).map(v => (typeof v === 'string' ? v.trim() : v));
  const map = {};
  header.forEach((h, i) => { if (h) map[h] = i + 1; });
  return map;
}

/**
 * Ελέγχει το INFO workbook: πρέπει να υπάρχει φύλλο "Street Name Replace"
 * με τις 4 απαιτούμενες στήλες.
 */
export function validateInfoReplaceSheet(wb) {
  const ws = wb.getWorksheet(INFO_SHEET_NAME);
  if (!ws) {
    throw new Error(
      `Λείπει το φύλλο "${INFO_SHEET_NAME}". ` +
      `Το INFO πρέπει να περιέχει φύλλο με αυτό το όνομα.`
    );
  }
  const map = getHeaderMap(ws);
  const missing = REQUIRED_INFO_COLS.filter(c => !(c in map));
  if (missing.length) {
    throw new Error(
      `Λείπουν στήλες στο φύλλο "${INFO_SHEET_NAME}": ${missing.join(', ')}. ` +
      `Απαιτούμενες: ${REQUIRED_INFO_COLS.join(', ')}.`
    );
  }
  return { ws, map };
}

/**
 * Διαβάζει τους κανόνες από το "Street Name Replace".
 * Επιστρέφει { rules, warnings }.
 * Κανόνες:
 *  - Κενά "Από" ή "Σε"                       -> skip + warning
 *  - Κενά και "Κωδ.Πελάτη" και "Συνεργάτης"  -> skip + warning (όχι global)
 *  - Αλλιώς προστίθεται κανόνας με specificity (1 ή 2).
 */
function parseRules(ws, map) {
  const rules = [];
  const warnings = [];
  const last = ws.actualRowCount || ws.rowCount;

  for (let r = 2; r <= last; r++) {
    const row = ws.getRow(r);
    const kwdRaw = row.getCell(map['Κωδ.Πελάτη']).value;
    const synRaw = row.getCell(map['Συνεργάτης']).value;
    const fromRaw = row.getCell(map['Από']).value;
    const toRaw = row.getCell(map['Σε']).value;

    const kwd = normalizeCode(kwdRaw);
    const syn = normalize(synRaw);
    const from = normalize(fromRaw);
    const toNorm = normalize(toRaw);

    // εντελώς κενή γραμμή -> ignore σιωπηλά
    if (!kwd && !syn && !from && !toNorm) continue;

    if (!from || !toNorm) {
      warnings.push(`Γραμμή ${r}: κενό "Από" ή "Σε" — παραλείπεται.`);
      continue;
    }
    if (!kwd && !syn) {
      warnings.push(
        `Γραμμή ${r}: κενά και "Κωδ.Πελάτη" και "Συνεργάτης" — παραλείπεται ` +
        `(δεν επιτρέπεται global replacement).`
      );
      continue;
    }

    // Η τιμή που θα γράψουμε στο "Οδός": κρατάμε το original trimmed text,
    // αλλά επειδή το master έχει γίνει UPPERCASE στο unmergeAndClean,
    // γράφουμε και εμείς σε UPPERCASE για συνέπεια.
    let toWrite;
    if (toRaw == null) toWrite = '';
    else if (typeof toRaw === 'object' && 'text' in toRaw) toWrite = String(toRaw.text);
    else if (typeof toRaw === 'object' && 'result' in toRaw) toWrite = String(toRaw.result);
    else toWrite = String(toRaw);
    toWrite = toWrite.trim().toUpperCase().replace(/\s+/g, ' ');

    rules.push({
      row: r,
      kwd,
      syn,
      from,
      to: toWrite,
      specificity: (kwd ? 1 : 0) + (syn ? 1 : 0)
    });
  }

  // Most-specific first: πρώτοι ελέγχονται οι κανόνες με Κωδ+Συνεργάτης.
  rules.sort((a, b) => b.specificity - a.specificity);

  return { rules, warnings };
}

/**
 * Εφαρμόζει τις αντικαταστάσεις στη στήλη "Οδός" όλων των φύλλων του master wb.
 * Ταίριασμα exact (ολόκληρη η τιμή του "Οδός" == "Από" μετά από normalize).
 *
 * @param {ExcelJS.Workbook} masterWb
 * @param {ExcelJS.Workbook} infoWb
 * @returns {{ totalChanges:number, rulesTotal:number, rulesUsed:number,
 *            warnings:string[], unused:string[] }}
 */
export function applyStreetReplacements(masterWb, infoWb) {
  const { ws: infoWs, map } = validateInfoReplaceSheet(infoWb);
  const { rules, warnings } = parseRules(infoWs, map);

  const hits = new Array(rules.length).fill(0);
  let totalChanges = 0;

  masterWb.worksheets.forEach(ws => {
    const header = getHeaderMap(ws);
    const cKwd = header['Κωδ.Πελάτη'];
    const cSyn = header['Συνεργάτης'];
    const cStreet = header['Οδός'];
    if (!cKwd || !cSyn || !cStreet) return;

    const last = ws.actualRowCount || ws.rowCount;
    for (let r = 2; r <= last; r++) {
      const row = ws.getRow(r);
      const streetCell = row.getCell(cStreet);
      const streetNorm = normalize(streetCell.value);
      if (!streetNorm) continue;

      const rowKwd = normalizeCode(row.getCell(cKwd).value);
      const rowSyn = normalize(row.getCell(cSyn).value);

      for (let i = 0; i < rules.length; i++) {
        const rule = rules[i];
        if (rule.kwd && rule.kwd !== rowKwd) continue;
        if (rule.syn && rule.syn !== rowSyn) continue;
        if (rule.from !== streetNorm) continue;

        streetCell.value = rule.to;
        hits[i]++;
        totalChanges++;
        break; // most-specific wins
      }
    }
  });

  const unused = rules
    .map((rule, i) => ({ rule, count: hits[i] }))
    .filter(x => x.count === 0)
    .map(x => {
      const key = [
        x.rule.kwd ? `Κωδ.=${x.rule.kwd}` : null,
        x.rule.syn ? `Συν.=${x.rule.syn}` : null
      ].filter(Boolean).join(', ');
      return `Γραμμή ${x.rule.row}: κανένα match για "${x.rule.from}" (${key}).`;
    });

  return {
    totalChanges,
    rulesTotal: rules.length,
    rulesUsed: hits.filter(c => c > 0).length,
    warnings,
    unused
  };
}
