import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import os
import json

# ========== 1. pandas 读取本地 jsonl ==========
df = pd.read_json(r"code/method1knn/data/train.jsonl", lines=True)

# test_df = pd.read_json(r"F:\ge2340\data\test.jsonl", lines=True)
# 拼接标题+正文

X_train_text = df["text"].tolist()
y_train = df["label"].tolist()
# X_test_text = test_df["text"].tolist()
# y_test = test_df["label"].tolist()
#label1就是spam，0不是


# ========== 2. TF-IDF 向量化 ==========
tfidf = TfidfVectorizer(stop_words="english", max_features=5000)
X_train_sparse = tfidf.fit_transform(X_train_text)
# X_test_sparse = tfidf.transform(X_test_text)

# 稀疏矩阵转 torch tensor（稠密，5000维）
X_train = torch.tensor(X_train_sparse.toarray(), dtype=torch.float32)
# X_test = torch.tensor(X_test_sparse.toarray(), dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.long)
# y_test = torch.tensor(y_test, dtype=torch.long)

# ========== 3. 自定义 Torch Dataset ==========
class TfidfDataset(Dataset):
    def __init__(self, X, y):
        self.X = X
        self.y = y
    def __len__(self):
        return len(self.X)
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_ds = TfidfDataset(X_train, y_train)
# test_ds = TfidfDataset(X_test, y_test)

train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
# test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)


# --------------------------
# 2. 【重点】把整个训练集全部读出来，存成大张量库（KNN的知识库）
# --------------------------
def load_all_data(loader):
    all_x = []
    all_y = []
    with torch.no_grad():
        for batch_x, batch_y in loader:
            all_x.append(batch_x)
            all_y.append(batch_y)
    X = torch.cat(all_x, dim=0)
    Y = torch.cat(all_y, dim=0)
    return X, Y

train_vecs, train_labels = load_all_data(train_loader)
print(f"训练向量库 shape: {train_vecs.shape}")

# KNN超参
K = 5

# --------------------------
# 3. KNN 预测函数（余弦相似度）
# --------------------------
def knn_predict_one(x, train_x, train_y, k):
    # x: [5000] 单个测试向量
    sim = torch.cosine_similarity(x, train_x, dim=-1) # shape [31716]
    _, topk_idx = torch.topk(sim, k=k, dim=0)
    neighbor_labels = train_y[topk_idx]
    pred, _ = torch.mode(neighbor_labels, dim=0)
    return pred

# --------------------------
# 4. 在测试集跑KNN，评估
# --------------------------
if False:
    all_preds = []
    all_trues = []
    limit = 5

    print(f"开始测试，限制前{limit}条数据")
    count = 0
    stop = False
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            for i in range(batch_x.shape[0]):
                if count >= limit:
                    stop = True
                    break
                p = knn_predict_one(batch_x[i], train_vecs, train_labels, K)
                all_preds.append(p.cpu())
                all_trues.append(batch_y[i].cpu())
                count += 1
            if stop:
                break

    # all_preds = torch.stack(all_preds)
    # all_trues = torch.cat(all_trues)


    acc = accuracy_score(all_trues, all_preds)
    report = classification_report(all_trues, all_preds, target_names=["ham", "spam"])

    print(f"\nK={K} | Test Accuracy: {acc:.4f}")
    print(report)

def main():
    folder_path = r"code/mail_json"
    
    result = {}
    # 遍历文件夹里面所有文件
    for filename in os.listdir(folder_path):
        # 只处理后缀是 .json 的文件
        if filename.endswith(".json"):
            file_full_path = os.path.join(folder_path, filename)
            #print("正在读取：", file_full_path)
            
            # 打开+读取json
            with open(file_full_path, "r", encoding="utf-8") as f:
                data = json.load(f)  
            text = data['subject'] + " " + data['body']
            text_vector = tfidf.transform([text])
            text_vector = torch.tensor(text_vector.toarray(), dtype=torch.float32)

            pred = knn_predict_one(text_vector, train_vecs, train_labels, 5).item()
            
            result[filename] = pred
            print("mail_id:",data['mail_id'], "pred:", pred)
            # if result[filename] == 1:
            #     print(data)

if __name__ == "__main__":
    main()