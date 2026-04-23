"""
Python port of SPAR lookup logic for regression testing.

Matches the JS in index.html:
  - sparWildcardByCode     : Κωδ only      → applies to all rows of that code
  - sparSpecificByCodeOdos : Κωδ + Οδός    → applies only to exact row
  - Priority on lookup: specific wins over wildcard.
  - Strict error on duplicate (Κωδ, Οδός) or duplicate wildcard Κωδ with different Περιοχή.
  - Normalization: NFD + strip diacritics + remove all whitespace + lowercase.
"""
import unicodedata


def normalize(val):
    if val is None:
        return ''
    s = str(val)
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = ''.join(ch for ch in s if not ch.isspace())
    return s.lower()


class SparDuplicateError(Exception):
    pass


def build_spar_maps(spar_rows):
    """
    spar_rows: list of dicts with keys 'code', 'odos', 'region'.
    Returns (wildcard_by_code, specific_by_code_odos).
    Raises SparDuplicateError on conflicting duplicates.
    """
    wildcard = {}
    specific = {}
    for row in spar_rows:
        code = (row.get('code') or '').strip()
        region = (row.get('region') or '').strip()
        odos = (row.get('odos') or '').strip()
        if not code or not region:
            continue
        n_code = normalize(code)
        n_odos = normalize(odos)
        if n_odos:
            key = n_code + '|' + n_odos
            if key in specific and specific[key] != region:
                raise SparDuplicateError(
                    f'Duplicate specific rule: Κωδ={code} Οδός={odos} → '
                    f'"{specific[key]}" vs "{region}"'
                )
            specific[key] = region
        else:
            if n_code in wildcard and wildcard[n_code] != region:
                raise SparDuplicateError(
                    f'Duplicate wildcard rule: Κωδ={code} → '
                    f'"{wildcard[n_code]}" vs "{region}"'
                )
            wildcard[n_code] = region
    return wildcard, specific


def spar_lookup(code, odos, wildcard, specific):
    """Returns bazaar region or '' for a master row."""
    if not code:
        return ''
    n_code = normalize(code)
    n_odos = normalize(odos)
    if n_odos:
        key = n_code + '|' + n_odos
        if key in specific:
            return specific[key]
        if n_code in wildcard:
            return wildcard[n_code]
        return ''
    # empty master Οδός → only wildcard can match
    return wildcard.get(n_code, '')


# ---------------- Tests ----------------
import sys


def _assert(cond, name):
    if not cond:
        print(f'FAIL: {name}')
        sys.exit(1)
    print(f'OK:   {name}')


def test_wildcard_only():
    rows = [{'code': '123', 'odos': '', 'region': 'ΘΕΣΣΑΛΟΝΙΚΗ'}]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'ΕΡΜΟΥ 5', w, s) == 'ΘΕΣΣΑΛΟΝΙΚΗ',
            'wildcard matches any street')
    _assert(spar_lookup('123', '', w, s) == 'ΘΕΣΣΑΛΟΝΙΚΗ',
            'wildcard matches empty street')
    _assert(spar_lookup('999', 'ΕΡΜΟΥ 5', w, s) == '',
            'wildcard does not leak to other codes')


def test_specific_only():
    rows = [{'code': '123', 'odos': 'ΕΡΜΟΥ 5', 'region': 'ΚΕΝΤΡΟ'}]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'ΕΡΜΟΥ 5', w, s) == 'ΚΕΝΤΡΟ',
            'specific hits exact match')
    _assert(spar_lookup('123', 'ΤΣΙΜΙΣΚΗ 10', w, s) == '',
            'specific does not match other streets (no wildcard)')
    _assert(spar_lookup('123', '', w, s) == '',
            'specific does not match empty street (no wildcard)')


