"""
Port της JS λογικής "Street Name Replace" (από index.html) σε Python,
για να τεστάρουμε συμπεριφορά χωρίς browser/Node.

Ο στόχος είναι να αναπαράγει ΑΚΡΙΒΩΣ:
  - advNormalize (trim+lowercase+NFD, αφαίρεση τόνων, collapse spaces)
  - toPlainString (για ExcelJS-style cell values)
  - header-row auto-detect στις πρώτες 5 γραμμές
  - parse κανόνων (skip/warnings)
  - apply σε master (scoping by Κωδ.Πελάτη/Συνεργάτης, most-specific wins)
"""

from __future__ import annotations
import re
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass


# --------- port των helpers από το index.html ---------

def adv_normalize(val) -> str:
    if val is None:
        return ""
    if isinstance(val, dict):
        for k in ("text", "result", "value"):
            if k in val and val[k] is not None:
                val = val[k]
                break
    s = str(val)
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", "", s)
    return s


def to_plain_string(val) -> str:
    if val is None:
        return ""
    if isinstance(val, str):
        return "" if re.search(r"\[object Object\]", val, re.I) else val
    if isinstance(val, (int, float, bool)):
        return str(val)
    if isinstance(val, dict):
        if "richText" in val and isinstance(val["richText"], list):
            return "".join(p.get("text", "") for p in val["richText"])
        for k in ("text", "result", "value"):
            if k in val and val[k] is not None:
                return to_plain_string(val[k])
    if isinstance(val, list):
        return "".join(to_plain_string(x) for x in val)
    return ""


# --------- parsing rules από το worksheet ---------

@dataclass
class Rule:
    row: int
    kwd: str
    syn: str
    from_key: str
    to: str
    specificity: int


def parse_rules(sheet_rows: list[list[str]]) -> tuple[list[Rule], list[str]]:
    """
    sheet_rows[r][c] (1-based) όπως τα επιστρέφει το ExcelJS.
    Αντιγράφει τη λογική του index.html.
    """
    warnings: list[str] = []
    k_kwd = adv_normalize("Κωδ.Πελάτη")
    k_syn = adv_normalize("Συνεργάτης")
    k_from = adv_normalize("Από")
    k_to = adv_normalize("Σε")

    header_row_num = -1
    c_kwd = c_syn = c_from = c_to = 0
    scan_up_to = min(5, len(sheet_rows) - 1)
    for r in range(1, scan_up_to + 1):
        values = sheet_rows[r]
        found: dict[str, int] = {}
        for c in range(1, len(values)):
            label = adv_normalize(to_plain_string(values[c]))
            if label:
                found[label] = c
        if k_from in found and k_to in found:
            header_row_num = r
            c_from = found[k_from]
            c_to = found[k_to]
            c_kwd = found.get(k_kwd, 0)
            c_syn = found.get(k_syn, 0)
            break

    if header_row_num < 0:
        warnings.append(
            'Στο φύλλο "Street Name Replace" δεν βρέθηκαν οι headers "Από"/"Σε" — παραλείπεται.'
        )
        return [], warnings
    if not c_kwd and not c_syn:
        warnings.append(
            'Στο φύλλο "Street Name Replace" λείπουν και οι δύο στήλες κλειδί — no-op.'
        )
        return [], warnings

    rules: list[Rule] = []
    for r in range(header_row_num + 1, len(sheet_rows)):
        row = sheet_rows[r]
        def cell(idx):
            return row[idx] if idx and idx < len(row) else None

        raw_kwd = to_plain_string(cell(c_kwd)).strip() if c_kwd else ""
        raw_syn = cell(c_syn) if c_syn else None
        raw_from = cell(c_from)
        raw_to = cell(c_to)

        syn_key = adv_normalize(raw_syn)
        from_key = adv_normalize(raw_from)
        to_str = to_plain_string(raw_to).strip()

        if not raw_kwd and not syn_key and not from_key and not to_str:
            continue
        if not from_key or not to_str:
            warnings.append(f'Γραμμή {r}: κενό "Από" ή "Σε" — παραλείπεται.')
            continue
        if not raw_kwd and not syn_key:
            warnings.append(
                f'Γραμμή {r}: κενά και "Κωδ.Πελάτη" και "Συνεργάτης" — παραλείπεται.'
            )
            continue

        rules.append(Rule(
            row=r, kwd=raw_kwd, syn=syn_key, from_key=from_key, to=to_str,
            specificity=(1 if raw_kwd else 0) + (1 if syn_key else 0),
        ))

    rules.sort(key=lambda x: -x.specificity)
    return rules, warnings


