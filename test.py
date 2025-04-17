from transformers import pipeline
ner = pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")

query = "I take paracetamol and tramadol"
results = ner(query)
for r in results:
    print(r)