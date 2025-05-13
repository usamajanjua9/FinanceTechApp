import streamlit as st
import json
import pandas as pd
import random
import os
import time

# -----------------------------
# File paths
# -----------------------------
SCORE_FILE = "user_scores.csv"
MCQ_FILE = "ai_finance_mcqs.json"

# -----------------------------
# Load Questions
# -----------------------------
def load_mcqs():
    with open(MCQ_FILE, "r") as f:
        return json.load(f)

# -----------------------------
# Get 20 shuffled MCQs per user (based on roll number seed)
# -----------------------------
def get_user_mcqs(seed):
    random.seed(seed)
    questions = load_mcqs()
    random.shuffle(questions)
    return questions[:20]

# -----------------------------
# Load or Initialize Scores
# -----------------------------
def load_scores():
    if os.path.exists(SCORE_FILE):
        return pd.read_csv(SCORE_FILE)
    else:
        return pd.DataFrame(columns=["RollNumber", "Name", "Score"])

def save_score(roll_number, name, score):
    scores_df = load_scores()
    new_entry = pd.DataFrame([{"RollNumber": roll_number, "Name": name, "Score": score}])
    scores_df = pd.concat([scores_df, new_entry], ignore_index=True)
    scores_df.to_csv(SCORE_FILE, index=False)

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="AI Finance Battleboard", layout="centered")
st.title("🎮 AI Finance Battleboard")
st.markdown("Test your knowledge of AI + Finance in this interactive classroom game. You only get **one attempt**, so make it count! 🎯")

# -----------------------------
# User Login
# -----------------------------
if "started" not in st.session_state:
    with st.form("user_login"):
        roll_number = st.text_input("🔐 Roll Number")
        name = st.text_input("👤 Full Name")
        submit_login = st.form_submit_button("🚀 Start Game")

    if submit_login and roll_number and name:
        scores_df = load_scores()
        if roll_number in scores_df["RollNumber"].values:
            st.warning("❌ You have already played the game. Only one attempt allowed per roll number.")
        else:
            # Initialize session state
            st.session_state.questions = get_user_mcqs(seed=roll_number)
            st.session_state.current_q = 0
            st.session_state.responses = {}
            st.session_state.score = 0
            st.session_state.roll_number = roll_number
            st.session_state.name = name
            st.session_state.start_time = time.time()
            st.session_state.finished = False
            st.session_state.started = True
            st.experimental_rerun()

# -----------------------------
# Quiz Interface
# -----------------------------
if st.session_state.get("started") and not st.session_state.get("finished", False):
    questions = st.session_state.questions
    q_index = st.session_state.current_q

    if q_index < len(questions):
        q = questions[q_index]
        st.header(f"📘 Question {q_index + 1}/20")
        st.markdown(f"**{q['question']}**")
        selected = st.radio("Choose one:", q["options"], key=f"q_{q_index}")

        # Timer
        elapsed = time.time() - st.session_state.start_time
        remaining = max(0, 30 - int(elapsed))
        st.info(f"⏳ Time left: {remaining} seconds")

        if remaining == 0:
            st.warning("⏰ Time's up! Moving to next question.")
            st.session_state.current_q += 1
            st.session_state.start_time = time.time()
            st.experimental_rerun()

        if st.button("✅ Lock Answer"):
            st.session_state.responses[q_index] = selected
            if selected == q["answer"]:
                st.session_state.score += 1
            st.session_state.current_q += 1
            st.session_state.start_time = time.time()
            st.experimental_rerun()
    else:
        st.success("🎉 You've completed all questions!")
        save_score(
            st.session_state.roll_number,
            st.session_state.name,
            st.session_state.score
        )
        st.session_state.finished = True
        st.experimental_rerun()

# -----------------------------
# Final Score Summary
# -----------------------------
if st.session_state.get("finished", False):
    st.balloons()
    st.header("🎯 Quiz Completed!")
    st.subheader(f"🙋 Name: {st.session_state.name}")
    st.subheader(f"🆔 Roll Number: {st.session_state.roll_number}")
    st.subheader(f"🏁 Final Score: {st.session_state.score} / 20")

# -----------------------------
# Leaderboard + Download
# -----------------------------
st.markdown("---")
if st.checkbox("📊 Show Leaderboard"):
    leaderboard = load_scores().sort_values(by="Score", ascending=False).reset_index(drop=True)
    if leaderboard.empty:
        st.info("No one has played yet.")
    else:
        st.subheader("🏆 Leaderboard")
        st.dataframe(leaderboard)

        top_score = leaderboard.iloc[0]["Score"]
        winners = leaderboard[leaderboard["Score"] == top_score]["Name"].tolist()
        st.markdown(f"🥇 **Top Scorer(s)**: {', '.join(winners)} with {top_score} points")

        # Download CSV
        csv = leaderboard.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Leaderboard as CSV",
            data=csv,
            file_name='AI_Finance_Leaderboard.csv',
            mime='text/csv',
        )
