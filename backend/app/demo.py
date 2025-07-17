
# Load model directly
from transformers import AutoTokenizer, AutoModelForMaskedLM

tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-bert-wwm-ext")
model = AutoModelForMaskedLM.from_pretrained("hfl/chinese-bert-wwm-ext")