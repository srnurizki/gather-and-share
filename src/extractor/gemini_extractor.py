# <<<./ Import Libraries
import json
import logging
import os
import re

from google import genai
from PIL import Image

from src.extractor.base import BaseExtractor, ExtractionError
from src.schemas import AdditionalCharges, Receipt, ReceiptItem

# <<<./ Instantiate Logger, Model, and Prompt
logger = logging.getLogger(__name__)

MODEL_NAME = 'gemini-2.5-flash'

EXTRACTION_PROMPT = """
Extract all data from this receipt and return ONLY a valid JSON object.
No explanation. No markdown. No code block. Only raw JSON.

Below is the example of required format. Use ONLY values from the receipt image.
NEVER copy the example values.

Required format:
{ 
    "items" : [
        { 
            "name" : "Item name as printed",
            "quantity" : 1.0,
            "unit_price" : 10000.0,
            "total_price" : 10000.0
        }
    ],
    "subtotal" : 10000.0,
    "additional_charges" : [
        { 
            "label" : "Charge label as printed",
            "amount" : 1000.0
        }
    ],
    "total" : 11000.0
}

Rules:
- All monetary values must be plain numbers. No currency symbols or dots as thousand separators.
- If no additional charges exist, use an empty list: []
- quantity must be greater than 0
"""

# <<<./ Build Gemini Extractor
class GeminiExtractor(BaseExtractor):
    def __init__(self, api_key: str = None, model_name: str = MODEL_NAME):
        api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError(
                'GEMINI_API_KEY not found.'
                'Define it in .env or pass directly to GeminiExtractor(api_key=YOUR_API_KEY)')

        # <<<./ Load Gemini API
        self.client = genai.Client(api_key=api_key)
        self.model = model_name
        logger.info(f'GeminiExtractor ready. Model: {model_name}')

    # <<<./ Get JSON
    def parse_json(self, raw_text: str):
        clean = re.sub(r'^```(?:json)?\s*\n?', '', raw_text.strip())
        clean = re.sub(r'\n?```\s*$', '', clean).strip()
        try:
            return json.loads(clean)
        except json.decoder.JSONDecodeError:
            pass

        match = re.search(r'\{n.*\}', clean, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.decoder.JSONDecodeError:
                pass

        raise ExtractionError(
            f'No valid JSON in model output. Raw output snippet: {raw_text[:300]}')

    # <<<./ Build Receipt Data
    def build_receipt(self, data: dict):
        try:
            items = [ReceiptItem(**item) for item in data['items']]
            additional_charges = [
                AdditionalCharges(**charge)
                for charge in data.get('additional_charges', [])
            ]
            return Receipt(
                items=items,
                subtotal=float(data['subtotal']),
                additional_charges=additional_charges,
                total=float(data['total']),
            )
        except (KeyError, TypeError, ValueError) as e:
            raise ExtractionError(f'Failed to construct Receipt from parsed data: {e}') \
                from e

    # <<<./ Extract as Single Information
    def extract(self, image: Image.Image):
        try:
            response = self.client.models.generate_content(model=self.model, contents=[EXTRACTION_PROMPT, image])
            raw_text = response.text
            data = self.parse_json(raw_text)
            return self.build_receipt(data)
        except ExtractionError as e:
            raise
        except Exception as e:
            raise ExtractionError(f'Gemini extraction failed unexpectedly: {e}') \
                from e


