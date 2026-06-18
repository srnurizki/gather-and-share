# <<<./ Import Libraries
import pandas as pd
import streamlit as st

from src.schemas import BillResult
from src.utils.export_utils import bill_to_csv

# <<<./ Render Summary
def render_split_summary():
    raw = st.session_state.get("bill")
    if raw is None:
        return
    bill = BillResult.model_validate(raw)

    if bill is None:
        return

    st.subheader('Split Summary')

    for result in bill.results:
        with st.expander(
            f'**{result.member}** — IDR {result.total_owed:.0f}',
            expanded=True):

            items_df = pd.DataFrame([
                {
                    'Item': item.name,
                    'Qty': item.quantity,
                    'Unit Price (IDR)': item.unit_price,
                    'Total (IDR)': item.total_price}
                for item in result.assigned_items
            ])
            st.dataframe(items_df, use_container_width=True, hide_index=True)

            col_sub, col_charge, col_total = st.columns(3)
            with col_sub:
                st.metric('Item Subtotal', f'IDR {result.item_subtotal:,.0f}')
            with col_charge:
                st.metric('Charge Share', f'IDR {result.charge_share:,.0f}')
            with col_total:
                st.metric('Total Owed', f'IDR {result.total_owed:,.0f}')

    st.divider()

    col_collected, col_receipt = st.columns(2)
    with col_collected:
        st.metric('Total Collected', f'IDR {bill.total_collected:,.0f}')
    with col_receipt:
        st.metric('Receipt Total', f'IDR {bill.receipt.total:,.0f}')

    if bill.is_split_balanced:
        st.success('Split Balanced')
    else:
        st.error('Split is not balanced. Please review item assignments')

    # <<<./ Download CSV
    st.download_button(
        label='Download Bill Summary',
        data=bill_to_csv(bill),
        file_name='split_summary.csv',
        mime='text/csv',
        use_container_width=True,
        key='download_split_csv')