# -*- coding: utf-8 -*-
"""Test: γραμμές με wrapped κείμενο πρέπει να έχουν ύψος 33, οι υπόλοιπες 25."""
import os
import sys
from openpyxl import load_workbook
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIX = os.path.join(HERE, "fixtures")
INDEX_URL = "file:///" + os.path.join(ROOT, "index.html").replace("\\", "/")
MASTER_PATH = os.path.join(FIX, "master.xlsx")
INFO_PATH = os.path.join(FIX, "INFO.xlsx")
DOWNLOAD_PATH = os.path.join(FIX, "_downloaded_height.xlsx")


def export():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(accept_downloads=True)
        page = ctx.new_page()
        logs = []
        page.on("console", lambda msg: logs.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda exc: logs.append(f"[pageerror] {exc}"))
        try:
            page.goto(INDEX_URL)
            page.wait_for_selector("#masterInput")
            page.set_input_files("#masterInput", MASTER_PATH)
            page.set_input_files("#infoInput", INFO_PATH)
            page.wait_for_selector("#exportFinalExcelBtn", timeout=60000, state="attached")
            with page.expect_download(timeout=30000) as dl_info:
                page.click("#exportFinalExcelBtn")
            dl = dl_info.value
            if os.path.exists(DOWNLOAD_PATH):
                os.remove(DOWNLOAD_PATH)
            dl.save_as(DOWNLOAD_PATH)
        finally:
            with open(os.path.join(FIX, "_console_height.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(logs))
            browser.close()


def run():
    export()
    wb = load_workbook(DOWNLOAD_PATH)
    errors = []
    for sname in wb.sheetnames:
        ws = wb[sname]
        # header row index: αν 1η γραμμή έχει 1 μη-κενό κελί → header στη 2η
        first_non_empty = sum(
            1 for c in range(1, ws.max_column + 1)
            if ws.cell(1, c).value not in (None, "") and str(ws.cell(1, c).value).strip() != ""
        )
        header_row = 2 if first_non_empty == 1 else 1
        print(f"\n=== {sname} (header_row={header_row}) ===")
        # Ετικέτες sub-table headers (το "Πελάτες ανά Περιοχή" έχει πολλούς πίνακες)·
        # τέτοιες γραμμές δεν είναι data rows και παραλείπονται.
        SUBHEADER_LABELS = {"Συνεργάτης", "Κωδ.Πελάτη", "Οδός", "Πόλη", "ID_Παραγγελίας"}
        for r in range(header_row + 1, ws.max_row + 1):
            row_vals = {str(ws.cell(r, c).value).strip() for c in range(1, ws.max_column + 1) if ws.cell(r, c).value not in (None, "")}
            # Παράλειψη sub-table header/title rows
            if row_vals & SUBHEADER_LABELS:
                continue
            h = ws.row_dimensions[r].height
            # έλεγξε αν κάποιο κελί έχει wrap + μακρύ κείμενο
            wrapped = False
            longest = ""
            for c in range(1, ws.max_column + 1):
                cell = ws.cell(r, c)
                val = cell.value
                if val is None:
                    continue
                s = str(val)
                if cell.alignment and cell.alignment.wrap_text:
                    width = ws.column_dimensions[cell.column_letter].width or 8
                    # Ίδιο heuristic με το index.html: φυσικό best-fit πλάτος
                    # (len * 1.15 + 2) > πλάτος στήλης → wrap.
                    natural = len(s) * 1.15 + 2
                    if "\n" in s or natural > width:
                        wrapped = True
                        if len(s) > len(longest):
                            longest = s
            if wrapped:
                # Οι wrapped γραμμές ΠΡΕΠΕΙ να έχουν ύψος 33.
                if h != 33:
                    errors.append(f"{sname} row {r}: wrapped αλλά height={h} (αναμενόταν 33) longest={longest!r}")
                else:
                    print(f"  row {r}: height={h} (wrapped, longest={longest!r})")
            else:
                # Οι μη-wrapped γραμμές ΔΕΝ πρέπει να γίνουν 33 (μένουν στο base ύψος του φύλλου).
                if h == 33:
                    errors.append(f"{sname} row {r}: ΔΕΝ είναι wrapped αλλά height=33 (false positive)")

    # Πρέπει να βρεθεί ΤΟΥΛΑΧΙΣΤΟΝ μία wrapped γραμμή ύψους 33 (αλλιώς το test δεν ελέγχει τίποτα)
    any_33 = False
    for sname in wb.sheetnames:
        ws = wb[sname]
        for r in range(1, ws.max_row + 1):
            if ws.row_dimensions[r].height == 33:
                any_33 = True
    if not any_33:
        errors.append("Καμία γραμμή δεν έχει ύψος 33 — ο μηχανισμός autoHeight δεν ενεργοποιήθηκε.")

    if errors:
        print("\nFAIL:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("\nPASS — όλες οι wrapped γραμμές έχουν ύψος 33, οι υπόλοιπες 25.")


if __name__ == "__main__":
    run()
