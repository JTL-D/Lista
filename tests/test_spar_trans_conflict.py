"""
Python port of SPAR↔TRANS conflict detection logic (index.html).

A conflict is a contradiction in the INFO.xlsx where the same (customer, branch)
is claimed by both SPAR (our truck) and TRANS (third-party carrier).

Rules:
  - Specific conflict : SPAR (Κωδ, Οδός) AND TRANS row with same (Κωδ, Οδός)
                        and non-empty Συνεργάτης.
  - Wildcard conflict : SPAR wildcard (Κωδ only) AND TRANS row with same Κωδ,
                        non-empty Συνεργάτης AND non-empty Οδός.
  - Normalization: NFD + strip diacritics + strip whitespace + lowercase.
"""
import unicodedata
import sys


def normalize(val):
    if val is None:
        return ''
    s = str(val)
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = ''.join(ch for ch in s if not ch.isspace())
    return s.lower()


def detect_conflicts(spar_wildcard_by_code, spar_specific_by_code_odos, trans_rows):
    """
    spar_wildcard_by_code     : dict nCode -> region
    spar_specific_by_code_odos: dict "nCode|nOdos" -> region
    trans_rows                : list of dicts with keys 'code','partner','odos'
    Returns: deduplicated list of conflict dicts.
    """
    conflicts = []
    for t in trans_rows:
        code = (t.get('code') or '').strip()
        partner = (t.get('partner') or '').strip()
        odos = (t.get('odos') or '').strip()
        if not code or not partner:
            continue
        n_code = normalize(code)
        n_odos = normalize(odos)
        # specific
        if n_odos:
            key = n_code + '|' + n_odos
            if key in spar_specific_by_code_odos:
                conflicts.append({
                    'type': 'specific',
                    'code': code, 'odos': odos, 'transPartner': partner,
                    'sparRegion': spar_specific_by_code_odos[key],
                })
                continue
        # wildcard (needs non-empty odos in TRANS)
        if n_odos and n_code in spar_wildcard_by_code:
            conflicts.append({
                'type': 'wildcard',
                'code': code, 'odos': odos, 'transPartner': partner,
                'sparRegion': spar_wildcard_by_code[n_code],
            })
    # dedupe on (code, odos, partner)
    seen = set()
    out = []
    for c in conflicts:
        k = (normalize(c['code']), normalize(c['odos']), normalize(c['transPartner']))
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    return out


# ---------------- Tests ----------------
def _assert(cond, name):
    if not cond:
        print(f'FAIL: {name}')
        sys.exit(1)
    print(f'OK:   {name}')


def test_specific_conflict_detected():
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [{'code': '123', 'partner': 'A', 'odos': 'ΕΡΜΟΥ 5'}]
    c = detect_conflicts({}, spar_spec, trans)
    _assert(len(c) == 1 and c[0]['type'] == 'specific',
            'specific conflict detected')


def test_wildcard_conflict_detected():
    spar_wild = {'123': 'ΘΕΣΣΑΛΟΝΙΚΗ'}
    trans = [{'code': '123', 'partner': 'A', 'odos': 'ΕΡΜΟΥ 5'}]
    c = detect_conflicts(spar_wild, {}, trans)
    _assert(len(c) == 1 and c[0]['type'] == 'wildcard',
            'wildcard conflict detected')


def test_wildcard_needs_nonempty_odos_in_trans():
    spar_wild = {'123': 'ΘΕΣΣΑΛΟΝΙΚΗ'}
    trans = [{'code': '123', 'partner': 'A', 'odos': ''}]
    c = detect_conflicts(spar_wild, {}, trans)
    _assert(len(c) == 0, 'wildcard w/ empty TRANS odos → no conflict')


def test_trans_needs_nonempty_partner():
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [{'code': '123', 'partner': '', 'odos': 'ΕΡΜΟΥ 5'}]
    c = detect_conflicts({}, spar_spec, trans)
    _assert(len(c) == 0, 'empty TRANS partner → skip row')


def test_no_conflict_when_no_spar():
    trans = [{'code': '123', 'partner': 'A', 'odos': 'ΕΡΜΟΥ 5'}]
    c = detect_conflicts({}, {}, trans)
    _assert(len(c) == 0, 'empty SPAR → no conflict')


def test_specific_wins_over_wildcard_on_same_row():
    # Both wildcard and specific exist; TRANS matches specific → reported as specific only
    spar_wild = {'123': 'ΘΕΣΣΑΛΟΝΙΚΗ'}
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [{'code': '123', 'partner': 'A', 'odos': 'ΕΡΜΟΥ 5'}]
    c = detect_conflicts(spar_wild, spar_spec, trans)
    _assert(len(c) == 1 and c[0]['type'] == 'specific',
            'specific conflict reported (not wildcard) when both exist')


def test_wildcard_conflict_on_other_street():
    # SPAR wildcard exists, TRANS row has DIFFERENT street (no specific match) → wildcard conflict
    spar_wild = {'123': 'ΘΕΣΣΑΛΟΝΙΚΗ'}
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [{'code': '123', 'partner': 'A', 'odos': 'ΤΣΙΜΙΣΚΗ 10'}]
    c = detect_conflicts(spar_wild, spar_spec, trans)
    _assert(len(c) == 1 and c[0]['type'] == 'wildcard',
            'wildcard conflict on street not covered by specific')


def test_diacritics_tolerance():
    spar_spec = {'123|αγιουιωαννη': 'X'}
    trans = [{'code': '123', 'partner': 'A', 'odos': 'Αγίου  Ιωάννη'}]
    c = detect_conflicts({}, spar_spec, trans)
    _assert(len(c) == 1, 'diacritics+whitespace tolerant')


def test_dedupe_identical_rows():
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [
        {'code': '123', 'partner': 'A', 'odos': 'ΕΡΜΟΥ 5'},
        {'code': '123', 'partner': 'A', 'odos': 'ΕΡΜΟΥ 5'},
    ]
    c = detect_conflicts({}, spar_spec, trans)
    _assert(len(c) == 1, 'duplicate TRANS rows deduped in output')


def test_conflict_even_when_regions_match():
    # Same region in SPAR and (implicitly) TRANS → still a conflict
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [{'code': '123', 'partner': 'ΜΕΤΑΦΟΡΙΚΗ Α', 'odos': 'ΕΡΜΟΥ 5'}]
    c = detect_conflicts({}, spar_spec, trans)
    _assert(len(c) == 1, 'conflict reported regardless of region equality')


def test_unrelated_rows_not_flagged():
    spar_spec = {'123|ερμου5': 'ΚΕΝΤΡΟ'}
    trans = [{'code': '999', 'partner': 'A', 'odos': 'ΦΑΝΤΑΣΤΙΚΗ 1'}]
    c = detect_conflicts({}, spar_spec, trans)
    _assert(len(c) == 0, 'unrelated TRANS row not flagged')


if __name__ == '__main__':
    test_specific_conflict_detected()
    test_wildcard_conflict_detected()
    test_wildcard_needs_nonempty_odos_in_trans()
    test_trans_needs_nonempty_partner()
    test_no_conflict_when_no_spar()
    test_specific_wins_over_wildcard_on_same_row()
    test_wildcard_conflict_on_other_street()
    test_diacritics_tolerance()
    test_dedupe_identical_rows()
    test_conflict_even_when_regions_match()
    test_unrelated_rows_not_flagged()
    print('\nALL SPAR↔TRANS CONFLICT TESTS PASSED')
