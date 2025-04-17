# 💊 Drug Interaction Advisor

An AI-powered app that checks for potential drug-drug interactions using free, open-source tools. It uses a biomedical NER model from HuggingFace to extract drug names from natural language queries and checks for interactions via the RxNav API.

---

## 🚀 Features

- ✅ Extracts drug names using HuggingFace NER (`d4data/biomedical-ner-all`)
- 🔍 Reconstructs subword tokens (e.g. "##cetamol" → "paracetamol")
- 🌐 Checks interactions via [RxNav API](https://rxnav.nlm.nih.gov/)
- 📦 Manual override for clinically critical combos (like `fluoxetine + tramadol`)
- 🖥️ Easy-to-use Streamlit UI
- 🔐 No OpenAI dependency — fully free and local!

---

## 🧠 Tech Stack

| Layer         | Tool                                      |
|---------------|-------------------------------------------|
| UI            | Streamlit                                 |
| Backend       | FastAPI                                   |
| NER Model     | HuggingFace Transformers (`biomedical-ner-all`) |
| Interaction API | RxNav                                    |
| Language      | Python                                     |

---

## 📦 Installation

```bash
git clone git@github.com:your-username/drug-interaction-advisor.git
cd drug-interaction-advisor
python -m venv .venv
source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows

pip install -r requirements.txt
python -m spacy download en_core_web_sm  # Optional if you want SpaCy fallback
