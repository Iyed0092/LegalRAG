import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000/api/v1"
INGEST_URL = f"{API_BASE_URL}/ingestion/documents/"
RAG_URL = f"{API_BASE_URL}/rag/ask/"

st.set_page_config(page_title="LegalRAG AI", page_icon="⚖️", layout="wide")

st.title("⚖️ LegalRAG - Assistant Juridique Intelligent")
st.markdown("---")

with st.sidebar:
    st.header("Ingestion de Documents")
    uploaded_file = st.file_uploader("Choisissez un fichier PDF", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Ingérer et Analyser"):
            with st.spinner("Envoi et Traitement (RAG Pipeline)..."):
                files = {"file": uploaded_file}
                data = {"title": uploaded_file.name} 
                response = requests.post(INGEST_URL, files=files, data=data)
                if response.status_code == 201:
                    st.balloons()
                    st.success("Document uploadé et indexé avec succès !")
                    st.json(response.json().get("data")) # Show metadata
                    
                elif response.status_code == 202:
                    st.warning("Fichier sauvegardé, mais erreur d'indexation.")
                    st.error(f"Détails : {response.json().get('error')}")
                    
                else:
                    st.error(f"Erreur Serveur ({response.status_code}) : {response.text}")

    st.markdown("---")
    st.info("Ce système utilise une architecture Hybride : **Neo4j** (Graphe) + **ChromaDB** (Vecteurs).")

st.header("Discutez avec vos documents")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Posez votre question juridique..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Analyse Hybride (Mots-clés + Sémantique)..."):
            payload = {"question": prompt}
            response = requests.post(RAG_URL, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', "Je n'ai pas trouvé de réponse.")
                full_response = answer
                message_placeholder.markdown(full_response)
            else:
                full_response = f"Erreur API : {response.text}"
                message_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})