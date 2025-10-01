import time, requests, json, os
# === Step 0: 从 config.json 读取配置 ===
with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)
MODE = cfg["mode"]
# 解析 cookies 字符串 -> dict
cookies = {}
for kv in cfg["cookies"].split(";"):
    kv = kv.strip()
    if not kv:
        continue
    try:
        k, v = kv.split(":", 1)
    except ValueError:
        print(f"❌ cookie 格式错误或者您没有按要求修改config文件。")
        exit(1)
    cookies[k] = v

token = cfg["X-Access-Token"]
if not token or token == "your token here":
    print("❌ 请在 config.json 中配置 X-Access-Token")
    exit(1)

headers = {
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://aqxx.nju.edu.cn",
    "Referer": "https://aqxx.nju.edu.cn/students/questionList",
    "User-Agent": "Mozilla/5.0 ...",
    "X-Access-Token": token,
    "X-TIMESTAMP": str(int(time.time() * 1000)),
    "X-Sign": "A48DAC0A80BCB90B2DD02118A53D8EC7",  # 先写死
    "tenant-id": "0"
}

# === Step 1: 开始考试 ===
exam_id = "1970328837573189633"  # ⚠️ 每次考试的ID需要替换
start_url = "https://aqxx.nju.edu.cn/api/jeecg-boot/jcedutec/exam/startExam"
payload = {"id": exam_id, "type": MODE}

resp = requests.post(start_url, headers=headers, cookies=cookies, json=payload)
try:
    exam_data = resp.json()
except Exception as e:
    print("❌ 请确认您已经登录并合法配置config.json")
    exit(1)

exam_record_id = exam_data["result"]["id"]
records = exam_data["result"]["records"]

print(f"考试记录ID: {exam_record_id}, 题目数: {len(records)}")

# === Step 2: 题库匹配答案（支持多选） ===
bank_file = "bank.json"
if os.path.exists(bank_file):
    with open(bank_file, "r", encoding="utf-8") as f:
        my_bank = json.load(f)
else:
    my_bank = {}

answers = {}
for r in records:
    qid = r["id"]
    stem = r["stem"]
    correct_texts = my_bank.get(stem)  # 列表
    chosen = []
    if correct_texts:
        if isinstance(correct_texts, str):  # 兼容旧题库
            correct_texts = [correct_texts]
        for key in ["optiona", "optionb", "optionc", "optiond"]:
            text = r.get(key)
            if text and text.strip() in [t.strip() for t in correct_texts]:
                chosen.append(key[-1].upper())  # 记录字母
    
    if not chosen:
        ans = "A"
    elif len(chosen) == 1:
        ans = "".join(chosen)
    else:
        chosen.sort()
        ans = chosen
    
    answers[qid] = ans

# === Step 3: 提交试卷 ===
submit_url = f"https://aqxx.nju.edu.cn/api/jeecg-boot/jcedutec/exam/submitExam/{exam_record_id}"
resp2 = requests.post(submit_url, headers=headers, cookies=cookies, json=answers)
result = resp2.json()["result"]

print("✅ 提交完成")
print("得分:", result["score"])
print("是否合格:", "是" if result["isQualified"] == "1" else "否")

# === Step 4: 获取错题集 ===
t = int(time.time())
wrong_url = f"https://aqxx.nju.edu.cn/api/jeecg-boot/jcedutec/exam/unCorrect?_t={t}&id={exam_id}&type=2"
resp3 = requests.get(wrong_url, headers=headers, cookies=cookies)
wrong_questions = resp3.json().get("result", [])

print(f"发现 {len(wrong_questions)} 道错题")

# === Step 5: 更新题库（保存为文本列表，支持多选） ===
new_entries = 0
for q in wrong_questions:
    stem = q["stem"]

    # 拿到正确答案的字母串，如 "A,B,D"
    correct_letters = q.get("correctAnswer") or ""
    letters = [c.strip() for c in correct_letters.split(",") if c.strip()]

    # 把字母转成文本
    correct_texts = []
    mapping = {"A": "optiona", "B": "optionb", "C": "optionc", "D": "optiond"}
    for l in letters:
        opt_key = mapping.get(l.upper())
        if opt_key and q.get(opt_key):
            correct_texts.append(q[opt_key])

    # 存入题库
    if stem and correct_texts:
        if stem not in my_bank:
            my_bank[stem] = correct_texts
            new_entries += 1

if new_entries > 0:
    with open(bank_file, "w", encoding="utf-8") as f:
        json.dump(my_bank, f, ensure_ascii=False, indent=2)
    print(f"📚 题库已更新，新增 {new_entries} 道题")
else:
    print("📚 没有新错题需要更新题库")