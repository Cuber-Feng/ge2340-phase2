import json
import joblib
from sentence_transformers import SentenceTransformer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ---------------------- 配置 ----------------------
train_jsonl_path = r"./code/method2svm&encoder/train.jsonl"    # 你的jsonl文件
test_jsonl_path = r"./code/method2svm&encoder/test.jsonl"
emb_model_name = "all-MiniLM-L6-v2"
svm_save_path = "./code/method2svm&encoder/spam_svm.joblib"
text_key = "text"    # 你json里面文本的字段名，不对就改
label_key = "label"  # 标签字段名

# 加载encoder模型（CPU运行）
emb_model = SentenceTransformer(emb_model_name)

# ---------------------- 读取jsonl ----------------------
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
        txt = obj.get(text_key, "")
        lab = obj.get(label_key)
        if txt and lab is not None:
            X_train.append(txt)
            y_train.append(int(lab))
with open(test_jsonl_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        txt = obj.get(text_key, "")
        lab = obj.get(label_key)
        if txt and lab is not None:
            X_test.append(txt)
            y_test.append(int(lab))

print(f"一共加载 {len(X_train)} 条邮件")
print(f"一共加载 {len(X_test)} 条邮件")

# ---------------------- 提取向量（Encoder attention输出） ----------------------
print("正在提取embedding ...")
train_embeddings = emb_model.encode(X_train, normalize_embeddings=True)
test_embeddings = emb_model.encode(X_test, normalize_embeddings=True)

# ---------------------- 训练SVM ----------------------
# X_train, X_test, y_train, y_test = train_test_split(
#     embeddings, labels, test_size=0.2, random_state=42, stratify=labels
# )
clf = LinearSVC(random_state=42)
clf.fit(train_embeddings, y_train)

# 评估
y_pred = clf.predict(test_embeddings)
print("\n===== 评估报告 =====")
print(classification_report(y_test, y_pred))

# 保存SVM
joblib.dump(clf, svm_save_path)
print(f"\nSVM模型已保存到 {svm_save_path}")
