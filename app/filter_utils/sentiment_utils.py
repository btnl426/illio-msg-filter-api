from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time
import os

sentiment_model_path = os.getenv("SENTIMENT_MODEL_PATH")
tokenizer = AutoTokenizer.from_pretrained(sentiment_model_path)
model = AutoModelForSequenceClassification.from_pretrained(sentiment_model_path)

def predict_sentiment(text: str) -> dict:
    start_time = time.time()

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probs = torch.nn.functional.softmax(logits, dim=1)
    predicted_class_id = torch.argmax(probs, dim=1).item()
    confidence = probs[0][predicted_class_id].item()

    elapsed_time = round(time.time() - start_time, 4)

    return {
        "label": "positive" if predicted_class_id == 1 else "negative",
        "confidence": confidence,
        "inference_time": elapsed_time
    }