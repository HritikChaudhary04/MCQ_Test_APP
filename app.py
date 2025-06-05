import streamlit as st
import json
import random
import time
import csv
from pathlib import Path
from datetime import datetime

# File paths
QUESTIONS_FILE = "engineering_mcqs.json"
HISTORY_FILE = "score_history.json"
ADMIN_PASSWORD = "adminaccess"

# Load questions
@st.cache_data
def load_questions():
    with open(QUESTIONS_FILE, "r") as f:
        return json.load(f)

# Load history
def load_history():
    if Path(HISTORY_FILE).exists():
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

# Save history
def save_history(data):
    with open(HISTORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def download_csv(data, username):
    filename = f"{username}_result.csv"
    path = Path(filename)  # Local directory instead of /mnt/data
    with open(path, "w", newline="", encoding="utf-8") as f:  # added encoding here too
        writer = csv.writer(f)
        writer.writerow(["Question", "Your Answer", "Correct Answer", "Status"])
        for row in data:
            writer.writerow([row["question"], row["selected"], row["correct"], row["status"]])
    return path



# Download full history CSV
def export_full_history(history):
    filename = "full_score_history.csv"
    path = Path("full_score_history.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["User", "Score", "Total", "Time", "Date"])
        for record in history:
            writer.writerow([record["user"], record["score"], record["total"], record["time"], record.get("date", "")])
    return path

# Load data
questions_data = load_questions()
history_data = load_history()
questions_data = [q for q in questions_data if isinstance(q.get("options"), list) and len(q["options"]) == 4 and q.get("answer") in q["options"]]


# Title
st.title("🧠 Engineering Management MCQ Test")

menu = st.sidebar.radio("Menu", ["Take Test", "Admin Panel"])

# --------------------------- TEST MODE --------------------------
if menu == "Take Test":
    username = st.text_input("Enter your name to begin:")
    num_questions = st.selectbox("Select number of questions:", [5, 10, 20,30,40,50,60,70,80,90,100])

    if "started" not in st.session_state:
        st.session_state.started = False

    if st.button("Start Test"):
        if username.strip() == "":
            st.warning("Please enter your name.")
        else:
            st.session_state.started = True
            st.session_state.start_time = time.time()
            st.session_state.selected_questions = random.sample(questions_data, num_questions)
            st.session_state.responses = {}

    if st.session_state.get("started", False):
        for idx, q in enumerate(st.session_state.selected_questions):
            if 'options' in q and isinstance(q['options'], list) and len(q['options']) == 4:
                 st.session_state.responses[idx] = st.radio(
                    f"Q{idx+1}: {q['question']}",
                    q['options'],
                    index=None,
                    key=f"q{idx}"
                )
        else:
            st.warning(f"⚠️ Skipping malformed question {idx+1}. It doesn't have 4 options.")

        if st.button("Submit Test"):
            end_time = time.time()
            time_taken = int(end_time - st.session_state.start_time)
            limit = num_questions * 60
            score = 0
            review = []

            for idx, q in enumerate(st.session_state.selected_questions):
                selected = st.session_state.responses.get(idx, "")
                correct = q["answer"]
                result = "✅" if selected == correct else "❌"
                review.append({
                    "question": q["question"],
                    "selected": selected,
                    "correct": correct,
                    "status": result
                })
                if selected == correct:
                    score += 1

            st.session_state.started = False
            st.markdown("### ✅ Test Completed")
            if time_taken > limit:
                st.error(f"⏱ Time exceeded! Limit was {limit}s, you took {time_taken}s.")
            else:
                st.success(f"🎯 {username} scored {score}/{num_questions}")
                st.info(f"⏳ Time taken: {time_taken} seconds")

                # Save result
                history_data.append({
                    "user": username,
                    "score": score,
                    "total": num_questions,
                    "time": time_taken,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                save_history(history_data)

                # Review answers
                st.markdown("### 📘 Review Answers")
                for r in review:
                    st.write(f"{r['status']} **{r['question']}**")
                    st.write(f"- Your answer: *{r['selected']}*")
                    st.write(f"- Correct answer: *{r['correct']}*")
                    st.markdown("---")

                # Download report
                csv_file = download_csv(review, username)
                st.download_button("📄 Download Your Result (CSV)", data=csv_file.read_bytes(), file_name=csv_file.name)

# --------------------------- ADMIN PANEL --------------------------
elif menu == "Admin Panel":
    pwd = st.text_input("Enter admin password:", type="password")
    if pwd == ADMIN_PASSWORD:
        st.success("Welcome, Admin!")

        # Score history
        st.markdown("### 📊 Score History")
        user_filter = st.text_input("Filter by username (optional):").strip().lower()
        filtered = [h for h in history_data if user_filter in h["user"].lower()] if user_filter else history_data

        if filtered:
            for rec in reversed(filtered[-20:]):
                st.write(f"{rec['date']} - **{rec['user']}**: {rec['score']}/{rec['total']} in {rec['time']}s")
        else:
            st.info("No records found.")

        # Download all scores
        csv_path = export_full_history(history_data)
        st.download_button("📥 Download All Scores (CSV)", data=csv_path.read_bytes(), file_name=csv_path.name)

        # Reset
        if st.button("⚠️ Clear All Test History"):
            save_history([])
            st.warning("All score history has been cleared. Please refresh.")
    else:
        st.info("Enter password to access the admin panel.")
