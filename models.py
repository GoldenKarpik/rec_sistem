import os
from sentence_transformers import SentenceTransformer
from keybert import KeyBERT
from transformers import pipeline


CACHE_DIR = ''
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['TRANSFORMERS_CACHE'] = CACHE_DIR
os.environ['HF_HOME'] = CACHE_DIR
sentence_model_name = "all-MiniLM-L6-v2"
sentence_model_path = os.path.join(CACHE_DIR, sentence_model_name)

if not os.path.exists(sentence_model_path):
    print(f"Downloading {sentence_model_name} to {sentence_model_path}...")
    nlp_model = SentenceTransformer(sentence_model_name)
    nlp_model.save(sentence_model_path)
else:
    print(f"Loading {sentence_model_name} from {sentence_model_path}...")
    nlp_model = SentenceTransformer(sentence_model_path)

generator_model_name = "gpt2"
generator_model_path = os.path.join(CACHE_DIR, generator_model_name)

if not os.path.exists(generator_model_path):
    print(f"Downloading {generator_model_name} to {generator_model_path}...")
    generator = pipeline('text-generation', model=generator_model_name)
    generator.model.save_pretrained(generator_model_path)
    generator.tokenizer.save_pretrained(generator_model_path)
else:
    print(f"Loading {generator_model_name} from {generator_model_path}...")
    generator = pipeline('text-generation', model=generator_model_path)

keyword_extractor = KeyBERT(model=nlp_model)