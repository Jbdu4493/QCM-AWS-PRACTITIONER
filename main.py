import streamlit as st
import json
import random

def run():
    st.set_page_config(
        page_title="Streamlit quizz app",
        page_icon="❓",
    )
nb_quest = 20
if __name__ == "__main__":
    run()

# Custom CSS for the buttons
st.markdown("""
<style>
div.stButton > button:first-child {
    display: block;
    margin: 0 auto;
</style>
""", unsafe_allow_html=True)

# Initialize session variables if they do not exist
default_values = {'current_index': 0, 'current_question': 0, 'score': 0, 'selected_option': None, 'answer_submitted': False}
for key, value in default_values.items():
    st.session_state.setdefault(key, value)

# Load quiz data
if "quiz_data" not in  st.session_state:
    with open('./quizz_question.json', 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)
        st.session_state.quiz_data = random.choices(quiz_data,k=nb_quest)

def restart_quiz():
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    with open('./quizz_question.json', 'r', encoding='utf-8') as f:
        quiz_data = json.load(f)
        st.session_state.quiz_data = random.choices(quiz_data,k=nb_quest)


def submit_answer():

    # Check if an option has been selected
    if st.session_state.selected_option is not None:
        # Mark the answer as submitted
        st.session_state.answer_submitted = True
        # Check if the selected option is correct
        if st.session_state.selected_option == st.session_state.quiz_data[st.session_state.current_index]['answer']:
            st.session_state.score += 1
    else:
        # If no option selected, show a message and do not mark as submitted
        st.warning("Please select an option before submitting.")

def next_question():
    st.session_state.current_index += 1
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False

# Title and description
st.title("Streamlit Quiz App")

# Progress bar
progress_bar_value = (st.session_state.current_index + 1) / nb_quest
score = st.session_state.score*100/st.session_state.current_index if st.session_state.current_index != 0 else 0
st.metric(label="Score", value=f"{score:.1f} %")
st.progress(progress_bar_value)

# Display the question and answer options
question_item = st.session_state.quiz_data[st.session_state.current_index]
st.subheader(f"Question {st.session_state.current_index + 1}")
st.write(f"#### {question_item['question']}")

st.markdown(""" ___""")

# Answer selection
options = question_item['options']
correct_answer = question_item['answer']

if st.session_state.answer_submitted:
    for i, option in enumerate(options):
        label = option
        if option == correct_answer:
            st.success(f"{label} (Correct answer)")
        elif option == st.session_state.selected_option:
            st.error(f"{label} (Incorrect answer)")
        else:
            st.write(label)
else:
    for i, option in enumerate(options):
        if st.button(option, key=i, use_container_width=True):
            st.session_state.selected_option = option

st.markdown(""" ___""")

# Submission button and response logic
if st.session_state.answer_submitted:
    if st.session_state.current_index < nb_quest - 1:
        st.button('Next', on_click=next_question)
    else:
        st.write(f"### Quiz completed! Your score is: {st.session_state.score*100/nb_quest:.1f}")
        col = st.columns(5,gap='large')
        with col[0]:
            if st.button('Restart', on_click=restart_quiz):
                pass
else:
    if st.session_state.current_index < nb_quest:
        st.button('Submit', on_click=submit_answer)