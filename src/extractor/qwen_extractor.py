# <<<./ Import Libraries
import json
import logging
import re
from typing import Optional

import torch
from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, BitsAndBytesConfig, Qwen2VLForConditionalGeneration

from src.extractor.base import BaseExtractor, ExtractionError
from src.schemas import AdditionalCharges, Receipt, ReceiptItem

# <<<./ Instantiate Logger, Model, and Prompt
logger = logging.getLogger(__name__)

MODEL_ID = 'Qwen/Qwen2-VL-2B-Instruct'

EXTRACTION_PROMPT = """
Extract all data from this receipt and return ONLY a valid JSON object.
No explanation. No markdown. No code block. Only raw JSON.

Below is the example of required format. Use ONLY values from the receipt image.
NEVER copy the example values. Also, NEVER make a key/field different from the key:value pair on the format.

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
- Field names must match exactly: "subtotal" not "sub_total", "total" not "grand_total".
- Do not hallucinate or assume a number on each key/field names, match exactly with what the image shown.
- All monetary values must be plain numbers. No currency symbols or dots as thousand separators.
- If no additional charges exist, use an empty list: []
- quantity must be greater than 0
"""

# <<<./ Build Qwen Extractor
class QwenExtractor(BaseExtractor):
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.model: Optional[Qwen2VLForConditionalGeneration] = None
        self.processor: Optional[AutoProcessor] = None
        self.load_model()

    # <<<./ Load Qwen and Quantization
    def load_model(self):
        logger.info(f'Loading model {self.model_id} with 4-bit quantization...')

        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_compute_dtype=torch.float16
            )

        self.model = Qwen2VLForConditionalGeneration.from_pretrained(
            self.model_id,
            quantization_config=quantization_config,
            device_map='auto')

        self.processor = AutoProcessor.from_pretrained(self.model_id, min_pixels=256 * 28 * 28, max_pixels=512 * 28 * 28)
        logger.info(f'Model loaded.')

    # <<<./ Build JSON Message
    def build_messages(self, image: Image.Image):
        return [
            {
                'role' : 'user',
                'content' : [
                    {'type': 'image', 'image': image},
                    {'type': 'text', 'text': EXTRACTION_PROMPT}
                ]
            }
        ]

    # <<<./ Generate JSON Message Containing Extracted Receipt Data
    def generate(self, messages: list):
        torch.cuda.empty_cache()
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True)

        image_inputs, _ = process_vision_info(messages)
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            padding=True,
            return_tensors='pt'
        ).to(self.model.device)

        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=2048)

        trimmed = [
            out[len(inp):]
            for inp, out in zip(inputs.input_ids, generated_ids)]

        return self.processor.batch_decode(
            trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )[0]

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
            messages = self.build_messages(image)
            raw_text = self.generate(messages)
            data = self.parse_json(raw_text)
            return self.build_receipt(data)
        except ExtractionError as e:
            raise
        except Exception as e:
            raise ExtractionError(f'Qwen extraction failed unexpectedly: {e}') \
                from e