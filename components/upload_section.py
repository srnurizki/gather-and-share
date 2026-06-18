# <<<./ Import Libraries
import streamlit as st
from src.utils.image_utils import load_image

# <<<./ Initialize Session State
def init_session_state():
    defaults = {
        'image': None,
        'receipt': None,
        'assignments': [],
        'bill': None,
        'upload_id': None}

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# <<<./ Reset State
def reset_downstream():
    st.session_state.receipt = None
    st.session_state.assignments = []
    st.session_state.bill = None

# <<<./ Render Upload
def render_upload_section():
    init_session_state()
    st.subheader('Upload Receipt')

    # <<<./ Upload Instruction
    uploaded_file = st.file_uploader(
        label='Upload receipt image',
        type=['jpg', 'jpeg', 'png', 'webp'],
        label_visibility='collapsed')

    if uploaded_file is None:
        if st.session_state.image is not None:
            st.session_state.image = None
            st.session_state.upload_id = None
            reset_downstream()
        st.info('Upload a receipt image to get started')
        return

    # <<<./ Load Image
    if st.session_state.upload_id != uploaded_file.file_id:
        try:
            image = load_image(uploaded_file)
        except ValueError as e:
            st.error(f'Cannot open image: {e}')
            return

        st.session_state.image = image
        st.session_state.upload_id = uploaded_file.file_id
        reset_downstream()

    # <<<./ Show Image
    st.image(
        st.session_state.image,
        caption=uploaded_file.name,
        use_container_width=True)

    w, h = st.session_state.image.size
    st.caption(f'{w} x {h} pixels · {st.session_state.image.mode}')