import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
import json

MODEL_PATH = './model/model_train.py'

with open('./model/model_config.json', 'r') as f:
    config = json.load(f)

labels = config['labels']

tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH, num_labels=len(labels))

def predict(text : str):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    predicted_class_id = logits.argmax().item()
    return labels[predicted_class_id]

if __name__ == "__main__":
    test_text = "This is a sample text for classification."
    prediction = predict(test_text)
    print(f"Predicted class: {prediction}")
    