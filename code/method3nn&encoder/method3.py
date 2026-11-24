import json
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sentence_transformers import SentenceTransformer

# ===================== 配置区，改这里 =====================
train_jsonl_path = r"./code/method3nn&encoder/data/train.jsonl"    # 你的jsonl文件
test_jsonl_path = r"./code/method3nn&encoder/data/test.jsonl"
emb_model_name = "all-MiniLM-L6-v2"
k = 2                # 你想要的隐藏层层数 k，比如 k=2、k=3、k=4
hidden_dim = 128     # 每层隐藏层神经元数量
dropout_rate = 0.2
lr = 1e-3
epoch_num = 30
# =========================================================

emb_model = SentenceTransformer(emb_model_name)

X_train = []
y_train = []
X_test = []
y_test = []
with open(train_jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        txt = obj.get("text", "").strip()
        lab = obj.get("label")
        if txt and lab is not None:
            X_train.append(txt)
            y_train.append(int(lab))
with open(test_jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        txt = obj.get("text", "").strip()
        lab = obj.get("label")
        if txt and lab is not None:
            X_test.append(txt)
            y_test.append(int(lab))

print(f"加载样本：{len(X_train)}")
print(f"加载样本：{len(X_test)}")
print("正在提取embedding...")
train_embeddings = emb_model.encode(X_train, normalize_embeddings=True)
test_embeddings = emb_model.encode(X_test, normalize_embeddings=True)



# 转为tensor
X_train = torch.tensor(train_embeddings, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_test = torch.tensor(test_embeddings, dtype=torch.float32)
y_test = torch.tensor(y_test, dtype=torch.float32)

# 动态搭建k层网络
class DynamicMLP(nn.Module):
    def __init__(self, in_dim=384, hidden_dim=128, out_dim=1, k=2, dropout=0.2):
        super().__init__()
        layers = []
        # 第一层：输入 -> 隐藏
        layers.append(nn.Linear(in_dim, hidden_dim))
        layers.append(nn.ReLU())
        layers.append(nn.Dropout(dropout))
        # 循环添加剩下 k-1 个隐藏层
        for _ in range(k - 1):
            layers.append(nn.Linear(hidden_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
        # 最后输出层
        layers.append(nn.Linear(hidden_dim, out_dim))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)

model = DynamicMLP(in_dim=384, hidden_dim=hidden_dim, k=k, dropout=dropout_rate)
loss_fn = nn.BCEWithLogitsLoss()
opt = optim.Adam(model.parameters(), lr=lr)

# 训练循环
for epoch in range(epoch_num):
    model.train()
    pred = model(X_train).squeeze()
    loss = loss_fn(pred, y_train)

    opt.zero_grad()
    loss.backward()
    opt.step()

    if epoch % 5 == 0:
        print(f"Epoch {epoch:2d} | Train Loss: {loss.item():.4f}")

# ---------------------- 测试集评估 ----------------------
model.eval()
with torch.no_grad():
    logits = model(X_test).squeeze()
    y_pred_prob = torch.sigmoid(logits)
    y_pred = (y_pred_prob > 0.5).long()

print("\n===== Test Classification Report =====")
print(classification_report(y_test.numpy(), y_pred.numpy(), target_names=["Normal", "Spam"]))

# 保存模型
torch.save(model.state_dict(), f"./code/method3nn&encoder/models/spam_mlp_k{k}_hd{hidden_dim}_dr{dropout_rate}.pt")
print(f"\n模型已保存：./code/method3nn&encoder/models/spam_mlp_k{k}_hd{hidden_dim}_dr{dropout_rate}.pt")
