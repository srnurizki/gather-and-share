# <<<./ Import Libraries
import pandas as pd
import streamlit as st

from src.schemas import ItemAssignment, Receipt, ReceiptItem
from src.splitter.calculator import BillCalculator, CalculationError

# <<<./ Convert Receipt Data to DataFrame
def receipt_to_df(receipt: Receipt):
    return pd.DataFrame([
        {'Name': item.name,
         'Qty': item.quantity,
         'Unit Price (IDR)': item.unit_price,
         'Total (IDR)': item.total_price}
    for item in receipt.items])

# <<<./ Convert DataFrame to Items
def df_to_items(df: pd.DataFrame):
    items = []
    for _, row in df.iterrows():
        try:
            items.append(ReceiptItem(
                name=str(row['Name']),
                quantity=float(row['Qty']),
                unit_price=float(row['Unit Price (IDR)']),
                total_price=float(row['Total (IDR)'])

            ))
        except Exception:
            pass
    return items

# <<<./ Render Receipt Editor
def render_receipt_editor():
    raw = st.session_state.get("receipt")
    if raw is None:
        return
    receipt = Receipt.model_validate(raw)
    members: list = st.session_state.get('members', [])
    if receipt is None:
        return
    if not members:
        st.info('Add members above before assigning items')
        return

    # <<<./ User Phase: Reviewing Data
    st.subheader('Review & Edit Receipt Data')
    st.caption('Double-check any AI extraction errors before assigning items')

    edited_df = st.data_editor(
        receipt_to_df(receipt),
        use_container_width=True,
        num_rows='fixed',
        column_config={
            'Name': st.column_config.TextColumn(
                'Item Name', width='large'),
            'Qty': st.column_config.NumberColumn(
                'Qty', min_value=0.01, format='%.2f'),
            'Unit Price (IDR)': st.column_config.NumberColumn(
                'Unit Price (IDR)', min_value=0.01, format='%,.0f'),
            'Total (IDR)': st.column_config.NumberColumn(
                'Total (IDR)', min_value=0, format='%,.0f')
            }
        )

    col_sub, col_add, col_total = st.columns(3)
    with col_sub:
        st.metric('Subtotal', f'IDR {receipt.subtotal:,.0f}')
    with col_add:
        label = ', '.join(c.label for c in receipt.additional_charges) or '-'
        st.metric('Charges', f'IDR {receipt.total_additional_charges:,.0f}', help=label)
    with col_total:
        st.metric('Total', f'IDR {receipt.total:,.0f}')

    # <<<./ User Phase: Assigning Items
    st.subheader('Assign Items to Participant')

    assignments = []
    all_assigned = True

    for i, row in edited_df.iterrows():
        selected = st.multiselect(
            label=f"{row['Name']} — IDR {row['Total (IDR)']:,.0f}",
            options=members,
            key=f'assign_item_{i}')

        if selected:
            assignments.append(ItemAssignment(item_index=i, assigned_to=selected))
        else:
            all_assigned = False

    if not all_assigned:
        st.warning('All items must be assigned before calculating')

    # <<<./ Calculate Split
    if st.button(
        'Calculate Split',
        disabled=not all_assigned,
        type='primary',
        use_container_width=True):

        items = df_to_items(edited_df)
        if not items:
            st.error('No valid items found. Please check the receipt data')
            return

        updated_receipt = receipt.model_copy(update={"items": items})

        try:
            bill = BillCalculator().split(updated_receipt, assignments, members)
            st.session_state.bill = bill.model_dump()
            st.session_state.assignments = assignments
            st.rerun()
        except CalculationError as e:
            st.error(f'Calculation Failed: {e}')
