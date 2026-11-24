import joblib
from sentence_transformers import SentenceTransformer
import os
import json

folder_path = r"./mail_json"
emb_model = SentenceTransformer("all-MiniLM-L6-v2")
clf = joblib.load("./code/method2svm&encoder/spam_svm.joblib")

def predict_spam(mail_text):
    emb = emb_model.encode([mail_text], normalize_embeddings=True)
    res = clf.predict(emb)
    return res[0] # 0正常，1垃圾

for file in os.listdir(folder_path):
    if file.endswith(".json"):
        file_path = os.path.join(folder_path, file)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)  
            text = data['subject'] + " " + data['body']
            pred = predict_spam(text)
            print("mail_id:",data['uid'], "pred:", pred)
