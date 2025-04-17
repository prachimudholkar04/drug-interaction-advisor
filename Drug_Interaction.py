from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import httpx
import os
import json
from transformers import pipeline
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Load NER pipeline from HuggingFace
ner = pipeline("ner", model="d4data/biomedical-ner-all", aggregation_strategy="simple")

# Manual override for critical known interactions
MANUAL_INTERACTIONS = {
    "fluoxetine+tramadol": {
        "severity": "major",
        "description": "Taking tramadol with fluoxetine can increase the risk of serotonin syndrome. Symptoms include confusion, hallucination, and increased heart rate."
    },
    "sertraline+tramadol": {
        "severity": "major",
        "description": "Sertraline and tramadol together may also increase the risk of serotonin syndrome."
    }
}

# ----------------------
# MODELS
# ----------------------
class DrugInput(BaseModel):
    query: str

class InteractionResult(BaseModel):
    drug_pair: str
    description: str
    severity: str

# ----------------------
# UTILITY FUNCTIONS
# ----------------------
async def get_rxcui(drug_name: str) -> str:
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]
        return rxcui

async def get_interactions(rxcui_list: List[str], drug_names: List[str]) -> List[InteractionResult]:
    interaction_results = []

    # Check manual overrides first
    key = "+".join(sorted(drug_names))
    if key in MANUAL_INTERACTIONS:
        manual = MANUAL_INTERACTIONS[key]
        interaction_results.append(InteractionResult(
            drug_pair=key,
            description=manual["description"],
            severity=manual["severity"]
        ))
        return interaction_results

    for i in range(len(rxcui_list)):
        for j in range(i + 1, len(rxcui_list)):
            url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcui_list[i]}+{rxcui_list[j]}"
            print(f"🔗 Querying interaction API: {url}")

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
            except Exception as e:
                print(f"❌ API error for {rxcui_list[i]} + {rxcui_list[j]}:", e)
                continue

            interactions = data.get("fullInteractionTypeGroup", [])
            print(f"📦 Raw interaction data: {interactions}")

            for group in interactions:
                for interaction_type in group.get("fullInteractionType", []):
                    for interaction_pair in interaction_type.get("interactionPair", []):
                        description = interaction_pair.get("description", "No description available.")
                        severity = interaction_pair.get("severity", "unknown")
                        pair = f"{rxcui_list[i]} + {rxcui_list[j]}"
                        interaction_results.append(InteractionResult(
                            drug_pair=pair,
                            description=description,
                            severity=severity
                        ))

    return interaction_results

async def extract_drug_names(query: str) -> List[str]:
    try:
        results = ner(query)
        print("🧠 Raw NER output:", results)

        # Reconstruct full names from subword pieces
        combined = []
        current = ""
        for r in results:
            word = r["word"]
            if word.startswith("##"):
                current += word[2:]
            else:
                if current:
                    combined.append(current)
                current = word
        if current:
            combined.append(current)

        drugs = [d.lower() for d in combined if d.isalpha()]
        print("🔍 Reconstructed drugs:", drugs)

        return list(set(drugs))

    except Exception as e:
        print("❌ NER extraction failed:", e)
        return []

# ----------------------
# API ENDPOINT
# ----------------------
@app.post("/interactions")
async def check_interactions(drug_query: DrugInput):
    print("✅ Query received:", drug_query.query)

    try:
        drug_names = await extract_drug_names(drug_query.query)
        print("💊 Extracted drugs:", drug_names)

        if not drug_names:
            raise HTTPException(status_code=400, detail="No valid drug names found.")

        rxcui_list = []
        for drug in drug_names:
            rxcui = await get_rxcui(drug)
            print(f"🔍 {drug} → {rxcui}")
            if not rxcui:
                raise HTTPException(status_code=404, detail=f"RxCUI not found for drug: {drug}")
            rxcui_list.append(rxcui)

        interactions = await get_interactions(rxcui_list, drug_names)
        print("✅ Interactions found:", interactions)

        return {
            "extracted_drugs": drug_names,
            "interactions": [interaction.dict() for interaction in interactions]
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print("❌ Exception:", e)
        raise HTTPException(status_code=500, detail=str(e))
