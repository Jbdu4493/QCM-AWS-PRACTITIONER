import streamlit as st
import json
import random
import requests
from requests.exceptions import RequestException
import random

api_url = "https://jv6gjfb6zh.execute-api.eu-west-3.amazonaws.com/v1"


def get_event(theme):
    try:
        response = requests.get(f"{api_url}/event", params={'theme': theme})
        response.raise_for_status()  # Raise an exception for non-2xx status codes

        return response.json()
    except RequestException as e:
        print(f"An error occurred: {e}")
        return []


def get_question_by_id(id_questions: list[str]):
    try:
        list_question = list()
        for id_question in id_questions:
            response = requests.get(f"{api_url}/question/{id_question}")
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            list_question.append(response.json())
        return list_question
    except RequestException as e:
        print(f"An error occurred: {e}")
        return []


def selection_type_examen():
    import pandas as pd
    selected_id_question = list()
    response = requests.get(f"{api_url}/theme/TYPE-EXAMEN")
    question_examen = response.json()
    question_examen_filter = list(
        filter(lambda q: "&&" not in q["answer"], question_examen))
    df_event = pd.DataFrame(get_event("TYPE-EXAMEN"))
    df_event_ko = df_event[df_event['event-type'] == "KO"]
    most_ko_question = df_event_ko.groupby(by='id-question')\
        .count()[["id-event"]]\
        .sort_values(by="id-event", ascending=False)\
        .head(65).index.to_list()

    question = list(
        set(map(lambda x: x["id-question"], question_examen_filter)))
    question_nerver_asked = list(
        filter(lambda x: x not in set(df_event["id-question"]), question))
    asked_question = df_event.sort_values(by=["timestamp"])[
        'id-question'].to_list()
    selected_id_question += question_nerver_asked
    selected_id_question += most_ko_question
    selected_id_question = list(set(selected_id_question))
    if len(selected_id_question) > 65:
        selected_id_question = selected_id_question[:65]
    elif len(selected_id_question) < 65:
        selected_id_question += asked_question[:65-len(selected_id_question)]
    return list(filter(lambda x: x['id-question'] in selected_id_question,  question_examen_filter))


def get_question_by_theme(theme):
    response = requests.get(f"{api_url}/theme/{theme}")
    response.raise_for_status()  # Raise an exception for non-2xx status codes
    try:
        data = list()
        if theme == "TYPE-EXAMEN":
            questions = selection_type_examen()
            for q in questions:
                if "&&" not in q["answer"]:
                    data.append(q)
            random.shuffle(data)
            shuffler_answer(data)
            return data

        return response.json()
    except RequestException as e:
        print(f"An error occurred: {e}")
        return []


def post_event(id_question, event_type, theme):
    reponse = requests.post(api_url+"/event/", params={
                            "id-question": id_question, "event-type": event_type, "theme": theme})

    return reponse.json()


def get_all_theme():
    try:
        if "all_theme" in st.session_state:
            return st.session_state.all_theme
        else:
            reponse = requests.get(api_url+"/theme/")
            reponse.raise_for_status()
            st.session_state.all_theme = reponse.json()
            return st.session_state.all_theme
    except RequestException as e:
        print(f"An error occurred: {e}")
        return []


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

        question_data = get_question_filter()
        random.shuffle(question_data)
        if len(question_data) > 65:
            st.session_state.quiz_data = question_data[:65]
        else:
            st.session_state.quiz_data = question_data

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


log = st.sidebar.checkbox("Log statistique", value=True)
st.session_state['stat'] = log


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


def load_event_data():
    for ts in st.session_state["theme_stat"]:
        if "event-"+ts not in st.session_state:
            json_data = get_event(ts)
            json_data = json.dumps(json_data)
            df = pd.read_json(StringIO(json_data))
            st.session_state["event-"+ts] = df

# concate all df of event in one df


def concat_df_event():
    df_all = pd.DataFrame()
    for ts in st.session_state["theme_stat"]:
        if "event-"+ts in st.session_state:
            df = st.session_state["event-"+ts]
            df_all = pd.concat([df_all, df])
    return df_all


