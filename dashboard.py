import streamlit as st
import requests

# --- CONFIGURATION ---
API_BASE_URL = "http://localhost:8000/api/v1"
INGEST_URL = f"{API_BASE_URL}/ingestion/documents/"
RAG_URL = f"{API_BASE_URL}/rag/ask/"

st.set_page_config(page_title="LegalRAG AI", page_icon="⚖️", layout="wide")

# --- HEADER ---
st.title("⚖️ LegalRAG - Assistant Juridique Intelligent")
st.markdown("---")

# --- SIDEBAR : UPLOAD ---
with st.sidebar:
    st.header("Ingestion de Documents")
    uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Ingérer et Analyser"):
            with st.spinner("Envoi du fichier vers le Backend Django..."):
                try:
                    files = {"file": uploaded_file}
                    response = requests.post(INGEST_URL, files=files)
                    
                    if response.status_code == 201:
                        doc_id = response.json()['id']
                        st.success("Fichier uploadé !")
                        
                        with st.spinner("🧠 Indexation dans Neo4j & ChromaDB..."):
                            process_url = f"{INGEST_URL}{doc_id}/process/"
                            proc_res = requests.post(process_url)
                            if proc_res.status_code == 202:
                                st.balloons()
                                st.success("Document prêt pour le RAG !")
                            else:
                                st.error(f"Erreur Indexation : {proc_res.text}")
                    else:
                        st.error(f"Erreur Upload : {response.text}")
                except Exception as e:
                    st.error(f"Erreur de connexion : {e}")

    st.markdown("---")
    st.info("Ce système utilise une architecture Hybride : **Neo4j** (Graphe) + **ChromaDB** (Vecteurs).")

# --- MAIN : CHAT ---
st.header("💬 Discutez avec vos documents")

# Initialisation de l'historique
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Zone de saisie utilisateur
if prompt := st.chat_input("Posez votre question juridique..."):
    # 1. Afficher la question de l'utilisateur
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Interroger l'API
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("L'IA réfléchit..."):
            try:
                payload = {"question": prompt}
                response = requests.post(RAG_URL, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get('answer', "Je n'ai pas trouvé de réponse.")
                    sources = data.get('context_used', '')
                    
                    full_response = f"{answer}\n\n---\n**Sources / Contexte :**\nRunning legal analysis on relevant nodes...\n{sources[:300]}..."
                    message_placeholder.markdown(full_response)
                else:
                    full_response = f"❌ Erreur API : {response.text}"
                    message_placeholder.markdown(full_response)
            except Exception as e:
                full_response = f"❌ Erreur de connexion : {e}"
                message_placeholder.markdown(full_response)
        
        # 3. Sauvegarder la réponse
        st.session_state.messages.append({"role": "assistant", "content": full_response})