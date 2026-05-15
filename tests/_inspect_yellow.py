# -*- coding: utf-8 -*-
import os, glob, openpyxl
base = r'C:\Users\U0091\Desktop\Lista'
files = [f for f in os.listdir(base) if f.lower().endswith('.xlsx') and '15-05-26' in f and not f.startswith('~$')]
print('Found:', files)
path = os.path.join(base, files[0])
wb = openpyxl.load_workbook(path)
print('Sheets:', wb.sheetnames)
target = None
for s in wb.sheetnames:
    if 'εριοχ' in s or 'εριοχ'.upper() in s.upper():
        target = s; break
print('Target:', target)
ws = wb[target]
print('Dims:', ws.max_row, ws.max_column)
print('Freeze:', ws.freeze_panes)
for r in range(1, ws.max_row+1):
    row_vals = [ws.cell(r,c).value for c in range(1,6)]
    fills = []
    for c in range(1,6):
        cell = ws.cell(r,c)
        f = cell.fill
        rgb = None
        if f and f.fgColor:
            rgb = f.fgColor.rgb
        fills.append(rgb)
    print(r, row_vals, fills)
