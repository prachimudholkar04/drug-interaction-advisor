import streamlit as st
import requests

st.set_page_config(page_title="Drug Interaction Advisor", page_icon="💊")
st.title("💊 Drug Interaction Advisor")

st.markdown("""
Type your medication list or query below, and this tool will check for known drug interactions using RxNav and HuggingFace's biomedical NER model.
""")

query = st.text_area("Enter your medication query:", "I take paracetamol and tramadol. Is it safe?")

if st.button("Check Interactions"):
    with st.spinner("Analyzing drug names and checking interactions..."):
        try:
            response = requests.post("http://localhost:8000/interactions", json={"query": query})

            if response.status_code == 200:
                data = response.json()

                # Show extracted drugs
                extracted = data.get("extracted_drugs", [])
                if extracted:
                    st.info(f"🧪 **Extracted Drugs:** `{', '.join(extracted)}`")
                else:
                    st.warning("⚠️ No drug names were extracted from your input.")

                # Show interactions
                interactions = data.get("interactions", [])
                if not interactions:
                    st.success("✅ No significant drug interactions found.")
                else:
                    st.subheader("🚨 Drug Interactions")
                    for item in interactions:
                        st.error(
                            f"**Drugs:** `{item['drug_pair']}`  \n"
                            f"**Severity:** `{item['severity'].capitalize()}`  \n"
                            f"**Details:** {item['description']}"
                        )

            else:
                try:
                    st.warning(f"⚠️ {response.status_code}: {response.json().get('detail', response.text)}")
                except Exception:
                    st.error(f"❌ Unexpected response: {response.text}")

        except Exception as e:
            st.error(f"🔴 Request failed: {e}")
