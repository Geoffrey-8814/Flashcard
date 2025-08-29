import streamlit as st
import pdfplumber
import pandas as pd
import time
import tempfile
from gtts import gTTS

# ========== PDF 解析 ==========
@st.cache_data
def load_pdf(path):
    words = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue
            for row in table[1:]:
                if len(row) < 5:
                    continue
                try:
                    idx = int(row[0])
                except:
                    continue
                w = (row[2] or "").strip()
                cn = (row[3] or "").strip()
                en = (row[4] or "").strip()
                words.append({"序号": idx, "单词": w, "中文": cn, "英文": en})
    return pd.DataFrame(words).drop_duplicates(["序号"]).sort_values("序号").reset_index(drop=True)


def speak_word(word):
    tts = gTTS(text=word, lang="en", tld="com")  # com 默认就是美式
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name

path = "Barron词汇"

# ========== 初始化 ==========
df = load_pdf(f"{path}.pdf")  # 改成你的路径
st.title(f"📚 {path} Flashcards")

start = st.number_input("起始序号", min_value=int(df['序号'].min()), max_value=int(df['序号'].max()), value=int(df['序号'].min()))
end = st.number_input("结束序号", min_value=int(df['序号'].min()), max_value=int(df['序号'].max()), value=int(df['序号'].min())+19)

subset = df[(df["序号"] >= start) & (df["序号"] <= end)].reset_index(drop=True)

# session_state
if "progress" not in st.session_state:
    st.session_state.progress = {}  # {序号: 熟练度}
if "remaining" not in st.session_state or st.session_state.get("_range") != (start, end):
    st.session_state._range = (start, end)
    st.session_state.remaining = [int(x) for x in subset["序号"].tolist()]
    for sid in st.session_state.remaining:
        st.session_state.progress.setdefault(sid, 0)
    st.session_state.current_pos = 0
if "show_meaning" not in st.session_state:
    st.session_state.show_meaning = False  # 控制显示/隐藏释义


# ========== 统计完成度 ==========
total = len(subset)
done = total-len(st.session_state.remaining)
st.progress(done / total if total > 0 else 0)
st.caption(f"完成度: {done}/{total}")

def moveToNext():
    # 模拟过渡效果
            placeholder = st.empty()
            placeholder.markdown("⏭ 正在切换下一个单词...")
            st.session_state.show_meaning = False
            time.sleep(0.1)
            placeholder.empty()
            st.rerun()

# ========== 主逻辑 ==========
if len(st.session_state.remaining) == 0:
    st.success("🎉 恭喜，范围内的单词都掌握了！")
    st.stop()  # 提前结束
else:
    if st.session_state.current_pos >= len(st.session_state.remaining):
        st.session_state.current_pos = 0
    current_id = st.session_state.remaining[st.session_state.current_pos]
    row = subset[subset["序号"] == current_id].iloc[0]
    word = row["单词"]
    st.header(word)
    
    if st.button("🔊 发音"):
        mp3_file = speak_word(word)
        st.audio(mp3_file, format="audio/mp3")

    # 当前熟练度
    st.write(f"当前熟练度：{st.session_state.progress.get(current_id,0)}/3")

    # 切换显示释义
    if st.button("显示/隐藏 释义", key=f"toggle_{current_id}"):
        st.session_state.show_meaning = not st.session_state.show_meaning

    if st.session_state.show_meaning:
        st.info(f"中文: {row['中文']}\n\n英文: {row['英文']}")

    # 按钮逻辑
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 会了", key=f"know_{current_id}"):
            st.session_state.progress[current_id] = st.session_state.progress.get(current_id, 0) + 1
            if st.session_state.progress[current_id] >= 3:
                st.success(f"{row['单词']} 已掌握 ✅")
                st.session_state.remaining.pop(st.session_state.current_pos)
            else:
                st.session_state.current_pos = (st.session_state.current_pos + 1) % len(st.session_state.remaining)

            moveToNext()

    with col2:
        if st.button("❌ 不会", key=f"unk_{current_id}"):
            st.session_state.progress[current_id] = 0
            st.session_state.current_pos = (st.session_state.current_pos + 1) % len(st.session_state.remaining)

            moveToNext()
