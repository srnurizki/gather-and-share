# 💵 Gather and Share

> AI-powered receipt splitting that handles tax, service charges, and additional fees proportionally so no one overpays or underpays.

We are a social being by nature, however, the concept of split bill is coined way later than when we first learned trading. Allotting owed payments could lead to headache and collective confusion when we have to deal with sharing tax, service, and other additional charges proportional to our purchase amount. Hereby, Gather and Share, a split bill prototype that alleviates your bill sharing process as quick as scanning your receipt, assigning items, and voila! You know how much should you pay (or receive) now!

![til](https://raw.githubusercontent.com/srnurizki/gather-and-share/master/assets/sample/demo.gif)

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| UI | Streamlit | Web app framework |
| Primary AI | Gemini 2.5 Flash (Google GenAI API) | OCR-free receipt extraction |
| Local AI | Qwen2VL | OCR-free receipt extraction (offline) |
| Quantization | BitsAndBytes | 4-bit model quantization for consumer GPU |
| Model Loading | HuggingFace Transformers | Local model inference pipeline |
| Data Validation | Pydantic v2 | Structured output schemas |
| Image Processing | Pillow | Receipt image preprocessing |
| Export | pandas | CSV bill summary generation |
| API SDK | google-genai | Gemini API client |

---

## Model Research

Two models were evaluated for receipt data extraction:

| Model | Type | Parameters | Hardware |
|---|---|---|---|
| Qwen2-VL 2B Instruct | Local (4-bit quantized) | 2B | NVIDIA RTX 3050 Studio, 4GB VRAM |
| Google Gemini 2.5 Flash | API | Undisclosed (large) | Google Cloud Infrastructure |

### Why These Models

**Qwen2-VL 2B** was selected for local inference compatibility with a 4GB VRAM consumer GPU. It is an OCR-free vision-language model available on HuggingFace, and 4-bit quantization brings the VRAM footprint to approximately 1.5–1.6GB, making it feasible on constrained hardware.

**Gemini 2.5 Flash** was selected for its strong multimodal capability and ease of integration via Google's GenAI API. As an API-based model, it runs on Google's infrastructure, enabling access to a significantly larger model without any local GPU requirement at the trade-off of requiring an internet connection and API key.

### Performance Comparison

| Model | Receipt | Name Score | Qty Acc (%) | Price Exact (%) | Avg Price MAPE (%) | Total Correct | Inference Time (s) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Gemini | familymart-1.jpeg | 98.8 | 100.0 | 100.0 | 0.00 | True | 20.59 |
| Gemini | kopken-1.jpeg | 98.1 | 100.0 | 100.0 | 0.00 | True | 6.68 |
| Gemini | lawson-1.jpeg | 100.0 | 100.0 | 100.0 | 0.00 | False | 7.84 |
| Gemini | ncoffee-1.jpeg | 100.0 | 100.0 | 100.0 | 0.00 | True | 6.74 |
| Gemini | toko-1.jpeg | 96.5 | 100.0 | 100.0 | 0.00 | True | 12.36 |
| Qwen | familymart-1.jpeg | 93.0 | 100.0 | 0.0 | 28.57 | False | 17.50 |
| Qwen | kopken-1.jpeg | 7.0 | 100.0 | 0.0 | 11.11 | False | 14.46 |
| Qwen | lawson-1.jpeg | 88.2 | 100.0 | 100.0 | 0.00 | False | 18.40 |
| Qwen | ncoffee-1.jpeg | 100.0 | 100.0 | 100.0 | 0.00 | True | 20.30 |
| Qwen | toko-1.jpeg | 97.8 | 25.0 | 75.0 | 15.00 | False | 33.52 |

---

### Sample Output Comparison

![alt text](https://raw.githubusercontent.com/srnurizki/gather-and-share/master/assets/receipts/familymart-1.jpeg)

**Gemini:** File `[familymart-1.jpeg]`
```json
{
  "items": [
    {
      "name": "Boneless Crispy Chicken Ala Cart e Pcs",
      "quantity": 1.0,
      "unit_price": 14000.0,
      "total_price": 14000.0
    },
    {
      "name": "Aquviva Btl 700ml",
      "quantity": 1.0,
      "unit_price": 3500.0,
      "total_price": 3500.0
    }
  ],
  "subtotal": 17500.0,
  "additional_charges": [],
  "total": 17500.0
}
```

**Qwen:** File `[familymart-1.jpeg]`
```json
{
  "items": [
    {
      "name": "Boneless Crispy Chicken Ala Cart",
      "quantity": 1.0,
      "unit_price": 10000.0,
      "total_price": 10000.0
    }
  ],
  "subtotal": 10000.0,
  "additional_charges": [
    {
      "label": "Charge label as printed",
      "amount": 1000.0
    }
  ],
  "total": 11000.0
}
```

---

> ![ncoffee-1.jpeg](https://github.com/srnurizki/gather-and-share/blob/master/assets/receipts/ncoffee-1.jpeg?raw=true)

**Gemini:** File `[ncoffee-1.jpeg]`
```json
{
  "items": [
    {
      "name": "Nasi Ayam Siram",
      "quantity": 1.0,
      "unit_price": 28000.0,
      "total_price": 28000.0
    },
    {
      "name": "Americano",
      "quantity": 1.0,
      "unit_price": 18000.0,
      "total_price": 18000.0
    }
  ],
  "subtotal": 46000.0,
  "additional_charges": [
    {
      "label": "PB1",
      "amount": 4600.0
    },
    {
      "label": "Pembulatan",
      "amount": 400.0
    }
  ],
  "total": 51000.0
}
```

**Qwen:** File `[ncoffee-1.jpeg]`
```json
{
  "items": [
    {
      "name": "Nasi Ayam Siram",
      "quantity": 1.0,
      "unit_price": 28000.0,
      "total_price": 28000.0
    },
    {
      "name": "Americano",
      "quantity": 1.0,
      "unit_price": 18000.0,
      "total_price": 18000.0
    }
  ],
  "subtotal": 46000.0,
  "additional_charges": [
    {
      "label": "Charge label as printed",
      "amount": 1000.0
    }
  ],
  "total": 51000.0
}
```

### Analysis

**Why local 2B models underperformed:**

Qwen2-VL 2B struggled on real-world Indonesian receipts. The root cause is model capacity at 2 billion parameters, which is insufficient for complex document layout understanding. Failures observed include:

- Misidentifying multi-line item names (e.g. item name wrapped across two lines on the receipt)
- Failing to parse domain-specific pricing notation (e.g. `@ONS` or price per 100g)
- Hallucinating numeric values not present on the receipt
- Returning inconsistent JSON field names despite explicit prompt instructions

**Note on quantization:** 4-bit quantization reduces VRAM usage approximately 4× by lowering numerical precision per parameter; it does not reduce the number of parameters. The performance gap observed is a consequence of model size, not quantization.

**Why Gemini 2.5 Flash outperformed:**

Running on Google's infrastructure, Gemini 2.5 Flash has access to significantly more parameters than the local 2B models. This translates to stronger instruction following, better spatial reasoning over document layouts, and correct interpretation of domain-specific notations like `@ONS`. The API model also does not face VRAM constraints that limit local inference.

### Conclusion

Gemini 2.5 Flash was selected as the primary model for this prototype due to its accuracy on diverse receipt formats. Local models remain available in the app as an offline alternative, with the caveat of reduced accuracy on complex receipts.


---

## Setup

### Prerequisites

- Python 3.10+
- Conda
- NVIDIA GPU with 4GB+ VRAM _(required for Granite Vision local model)_
- CUDA 11.8 or higher

### Installation

```bash
# 1. Clone repository
git clone https://github.com/<username>/gather-and-share.git
cd gather-and-share

# 2. Create and activate conda environment
conda create -n <your-env> python=3.10
conda activate <your-env>

# 3. Install PyTorch with CUDA (must be installed before other dependencies)
pip install torch --index-url https://download.pytorch.org/whl/cu118

# 4. Install remaining dependencies
pip install -r requirements.txt
```

### Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in your API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key at [aistudio.google.com](https://aistudio.google.com).

### Running the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## How It Works

1. **Upload** a receipt photo (JPG, PNG, WebP)
2. **Review** AI-extracted items, correct any misread names or prices
3. **Add** participant names
4. **Assign** each item to the person(s) who ordered it
5. **Calculate** charges like tax and service fee are split proportionally based on each person's item subtotal
6. **Download** the bill summary as CSV

---

## Limitations

- Unable to assign friends of the same name (e.g. John Doe and John Doe), therefore do make a distinction :D!
- Information extraction quality is subject to image clarity; blurry images, fading inks, overexposure, underexposure, and other visual bottlenecks may lead to false extraction.
- Local model performance (e.g. inference time) is affected directly by your GPU VRAM. Higher VRAM may result in better performance.
- Amendment of item details may lead to subtotal mismatch.
- One bill at a time, multiple receipts are currently not supported.
- At last, this is not hosted yet, therefore you need to set it up locally

---

## Potential Improvements

- Database integration to save user previous receipts and sessions
- Multiple receipts support, allowing completely different receipts to be scanned at once.
- Fine-tuning model across a large amount and diverse receipts to speed up inference time.
- Ability to store identical name of different people by assigning UUID to each individuals.
- Save-as-Image feature allowing easier shareable media for more intuitive user experience.
