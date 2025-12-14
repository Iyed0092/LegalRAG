import os
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from sentence_transformers import SentenceTransformer

base_path = "./data/ai_models"
os.makedirs(base_path, exist_ok=True)

print("1. Téléchargement du modèle d'Embedding (Sentence-Transformers)...")
embed_path = os.path.join(base_path, "all-MiniLM-L6-v2")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model.save(embed_path)
print(f"Embedding sauvegardé dans : {embed_path}")

print("\n2. Téléchargement du LLM (FLAN-T5-Base) - Ça peut prendre du temps (1GB)...")
llm_name = "google/flan-t5-base"
llm_path = os.path.join(base_path, "flan-t5-base")

tokenizer = AutoTokenizer.from_pretrained(llm_name)
model_llm = AutoModelForSeq2SeqLM.from_pretrained(llm_name)

tokenizer.save_pretrained(llm_path)
model_llm.save_pretrained(llm_path)
print(f"LLM sauvegardé dans : {llm_path}")