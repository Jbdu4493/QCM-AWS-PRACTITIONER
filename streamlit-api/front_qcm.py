import streamlit as st
import json
import random
import requests
from requests.exceptions import RequestException
import random

api_url = "https://jv6gjfb6zh.execute-api.eu-west-3.amazonaws.com/v1"


def get_question_by_theme(theme):
    try:
        response = requests.get(f"{api_url}/theme/{theme}")
        response.raise_for_status()  # Raise an exception for non-2xx status codes
        return response.json()
    except RequestException as e:
        print(f"An error occurred: {e}")
        return []


def post_event(id_question, event_type, theme):
    reponse = requests.post(api_url+"/add_event/", params={
                            "id-question": id_question, "event-type": event_type, "theme": theme})

    return reponse.json()


def get_all_theme():
    reponse = requests.get(api_url+"/theme/")
    return reponse.json()


def shuffler_answer(quiz):
    for i in range(len(quiz)):
        random.shuffle(quiz[i]["options"])


def run():
    st.set_page_config(
        page_title="AWS QUIZZ",
        page_icon="💻",
    )


def restart_quiz():
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False


def main_page():
    pass


def side_bar():
    pass


if __name__ == "__main__":
    run()
    main_page()
    side_bar()


# Custom CSS for the buttons
st.markdown("""
<style>
div.stButton > button:first-child {
    display: block;
    margin: 0 auto;
</style>
""", unsafe_allow_html=True)

# Initialize session variables if they do not exist
default_values = {'current_index': 0, 'current_question': 0,
                  'score': 0, 'selected_option': None, 'answer_submitted': False}
for key, value in default_values.items():
    st.session_state.setdefault(key, value)

# Load quiz data

# if "quiz_data" not in  st.session_state:
#    load_quizz()


def get_question_filter():
    questions = list()
    for t in st.session_state.selected_theme:
        questions = questions + get_question_by_theme(t)
    for q in questions:
        random.shuffle(q["options"])
    return questions


def filter_quizz():
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    if st.session_state.selected_theme:

        st.session_state.quiz_data = get_question_filter()
        random.shuffle(st.session_state.quiz_data)

    elif st.session_state.selected_theme == []:
        st.write(f"### ◀︎ Aucun thème n'a été choisi ....")


def select_random_theme():
    themes = get_all_theme()
    random.shuffle(themes)
    st.session_state.selected_theme = themes[:4]
    st.session_state.current_index = 0
    st.session_state.score = 0
    st.session_state.selected_option = None
    st.session_state.answer_submitted = False
    if st.session_state.selected_theme:
        st.session_state.quiz_data = get_question_filter()
        random.shuffle(st.session_state.quiz_data)
    elif st.session_state.selected_theme == []:
        st.write(f"### ◀︎ Aucun thème n'a été choisi ....")


themes = get_all_theme()
themes.sort()
add_selectbox = st.sidebar.multiselect(
    "Wich themes would you like to be choose?",
    themes
)
st.session_state['selected_theme'] = add_selectbox
col1, col2 = st.sidebar.columns(2)


with col1:
    st.sidebar.button('Random 4', on_click=select_random_theme)
with col2:
    st.sidebar.button('Filtrer', on_click=filter_quizz)


stats = st.sidebar.checkbox("Log statistique", value=True)
st.session_state['stat'] = stats


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


qcm, stat = st.tabs(["QCM", "STATISTIQUE"])


with qcm:
    # Title and description
    st.title("Streamlit Quiz App")
    if "quiz_data" in st.session_state:
        # Progress bar
        progress_bar_value = (
            st.session_state.current_index + 1) / len(st.session_state.quiz_data)
        if st.session_state.answer_submitted:
            score = (st.session_state.score*100)/(st.session_state.current_index +
                                                  1) if st.session_state.current_index != 0 else 0
        else:
            score = (st.session_state.score*100) / \
                (st.session_state.current_index) if st.session_state.current_index != 0 else 0
        st.metric(label="Score", value=f"{score:.1f} %")
        st.progress(progress_bar_value)

        # Display the question and answer options
        question_item = st.session_state.quiz_data[st.session_state.current_index]
        st.subheader(
            f"Question {st.session_state.current_index + 1} sur {len(st.session_state.quiz_data )}")
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
                    if st.session_state['stat']:
                        post_event(
                            question_item["id-question"], "OK", question_item["theme"])
                elif option == st.session_state.selected_option:
                    st.error(f"{label} (Incorrect answer)")
                    if st.session_state['stat']:
                        post_event(
                            question_item["id-question"], "KO", question_item["theme"])

                else:
                    st.write(label)
        else:
            for i, option in enumerate(options):
                if st.button(option, key=i, use_container_width=True):
                    st.session_state.selected_option = option

        st.markdown(""" ___""")

        # Submission button and response logic
        if st.session_state.answer_submitted:
            if st.session_state.current_index < len(st.session_state.quiz_data) - 1:
                st.button('Next', on_click=next_question)
            else:
                st.write(
                    f"### Quiz completed! Your score is: {st.session_state.score*100/len(st.session_state.quiz_data ):.1f}")
                col = st.columns(5, gap='large')
        else:
            if st.session_state.current_index < len(st.session_state.quiz_data):
                st.button('Submit', on_click=submit_answer)
    else:
        st.write(f"### ◀︎ Aucun thème n'a été choisi ....")
