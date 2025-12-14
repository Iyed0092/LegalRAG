from transformers import pipeline
from django.conf import settings

class LLMService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance.generator = pipeline(
                "text2text-generation",
                model=settings.LLM_MODEL_NAME,
                max_length=settings.GENERATION_CONFIG['max_length'],
            )
        return cls._instance

    def generate_answer(self, context, question):
        input_text = (
            "You are a helpful legal assistant. Use the provided Context to answer the Question accurately. "
            "If the answer is NOT in the Context, simply say 'Information not found in the documents'.\n\n"
            f"Context: {context}\n\n"
            f"Question: {question}\n\n"
            "Answer:"
        )
        
        if len(input_text) > 4000: 
            input_text = input_text[:4000]

       
        result = self.generator(
            input_text,
            **settings.GENERATION_CONFIG  
        )
        
        return result[0]['generated_text']