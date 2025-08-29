from gtts import gTTS
import streamlit as st
import os
import tempfile

def speak_word(word):
    tts = gTTS(text=word, lang="en", tld="com")  # com 默认就是美式
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(tmp.name)
    return tmp.name

word = "example"
st.write(word)

if st.button("🔊 播放发音"):
    mp3_file = speak_word(word)
    st.audio(mp3_file, format="audio/mp3")