with stat:
    import pandas as pd
    from io import StringIO
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    st.session_state['theme_stat'] = get_all_theme()
    st.button("Analyser", key="stat-load", on_click=load_event_data)

    st.session_state['theme_stat'] = get_all_theme()
    if "theme_stat" in st.session_state and len(st.session_state.theme_stat) != 0:
        # Charger les données
        df = concat_df_event()
        if df.shape[0] != 0:
            # Convertir la colonne 'timestamp' en objet datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.reset_index(inplace=True, drop=True)
            # Titre du tableau de bord
            st.title("Tableau de Bord des Résultats")

            st.header(
                "Nombre de questions par thème (trié) avec distinction OK/KO")
            # Calculer la proportion de OK/KO par thème
            proportion_ok_ko = df.groupby(
                'theme')['event-type'].value_counts(normalize=True).unstack().fillna(0)

            # Trier les thèmes par proportion de KO décroissante
            proportion_ok_ko = proportion_ok_ko.sort_values(
                by='OK', ascending=False)

            # Générer le graphique trié
            fig4, ax4 = plt.subplots(figsize=(10, 6))

            # Barres empilées pour OK/KO
            proportion_ok_ko.plot(kind='bar', stacked=True, ax=ax4)

            # Titre et labels
            ax4.set_title(
                'Proportion de OK/KO par thème (trié par proportion de KO)')
            ax4.set_ylabel('Proportion')
            ax4.set_xlabel('Thème')
            ax4.set_xticklabels(ax4.get_xticklabels(), rotation=45, ha='right')

            # Légende
            ax4.legend(['KO', "OK"], loc='upper right')

            plt.tight_layout()
            st.pyplot(fig4)

           # Trier le dernier graphique en fonction du nombre total de questions
            st.header(
                "Nombre de questions par thème (trié) avec distinction OK/KO")

            # Calculer le nombre de questions par thème avec distinction OK/KO
            questions_per_theme_result = df.groupby(
                ['theme', 'event-type']).size().unstack().fillna(0)

            # Calculer le total des questions par thème
            questions_per_theme_result['Total'] = questions_per_theme_result.sum(
                axis=1)

            # Trier les thèmes par le nombre total de questions en ordre décroissant
            questions_per_theme_result = questions_per_theme_result.sort_values(
                by='Total', ascending=False)

            # Supprimer la colonne Total pour ne garder que OK/KO dans le graphique
            questions_per_theme_result = questions_per_theme_result.drop(columns=[
                                                                         'Total'])

            # Générer le graphique trié
            fig, ax = plt.subplots(figsize=(10, 6))

            # Barres empilées pour OK/KO
            questions_per_theme_result.plot(kind='bar', stacked=True, ax=ax)

            # Titre et labels
            ax.set_title(
                'Nombre de questions par thème avec distinction OK/KO (trié par nombre total)')
            ax.set_ylabel('Nombre de questions')
            ax.set_xlabel('Thème')
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')

            # Légende
            ax.legend(['KO', 'OK'], loc='upper right')

            plt.tight_layout()  # Pour éviter les chevauchements
            st.pyplot(fig)

            # 2. Pourcentage de OK par jour
            st.header("Pourcentage de OK par jour")
            df_unique = df.drop_duplicates(subset=['timestamp', 'event-type'])
            ok_counts = df_unique[df_unique['event-type'] ==
                                  'OK'].groupby(df_unique['timestamp'].dt.date).size()
            total_counts = df_unique.groupby(
                df_unique['timestamp'].dt.date).size()
            percentage_ok_per_day = (ok_counts / total_counts) * 100

            # Convertir l'index en datetime si nécessaire
            percentage_ok_per_day.index = pd.to_datetime(
                percentage_ok_per_day.index)

            fig2, ax2 = plt.subplots(figsize=(10, 6))
            percentage_ok_per_day.plot(kind='line', ax=ax2)
            ax2.set_title('Pourcentage de OK par jour')
            ax2.set_ylabel('Pourcentage de OK')
            ax2.set_xlabel('Date')

            # Utiliser Matplotlib Dates pour améliorer l'affichage des dates
            ax2.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

            fig2.autofmt_xdate()  # Pour améliorer la lisibilité des dates
            plt.tight_layout()  # Pour éviter les chevauchements
            st.pyplot(fig2)

            # 3. Nombre de questions par jour
            st.header("Nombre de questions par jour")
            questions_per_day = df_unique.groupby(
                df_unique['timestamp'].dt.date).size()
            # Convertir l'index en datetime si nécessaire
            questions_per_day.index = pd.to_datetime(questions_per_day.index)

            fig3, ax3 = plt.subplots(figsize=(10, 6))
            questions_per_day.plot(kind='bar', ax=ax3)
            ax3.set_title('Nombre de questions par jour')
            ax3.set_ylabel('Nombre de questions')
            ax3.set_xlabel('Date')
            # Convertir les dates en chaînes de caractères au format souhaité
            formatted_dates_qpd = questions_per_day.index.strftime('%Y-%m-%d')
            # Configurer les ticks pour chaque point de données
            ax3.set_xticks(range(len(formatted_dates_qpd)))
            ax3.set_xticklabels(formatted_dates_qpd, rotation=45, ha='right')
            st.pyplot(fig3)

            # Trier le dernier graphique en fonction du nombre total de questions