# --------- apply σε master ---------

def apply_replacements(master_rows: list[dict], rules: list[Rule],
                       raw_master_by_code: dict | None = None,
                       customer_replace_map: dict | None = None) -> list[dict]:
    """Αναπαράγει τον JS applyReplacements:
      1) Partner replacement (Customer Name Replace) πρώτα.
      2) Street replacement μετά, με scoping ΒΑΣΕΙ του raw master (raw_master_by_code),
         όχι των τρεχουσών τιμών του row.
    master_rows: dicts με keys 'Κωδ.Πελάτη','Συνεργάτης','Οδός'.
    raw_master_by_code: {code: {'kwd':code,'syn':adv_normalize(raw_partner)}}
    customer_replace_map: {adv_normalize(old_partner): new_partner_str}
    """
    customer_replace_map = customer_replace_map or {}
    raw_master_by_code = raw_master_by_code or {}
    out = [dict(r) for r in master_rows]
    for row in out:
        # Partner replacement
        orig_partner = row.get("Συνεργάτης")
        key = adv_normalize(orig_partner)
        if key in customer_replace_map:
            row["Συνεργάτης"] = customer_replace_map[key]

        # Street replacement — scoping από raw master
        street_key = adv_normalize(row.get("Οδός"))
        if not street_key:
            continue
        row_kwd = to_plain_string(row.get("Κωδ.Πελάτη")).strip()
        raw_info = raw_master_by_code.get(row_kwd)
        row_syn = raw_info["syn"] if raw_info else ""
        if not row_syn:
            # fallback στην τρέχουσα (ήδη replaced) τιμή
            row_syn = adv_normalize(row.get("Συνεργάτης"))
        for rule in rules:
            if rule.kwd and rule.kwd != row_kwd:
                continue
            if rule.syn and rule.syn != row_syn:
                continue
            if rule.from_key != street_key:
                continue
            row["Οδός"] = rule.to
            row["_hit_rule"] = rule.row
            break
    return out


def build_raw_map_from_rows(raw_rows: list[dict]) -> dict:
    m = {}
    for r in raw_rows:
        code = to_plain_string(r.get("Κωδ.Πελάτη")).strip()
        if not code:
            continue
        syn = adv_normalize(r.get("Συνεργάτης"))
        if code not in m or (not m[code]["syn"] and syn):
            m[code] = {"kwd": code, "syn": syn}
    return m


# --------- loader για xlsx ---------

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheet_rows(xlsx_path: str, sheet_name: str) -> list[list[str]]:
    with zipfile.ZipFile(xlsx_path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        sheets = list(wb.find("x:sheets", NS))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_to_target = {r.get("Id"): r.get("Target") for r in rels}
        target = None
        for idx, s in enumerate(sheets, 1):
            if s.get("name") == sheet_name:
                rid = s.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
                )
                target = rid_to_target[rid]
                break
        if not target:
            raise RuntimeError(f"Sheet {sheet_name!r} not found")
        ss_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        shared = [
            "".join(t.text or "" for t in si.iter(f"{{{NS['x']}}}t"))
            for si in ss_root.findall("x:si", NS)
        ]
        sheet_xml = ET.fromstring(z.read(f"xl/{target}"))
        data = sheet_xml.find("x:sheetData", NS)
        rows: list[list[str]] = [[]]  # index 0 unused (1-based)
        for row in data.findall("x:row", NS):
            rnum = int(row.get("r"))
            while len(rows) <= rnum:
                rows.append([""])  # 1-based; [0] unused
            cells: list[str] = [""]
            for c in row.findall("x:c", NS):
                ref = c.get("r")
                col_letters = "".join(ch for ch in ref if ch.isalpha())
                col_num = 0
                for ch in col_letters:
                    col_num = col_num * 26 + (ord(ch) - 64)
                t = c.get("t")
                v = c.find("x:v", NS)
                inline = c.find("x:is", NS)
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif inline is not None:
                    val = "".join(t.text or "" for t in inline.iter(f"{{{NS['x']}}}t"))
                elif v is not None:
                    val = v.text or ""
                else:
                    val = ""
                while len(cells) <= col_num:
                    cells.append("")
                cells[col_num] = val
            rows[rnum] = cells
        return rows