def test_coexistence_specific_wins():
    rows = [
        {'code': '123', 'odos': '',        'region': 'ΘΕΣΣΑΛΟΝΙΚΗ'},
        {'code': '123', 'odos': 'ΕΡΜΟΥ 5', 'region': 'ΚΕΝΤΡΟ'},
    ]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'ΕΡΜΟΥ 5', w, s) == 'ΚΕΝΤΡΟ',
            'specific wins over wildcard')
    _assert(spar_lookup('123', 'ΤΣΙΜΙΣΚΗ 10', w, s) == 'ΘΕΣΣΑΛΟΝΙΚΗ',
            'other streets fall back to wildcard')
    _assert(spar_lookup('123', '', w, s) == 'ΘΕΣΣΑΛΟΝΙΚΗ',
            'empty street → wildcard')


def test_no_match():
    w, s = build_spar_maps([])
    _assert(spar_lookup('123', 'ΕΡΜΟΥ 5', w, s) == '', 'empty SPAR → empty')


def test_diacritics_and_whitespace():
    rows = [{'code': '123', 'odos': 'Αγίου  Ιωάννη', 'region': 'ΠΕΡ'}]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'αγιου ιωαννη', w, s) == 'ΠΕΡ',
            'diacritics+whitespace tolerant')


def test_duplicate_specific_conflict_raises():
    rows = [
        {'code': '123', 'odos': 'ΕΡΜΟΥ 5', 'region': 'ΚΕΝΤΡΟ'},
        {'code': '123', 'odos': 'ΕΡΜΟΥ 5', 'region': 'ΔΥΤΙΚΟ'},
    ]
    try:
        build_spar_maps(rows)
    except SparDuplicateError:
        print('OK:   duplicate specific raises')
        return
    print('FAIL: duplicate specific should have raised')
    sys.exit(1)


def test_duplicate_specific_same_region_ok():
    rows = [
        {'code': '123', 'odos': 'ΕΡΜΟΥ 5', 'region': 'ΚΕΝΤΡΟ'},
        {'code': '123', 'odos': 'ΕΡΜΟΥ 5', 'region': 'ΚΕΝΤΡΟ'},
    ]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'ΕΡΜΟΥ 5', w, s) == 'ΚΕΝΤΡΟ',
            'duplicate specific with same region is OK')


def test_duplicate_wildcard_conflict_raises():
    rows = [
        {'code': '123', 'odos': '', 'region': 'ΘΕΣΣΑΛΟΝΙΚΗ'},
        {'code': '123', 'odos': '', 'region': 'ΑΘΗΝΑ'},
    ]
    try:
        build_spar_maps(rows)
    except SparDuplicateError:
        print('OK:   duplicate wildcard raises')
        return
    print('FAIL: duplicate wildcard should have raised')
    sys.exit(1)


def test_orphan_spar_row_silent():
    # SPAR row with no matching master row → no lookup happens, no error.
    rows = [{'code': '999', 'odos': 'ΦΑΝΤΑΣΤΙΚΗ 1', 'region': 'ΟΥΤΟΠΙΑ'}]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'ΕΡΜΟΥ 5', w, s) == '',
            'orphan SPAR row does not affect other masters')


def test_partial_coverage_example_from_spec():
    """
    User spec example:
      SPAR: (Κωδ=123, Οδός=Α), (Κωδ=123, Οδός=Β)
      Master: (123,Α), (123,Β), (123,Γ)
      Expected: Α→region, Β→region, Γ→''
    """
    rows = [
        {'code': '123', 'odos': 'Α', 'region': 'Ρ1'},
        {'code': '123', 'odos': 'Β', 'region': 'Ρ2'},
    ]
    w, s = build_spar_maps(rows)
    _assert(spar_lookup('123', 'Α', w, s) == 'Ρ1', 'partial: Α hits')
    _assert(spar_lookup('123', 'Β', w, s) == 'Ρ2', 'partial: Β hits')
    _assert(spar_lookup('123', 'Γ', w, s) == '', 'partial: Γ does NOT hit')


if __name__ == '__main__':
    test_wildcard_only()
    test_specific_only()
    test_coexistence_specific_wins()
    test_no_match()
    test_diacritics_and_whitespace()
    test_duplicate_specific_conflict_raises()
    test_duplicate_specific_same_region_ok()
    test_duplicate_wildcard_conflict_raises()
    test_orphan_spar_row_silent()
    test_partial_coverage_example_from_spec()
    print('\nALL SPAR TESTS PASSED')
