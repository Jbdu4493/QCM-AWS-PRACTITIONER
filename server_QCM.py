from flask import Flask, render_template, request
import json
import random
app = Flask(__name__)
import re
import webbrowser

def decompose(qr):
    result = dict()
    result["question"]=qr[0]
    valid = list()
    reponse = list()
    for r in qr[1:]:
        if '@' in r:
            valid.append(1)
            reponse.append(r[:-1])
        else:
            valid.append(0)
            reponse.append(r)
    result['reponses'] = reponse
    result["valid"] = valid
    return result
def create_questions():
    f = open("/Users/jonathanbizet/Documents/Formation_IA/QGM/Reponses.txt",'r')
    lines = f.read().split('\n')
    text = "".join(lines)
    question = re.split('Question\d?\d',text)
    list_question_reponse = list(map(lambda x :re.split('[A-Z]\. ',x),question))[1:]        
    questions = list(map(decompose,list_question_reponse))
    questions = random.sample(questions, 20)
    return questions
questions = create_questions()
# Page d'accueil
@app.route('/')
def index():
    global questions
    questions = create_questions()
    radio = [ "radio" if sum(q['valid']) == 1 else "checkbox" for q in questions ]
    return render_template('index.html', questions=enumerate(questions),radio = radio )

@app.route('/result', methods=['POST'])
def result():
    global questions
    responses = []
    user_reponses = list()
    for i in range(len(questions)):
        nb_reponse=len(questions[i]["valid"])
        user_reponse = [0 for j in range(nb_reponse)]
        for j in request.form.getlist(f"question_{i}"):
            user_reponse[int(j)]=1

        user_reponses.append(user_reponse)
    all_colors = list()
    for res, usr_res in  zip(map(lambda x :x["valid"],questions), user_reponses):
        color = ['normal' for i in range(len(usr_res))]
        for r,ur,i in zip(res, usr_res,range(len(res))):
            if r == 1:
                if ur == r:
                   color[i]='correct'  
                else:
                    color[i]='incorrect'
            if r == 0:
                 if not(ur == r):
                    color[i]='incorrect'
        all_colors.append(color)
       
    radio = [ "radio" if sum(q['valid']) == 1 else "checkbox" for q in questions ]
    percentage = (1 - (sum(['incorrect' in color for color in all_colors ])/len(all_colors)))*100
    return render_template('result.html', percentage=percentage,
                           questions = enumerate(questions),
                           user_reponses = user_reponses,
                           all_colors=all_colors,
                           radio = radio)  # Envoyez les réponses valides
import webbrowser
import asyncio
import time

    
if __name__ == '__main__':
    app.run(debug=True)
    