# --------- TESTS ---------

def test_adv_normalize():
    assert adv_normalize("Κωδ.Πελάτη") == adv_normalize("κωδ.πελατη")
    assert adv_normalize("  ΕΡΜΟΎ  ") == "ερμου"
    assert adv_normalize(None) == ""
    # richText values πρέπει να περνούν πρώτα από to_plain_string
    rt = {"richText": [{"text": "ΑΒ"}, {"text": "Γ"}]}
    assert adv_normalize(to_plain_string(rt)) == "αβγ"


def test_real_info_detects_headers():
    rows = read_sheet_rows(r"c:\Users\U0091\Desktop\Lista\INFO.XLSX", "Street Name Replace")
    rules, warnings = parse_rules(rows)
    # Headers πρέπει να εντοπιστούν (αλλιώς θα είχαμε warning "δεν βρέθηκαν").
    assert not any("δεν βρέθηκαν" in w for w in warnings)
    # Πρέπει να έχουμε warnings για τις rows χωρίς keys, και πιθανώς κάποιους κανόνες.
    assert warnings, "Θα περιμέναμε τουλάχιστον warnings (υπάρχουν rows χωρίς keys)."
    print(f"  real INFO: headers OK, {len(rules)} rules, {len(warnings)} warnings.")
    for r in rules[:5]:
        print(f"     rule @row {r.row}: kwd={r.kwd!r} syn={r.syn!r} "
              f"from={r.from_key!r} → {r.to!r} (spec={r.specificity})")


def make_synthetic_rows(lines: list[list[str]]) -> list[list[str]]:
    """1-based rows/cols."""
    out: list[list[str]] = [[""]]
    for line in lines:
        out.append([""] + line)
    return out


def test_only_customer_code_scoping():
    # Header row 2
    rows = make_synthetic_rows([
        ["Street Name Replace", "", "", ""],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["1001", "", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],
    ])
    rules, w = parse_rules(rows)
    assert len(rules) == 1 and rules[0].specificity == 1
    master = [
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "Α", "Οδός": "ΕΡΜΟΥ"},     # match
        {"Κωδ.Πελάτη": "1002", "Συνεργάτης": "Α", "Οδός": "ΕΡΜΟΥ"},     # ίδιο street, ΑΛΛΟ code → skip
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "Β", "Οδός": "ΣΤΑΔΙΟΥ"},   # ίδιο code, άλλο street → skip
    ]
    result = apply_replacements(master, rules)
    assert result[0]["Οδός"] == "ΠΑΤΗΣΙΩΝ"
    assert result[1]["Οδός"] == "ΕΡΜΟΥ"
    assert result[2]["Οδός"] == "ΣΤΑΔΙΟΥ"
    print("  only-code scoping: OK")


def test_only_partner_scoping():
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["", "ΠΑΠΑΔΟΠΟΥΛΟΣ", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],
    ])
    rules, w = parse_rules(rows)
    assert len(rules) == 1 and rules[0].specificity == 1
    master = [
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "ΠΑΠΑΔΌΠΟΥΛΟΣ", "Οδός": "ερμού"},  # diacritics/case
        {"Κωδ.Πελάτη": "1002", "Συνεργάτης": "ΑΛΛΟΣ",         "Οδός": "ΕΡΜΟΥ"},   # other partner → skip
    ]
    raw_map = build_raw_map_from_rows(master)
    result = apply_replacements(master, rules, raw_master_by_code=raw_map)
    assert result[0]["Οδός"] == "ΠΑΤΗΣΙΩΝ"
    assert result[1]["Οδός"] == "ΕΡΜΟΥ"
    print("  only-partner scoping (με diacritics): OK")


