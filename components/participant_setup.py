# <<<./ Import Libraries
import streamlit as st

# <<<./ Initialize State
def init_state():
    if 'members' not in st.session_state:
        st.session_state.members = []

# <<<./ Reset State
def reset_split_state():
    st.session_state.assignments = []
    st.session_state.bill = None

# <<<./ Render Input
def render_participant_setup():
    init_state()

    st.subheader('Add Members')

    col_input, col_btn = st.columns([4, 1])

    with col_input:
        new_name = st.text_input(
            label='Member name',
            key='new_member_input',
            placeholder='e.g. Lamine',
            label_visibility='collapsed')

    with col_btn:
        add_clicked = st.button('Add', use_container_width=True)

    if add_clicked:
        name = new_name.strip()
        if not name:
            st.warning('Name cannot be empty')
        elif name in st.session_state.members:
            st.warning(f'{name} already exists')
        else:
            st.session_state.members.append(name)
            reset_split_state()
            del st.session_state['new_member_input']
            st.rerun()

    if not st.session_state.members:
        st.caption('No members added yet')
        return

    for i, name in enumerate(st.session_state.members):
        col_name, col_remove = st.columns([5, 1])
        with col_name:
            st.write(f'**{i + 1}.** {name}')
        with col_remove:
            if st.button('X', key=f'remove_member_{i}', use_container_width=True):

                st.session_state.members.pop(i)
                reset_split_state()
                st.rerun()
