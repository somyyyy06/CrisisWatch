from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=2)

# load your dataset or a public dataset (example using a placeholder)
dataset = load_dataset("csv", data_files={"train":"data/train.csv","validation":"data/val.csv"})
def preprocess(ex):
    return tokenizer(ex['text'], truncation=True, padding='max_length', max_length=256)
dataset = dataset.map(preprocess, batched=True)

training_args = TrainingArguments(output_dir="./models/distil_cred_v1", per_device_train_batch_size=16, num_train_epochs=3, evaluation_strategy="epoch")
trainer = Trainer(model=model, args=training_args, train_dataset=dataset['train'], eval_dataset=dataset['validation'])
trainer.train()
trainer.save_model("./models/distil_cred_v1")
