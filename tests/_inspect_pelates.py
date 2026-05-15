# -*- coding: utf-8 -*-
import os, openpyxl
base = r'C:\Users\U0091\Desktop\Lista'
files = [f for f in os.listdir(base) if f.lower().endswith('.xlsx') and '15-05-26' in f and not f.startswith('~$')]
path = os.path.join(base, files[0])
wb = openpyxl.load_workbook(path)

yellow_codes = {'802769750','1185','998716895','800156819','039035330','800558765','2956'}

for sname in ['Πελατες Ημερας', 'Πρακτορεια Ημερας', 'Μόνο Πρακτορεία']:
    if sname not in wb.sheetnames:
        print(sname, 'MISSING'); continue
    ws = wb[sname]
    # Find header row and Κωδ.Πελάτη column index
    header_row = None
    code_col = None
    partner_col = None
    for r in range(1, min(6, ws.max_row+1)):
        for c in range(1, ws.max_column+1):
            v = ws.cell(r,c).value
            if v and 'Κωδ.Πελάτη' in str(v):
                header_row = r; code_col = c
            if v and 'Συνεργάτης' in str(v):
                partner_col = c
        if header_row:
            break
    print(f'--- {sname} (header_row={header_row}, code_col={code_col}, partner_col={partner_col}) ---')
    if not header_row:
        continue
    for r in range(header_row+1, ws.max_row+1):
        code = str(ws.cell(r, code_col).value or '').strip()
        if code in yellow_codes:
            partner = str(ws.cell(r, partner_col).value or '').strip() if partner_col else ''
            print(f'  row {r}: code={code}, partner={partner!r}')
