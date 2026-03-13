import json
import os
import pandas as pd
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    TrainingArguments,
    Trainer
)

#carregar configuração
with open("model/model_config.json") as f:
    config = json.load(f)

with open("model/tokenizer_config.json") as f:
    tokenizer_config = json.load(f)

MODEL_NAME = config["model_name"]
LABELS = config["labels"]

#carregar dataset
data = pd.read_csv("model/intent_dataset.csv")

label2id = {label: i for i, label in enumerate(LABELS)}
id2label = {i: label for label, i in label2id.items()}

data["label"] = data["intent"].map(label2id)

#split
train_df, test_df = train_test_split(data, test_size=0.2, random_state=42)
train_data = Dataset.from_pandas(train_df)
test_data = Dataset.from_pandas(test_df)

#tokenizer
tokenizer = DistilBertTokenizerFast.from_pretrained(
    MODEL_NAME,
    **tokenizer_config
)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=64
    )

train_data = train_data.map(tokenize, batched=True, batch_size=32)
test_data = test_data.map(tokenize, batched=True, batch_size=32)

train_data.set_format("torch", columns=["input_ids", "attention_mask", "label"])
test_data.set_format("torch", columns=["input_ids", "attention_mask", "label"])

#model
model = DistilBertForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=len(LABELS),
    id2label=id2label,
    label2id=label2id
)

#training
training_args = TrainingArguments(
    output_dir="model/intent_model",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=5e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=4,
    weight_decay=0.01,
    logging_steps=10,
    logging_dir=os.path.join("model/intent_model", "logs"),
    load_best_model_at_end=True
        )

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=test_data
)

#train
print("Iniciando o treinamento do modelo...")
trainer.train()

#save
print("Salvando o modelo treinado...")
trainer.save_model("./model/trained/")
tokenizer.save_pretrained("./model/trained/")

print("Treinamento finalizado com sucesso!")