# <<<./ Import Libraries
import pandas as pd
from src.schemas import BillResult

# <<<./ Convert Bill to CSV
def bill_to_csv(bill: BillResult):
    rows = []

    # <<<./ Store Each Member-Assigned Item to Each Row
    for result in bill.results:
        for item in result.assigned_items:
            rows.append({
                'Member': result.member,
                'Item': item.name,
                'Qty': item.quantity,
                'Unit Price (IDR)': item.unit_price,
                'Item Total (IDR)': item.total_price
            })

        # <<<./ Member Subtotal Row
        rows.append({
            'Member': result.member,
            'Item': 'SUBTOTAL',
            'Qty': '',
            'Unit Price (IDR)': '',
            'Item Total (IDR)': result.item_subtotal
        })

        # <<<./ Member Charge Share Row
        rows.append({
            'Member': result.member,
            'Item': 'CHARGE SHARE',
            'Qty': '',
            'Unit Price (IDR)': '',
            'Item Total (IDR)': result.charge_share
        })

        # <<<./ Member Total Owed Row
        rows.append({
            'Member': result.member,
            'Item': 'TOTAL OWED',
            'Qty': '',
            'Unit Price (IDR)': '',
            'Item Total (IDR)': result.total_owed
        })

    # <<<./ Convert to CSV
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')