def test_partner_scoping_uses_RAW_not_processed():
    """
    Το κρίσιμο test: το Customer Name Replace αλλάζει ΑΒΑΝΑ→ΔΕΛΤΑ,
    αλλά ο street-rule έχει "Συνεργάτης = ΑΒΑΝΑ" (raw value).
    Το street replacement πρέπει ΠΑΡΑ ΤΑΥΤΑ να εφαρμοστεί, γιατί στο
    ΑΡΧΙΚΟ (raw) master ο Συνεργάτης ήταν ΑΒΑΝΑ.
    """
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["", "ΑΒΑΝΑ", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],  # scope μόνο Συνεργάτης=ΑΒΑΝΑ (raw)
    ])
    rules, _ = parse_rules(rows)
    raw_master = [
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "ΑΒΑΝΑ", "Οδός": "ΕΡΜΟΥ"},
        {"Κωδ.Πελάτη": "2002", "Συνεργάτης": "ΔΕΛΤΑ", "Οδός": "ΕΡΜΟΥ"},  # διαφορετικός raw → skip
    ]
    raw_map = build_raw_map_from_rows(raw_master)
    customer_replace = {adv_normalize("ΑΒΑΝΑ"): "ΔΕΛΤΑ"}  # ΑΒΑΝΑ → ΔΕΛΤΑ στο processed
    result = apply_replacements(raw_master, rules,
                                raw_master_by_code=raw_map,
                                customer_replace_map=customer_replace)
    # Στο processed row 1001: partner έγινε ΔΕΛΤΑ, αλλά scoping βλέπει raw=ΑΒΑΝΑ → match
    assert result[0]["Συνεργάτης"] == "ΔΕΛΤΑ"
    assert result[0]["Οδός"]       == "ΠΑΤΗΣΙΩΝ", result[0]
    # Στο 2002: raw partner=ΔΕΛΤΑ → scoping ΑΒΑΝΑ δεν ταιριάζει → καμία αλλαγή στην Οδός
    assert result[1]["Οδός"] == "ΕΡΜΟΥ"
    print("  raw-partner scoping (πριν το Customer Name Replace): OK")


def test_partner_scoping_NEGATIVE_raw_differs():
    """
    Αντίστροφο: το Customer Name Replace αλλάζει ΔΕΛΤΑ→ΑΒΑΝΑ στο processed,
    αλλά ο street-rule έχει scope "Συνεργάτης = ΑΒΑΝΑ". ΔΕΝ πρέπει να εφαρμοστεί
    γιατί στο raw master ο Συνεργάτης ήταν ΔΕΛΤΑ.
    """
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["", "ΑΒΑΝΑ", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],
    ])
    rules, _ = parse_rules(rows)
    raw_master = [
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "ΔΕΛΤΑ", "Οδός": "ΕΡΜΟΥ"},
    ]
    raw_map = build_raw_map_from_rows(raw_master)
    customer_replace = {adv_normalize("ΔΕΛΤΑ"): "ΑΒΑΝΑ"}  # ΔΕΛΤΑ → ΑΒΑΝΑ (processed θα γίνει ΑΒΑΝΑ)
    result = apply_replacements(raw_master, rules,
                                raw_master_by_code=raw_map,
                                customer_replace_map=customer_replace)
    # Χωρίς raw map, η παλιά λογική θα έβλεπε partner=ΑΒΑΝΑ (post-replace) → λανθασμένο match.
    # Με raw map, scoping βλέπει raw=ΔΕΛΤΑ → no match, Οδός αμετάβλητη.
    assert result[0]["Συνεργάτης"] == "ΑΒΑΝΑ"
    assert result[0]["Οδός"]       == "ΕΡΜΟΥ", f"Δεν έπρεπε να αλλάξει: {result[0]}"
    print("  raw-partner scoping (negative case, πριν το Customer Name Replace): OK")


