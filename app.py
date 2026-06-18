# <<<./ Import Libraries
import streamlit as st
from dotenv import load_dotenv

from components.receipt_editor import render_receipt_editor
from components.participant_setup import render_participant_setup
from components.split_summary import render_split_summary
from components.upload_section import render_upload_section
from src.extractor.base import ExtractionError
from src.extractor.qwen_extractor import QwenExtractor
from src.extractor.gemini_extractor import GeminiExtractor

# <<<./ Load Environment
load_dotenv()

# <<<./ Load Gemini
@st.cache_resource
def load_gemini():
    return GeminiExtractor()

# <<<./ Load Qwen
@st.cache_resource
def load_qwen():
    return QwenExtractor()

# <<<./ Run Streamlit
def main():
    st.set_page_config(
        page_title="Gather and Share",
        page_icon='💵',
        layout='centered')

    st.title('💵 Gather and Share')
    st.caption('Upload your receipt, assign items, and let AI split the bill')

    model_choice = st.radio(
        'AI Model',
        options=['Gemini 2.5 Flash', 'Qwen2-VL-2B'],
        horizontal=True,
        label_visibility='collapsed')

    extractor=load_gemini() if model_choice.startswith('Gemini') else load_qwen()

    render_upload_section()

    if (st.session_state.get('image') is not None
            and st.session_state.get('receipt') is None):
        with st.spinner('Reading receipt...'):
            try:
                receipt = extractor.extract(st.session_state.image)
                st.session_state.receipt = receipt.model_dump()
                st.rerun()
            except ExtractionError as e:
                st.error(f'Failed to read receipt: {e}')

    render_participant_setup()
    render_receipt_editor()
    render_split_summary()

if __name__ == '__main__':
    main()