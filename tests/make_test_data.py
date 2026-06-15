"""Δημιουργεί συνθετικά αρχεία master.xlsx + INFO.xlsx για integration test
του φύλλου 'Πελάτες ανά Περιοχή'.

Σενάρια:
  100 ALPHA  → καθαρό intra (Αττική)
  200 BETA   → μόνο ΤΡ (RETAIL hit)  → intra
  300 GAMMA  → μόνο TRANS            → Με Μεταφορική
  400 DELTA  → μόνο TRANS            → Με Μεταφορική
  500 EPS    → ΤΡ + TRANS            → Με Μεταφορική
  600 ZETA   → μόνο SPAR/Bazaar      → Με Μεταφορική
  700 ETA    → Bazaar + TRANS (conflict) → Με Μεταφορική (+ warning)
"""
import os
from openpyxl import Workbook

HERE = os.path.dirname(__file__)
OUT_DIR = os.path.join(HERE, "fixtures")
os.makedirs(OUT_DIR, exist_ok=True)


def build_master(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet"
    ws.append(["Κωδ.Πελάτη", "Συνεργάτης", "Οδός", "Πόλη"])
    ws.append(["100", "ALPHA",   "ODOS A", "ΑΘΗΝΑ"])
    ws.append(["200", "BETA",    "ODOS B", "ΠΕΙΡΑΙΑΣ"])
    ws.append(["300", "GAMMA",   "ODOS C", "ΘΕΣΣΑΛΟΝΙΚΗ"])
    ws.append(["400", "DELTA",   "ODOS D", "ΛΑΡΙΣΑ"])
    ws.append(["500", "EPSILON", "ODOS E", "ΠΑΤΡΑ"])
    ws.append(["600", "ZETA",    "ODOS F", "ΗΡΑΚΛΕΙΟ"])
    ws.append(["700", "ETA",     "ODOS G", "ΚΕΡΚΥΡΑ"])
    wb.save(path)


def build_info(path):
    wb = Workbook()
    # RETAIL — title row + header row + data
    ws = wb.active
    ws.title = "RETAIL"
    ws.append(["Πελατες της Retail & More"])
    ws.append(["Κωδ.Πελάτη", "Συνεργάτης(μονο πληφοριακά)", "Οδός(μονο πληφοριακά)", "Περιοχή(μονο πληφοριακά)"])
    ws.append(["200", "BETA",    "", "ΑΤΤΙΚΗ"])
    ws.append(["500", "EPSILON", "", "ΑΧΑΪΑ"])

    # SPAR
    ws = wb.create_sheet("SPAR")
    ws.append(["ΠΕΛΑΤΕΣ SPAR"])
    ws.append(["Κωδ.Πελάτη", "Συνεργάτης(μονο πληφοριακά)", "Οδός", "Περιοχή"])
    ws.append(["600", "ZETA", "",       "BAZAAR-1"])  # wildcard
    ws.append(["700", "ETA",  "ODOS G", "BAZAAR-2"])  # specific (επίσης TRANS παρακάτω)

    # TRANS — single header row (όχι title)
    ws = wb.create_sheet("TRANS")
    ws.append([
        "Κωδ.Πελάτη", "Συνεργάτης", "Υποκατάστημα(Οδός)", "Περιοχή",
        "Μεταφορική", "Διεύθυνση Μετ", "Τύπος Φορτίου", "Μέρες",
        "Τηλέφωνο 1", "Τηλέφωνο 2"
    ])
    ws.append(["300", "GAMMA",   "ODOS C", "ΜΑΚΕΔΟΝΙΑ ΘΕΣΣΑΛΟΝΙΚΗ ΠΕΡΙΟΧΗ ΤΕΣΤ ΜΑΚΡΥ", "ΜΕΤΑΦ Α", "ΟΔΟΣ 1", "ΞΗΡΟ", "", "", ""])
    # Borderline Μεταφορική (length ~20 < 21.71): το παλιό heuristic length>width
    # ΔΕΝ θα το έπιανε, αλλά το Excel το σπάει — πρέπει να γίνει height 33.
    ws.append(["400", "DELTA",   "ODOS D", "ΘΕΣΣΑΛΙΑ",  "ΜΕΤΑΦΟΡΙΚΗ ΑΦΟΙ ΠΑΠΑΣ", "ΟΔΟΣ 2", "ΞΗΡΟ", "", "", ""])
    ws.append(["500", "EPSILON", "ODOS E", "ΑΧΑΪΑ",     "ΜΕΤΑΦ Γ", "ΟΔΟΣ 3", "ΞΗΡΟ", "", "", ""])
    # ΣΗΜ.: ο κωδ.700 δεν τίθεται στο TRANS — ο upstream validator απαγορεύει
    # SPAR↔TRANS conflict (ίδιος Κωδ.Πελάτη και στα δύο φύλλα). Άρα δεν είναι
    # δυνατό να αναπαραχθεί Bazaar+TRANS μέσω INFO. Το κρατάμε μόνο ως Bazaar.

    # Customer Name Replace
    ws = wb.create_sheet("Customer Name Replace")
    ws.append(["Customer Name Replace"])
    ws.append(["Από", "Σε"])

    # Street Name Replace
    ws = wb.create_sheet("Street Name Replace")
    ws.append(["Street Name Replace"])
    ws.append(["Κωδ.Πελάτη", "Συνεργάτης", "Από", "Σε"])

    # BlackList Customers
    ws = wb.create_sheet("BlackList Customers")
    ws.append(["BlackList Customers"])
    ws.append(["Κωδ.Πελάτη", "Συνεργάτης", "Οδός"])

    wb.save(path)


if __name__ == "__main__":
    master_path = os.path.join(OUT_DIR, "master.xlsx")
    info_path = os.path.join(OUT_DIR, "INFO.xlsx")
    build_master(master_path)
    build_info(info_path)
    print("Wrote:", master_path)
    print("Wrote:", info_path)
