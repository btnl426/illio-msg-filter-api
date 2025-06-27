from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import time

# 모델 경로 
MODEL_PATH = "models/sentiment_models/daekeun-ml_koelectra-small-v3-nsmc"

# 모델과 토크나이저 로드
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)


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
        "elapsed": elapsed_time
    }