def test_both_keys_and_priority():
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        # specific (Κωδ+Συν) rule and a broader (only-partner) rule for same street
        ["1001", "ΠΑΠΑΔΟΠΟΥΛΟΣ", "ΕΡΜΟΥ", "SPECIFIC"],
        ["",     "ΠΑΠΑΔΟΠΟΥΛΟΣ", "ΕΡΜΟΥ", "BROAD"],
    ])
    rules, w = parse_rules(rows)
    assert len(rules) == 2
    # Most-specific sorted first
    assert rules[0].specificity == 2 and rules[1].specificity == 1
    master = [
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "ΠΑΠΑΔΟΠΟΥΛΟΣ", "Οδός": "ΕΡΜΟΥ"},  # → SPECIFIC
        {"Κωδ.Πελάτη": "2222", "Συνεργάτης": "ΠΑΠΑΔΟΠΟΥΛΟΣ", "Οδός": "ΕΡΜΟΥ"},  # → BROAD
    ]
    result = apply_replacements(master, rules)
    assert result[0]["Οδός"] == "SPECIFIC"
    assert result[1]["Οδός"] == "BROAD"
    print("  both-keys AND + most-specific wins: OK")


def test_warnings_partial_empty():
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["1001", "", "", "ΠΑΤΗΣΙΩΝ"],          # κενό Από
        ["", "", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],         # κενά και Κωδ και Συν
        ["", "", "", ""],                     # εντελώς κενή → ignore σιωπηλά
    ])
    rules, w = parse_rules(rows)
    assert len(rules) == 0
    assert sum("κενό" in x for x in w) == 1, w
    assert sum("κενά και" in x for x in w) == 1, w
    print("  warnings partial empty + skip all-empty: OK")


def test_exact_match_only():
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["1001", "", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],
    ])
    rules, _ = parse_rules(rows)
    master = [
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "Α", "Οδός": "ΕΡΜΟΥ 12"},  # exact only → skip
        {"Κωδ.Πελάτη": "1001", "Συνεργάτης": "Α", "Οδός": "ΕΡΜΟΥ"},     # exact → match
    ]
    result = apply_replacements(master, rules)
    assert result[0]["Οδός"] == "ΕΡΜΟΥ 12"
    assert result[1]["Οδός"] == "ΠΑΤΗΣΙΩΝ"
    print("  exact match only (όχι substring): OK")


def test_header_on_row1():
    rows = make_synthetic_rows([
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["1001", "", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],
    ])
    rules, _ = parse_rules(rows)
    assert len(rules) == 1
    print("  headers σε row 1 (χωρίς title row): OK")


def test_header_on_row3():
    rows = make_synthetic_rows([
        ["noise"],
        ["more noise", "x"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["1001", "", "ΕΡΜΟΥ", "ΠΑΤΗΣΙΩΝ"],
    ])
    rules, _ = parse_rules(rows)
    assert len(rules) == 1
    print("  headers σε row 3 (με 2 rows θόρυβο): OK")


def test_missing_headers():
    rows = make_synthetic_rows([
        ["Street Name Replace"],
        ["A", "B", "C", "D"],
        ["1", "2", "3", "4"],
    ])
    rules, w = parse_rules(rows)
    assert len(rules) == 0
    assert any("δεν βρέθηκαν" in x for x in w)
    print("  missing-headers → warning no-op: OK")


def test_leading_zeros_codes():
    rows = make_synthetic_rows([
        ["title"],
        ["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"],
        ["0042", "", "ΕΡΜΟΥ", "NEW"],
    ])
    rules, _ = parse_rules(rows)
    master = [
        {"Κωδ.Πελάτη": "0042", "Συνεργάτης": "", "Οδός": "ΕΡΜΟΥ"},  # match
        {"Κωδ.Πελάτη": "42",   "Συνεργάτης": "", "Οδός": "ΕΡΜΟΥ"},  # string != 0042 → skip
    ]
    result = apply_replacements(master, rules)
    assert result[0]["Οδός"] == "NEW"
    assert result[1]["Οδός"] == "ΕΡΜΟΥ"
    print("  leading zeros preserved (string comparison): OK")


def run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"Running {len(tests)} tests:")
    fails = 0
    for t in tests:
        name = t.__name__
        try:
            t()
            print(f"✓ {name}")
        except AssertionError as e:
            fails += 1
            print(f"✗ {name}: AssertionError: {e}")
        except Exception as e:
            fails += 1
            print(f"✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{'ALL PASSED' if fails == 0 else f'{fails} FAILED'}")
    return fails


if __name__ == "__main__":
    raise SystemExit(run_all())
