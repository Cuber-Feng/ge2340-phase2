import torch
import torch.nn as nn
from sentence_transformers import SentenceTransformer
import os
import json

folder_path = r"./mail_json"
emb_model = SentenceTransformer("all-MiniLM-L6-v2")

k = 2
hidden_dim = 128
dropout_rate = 0.2

class DynamicMLP(nn.Module):
    def __init__(self, in_dim=384, hidden_dim=128, out_dim=1, k=2, dropout=0.2):
        super().__init__()
        layers = []
        layers.append(nn.Linear(in_dim, hidden_dim))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(dropout))
        for _ in range(k - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
        layers.append(nn.Linear(hidden_dim, out_dim))
        self.net = nn.Sequential(*layers)
    def forward(self, x):
        return self.net(x)

model = DynamicMLP(in_dim=384, hidden_dim=hidden_dim, k=k, dropout=dropout_rate)
model.load_state_dict(torch.load(f"./code/method3nn&encoder/models/spam_mlp_k{k}_hd{hidden_dim}_dr{dropout_rate}.pt"))
model.eval()

def predict_spam(text):
    emb = emb_model.encode([text], normalize_embeddings=True)
    tensor_x = torch.tensor(emb, dtype=torch.float32)
    with torch.no_grad():
        logit = model(tensor_x).squeeze()
        prob = torch.sigmoid(logit).item()
    return 1 if prob > 0.5 else 0, prob

for file in os.listdir(folder_path):
    if file.endswith(".json"):
        file_path = os.path.join(folder_path, file)
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            text = data['subject'] + " " + data['body']
            pred, prob = predict_spam(text)
            print("mail_id:",data['uid'], "pred:", pred, "prob:", prob)