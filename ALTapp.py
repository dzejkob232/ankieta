# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import uuid
import random
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure secret key

DATABASE = 'responses.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            respondent_id TEXT PRIMARY KEY,
            treatment_id INTEGER,
            page1_answer INTEGER,
            page2_answer1 INTEGER,
            page2_answer2 INTEGER,
            page2_answer3 INTEGER,
            page3_answer1 INTEGER,
            page3_answer2 INTEGER,
            page3_answer3 INTEGER,
            page3_answer4 INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def save_response(respondent_id, data):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    placeholders = ', '.join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [respondent_id]
    query = f"UPDATE responses SET {placeholders} WHERE respondent_id = ?"
    c.execute(query, values)
    conn.commit()
    conn.close()

def insert_new_respondent(respondent_id, treatment_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO responses (respondent_id, treatment_id)
        VALUES (?, ?)
    ''', (respondent_id, treatment_id))
    conn.commit()
    conn.close()

def export_to_csv():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT * FROM responses')
    rows = c.fetchall()
    headers = [description[0] for description in c.description]
    conn.close()

    with open('responses.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

@app.route('/')
def index():
    # Assign a unique respondent ID and treatment ID if not already assigned
    if 'respondent_id' not in session:
        respondent_id = str(uuid.uuid4())
        treatment_id = random.choice([0, 1, 2, 3, 4])
        session['respondent_id'] = respondent_id
        session['treatment_id'] = treatment_id
        insert_new_respondent(respondent_id, treatment_id)
    else:
        respondent_id = session['respondent_id']
        treatment_id = session['treatment_id']
    return redirect(url_for('page1'))

@app.route('/page1', methods=['GET', 'POST'])
def page1():
    """
    Handle Page 1: Single choice with randomized treatment-based question.
    """
    treatment_id = session['treatment_id']
    
    # Define different questions based on treatment_id
    questions = {
    
        0: "0 Na koncie w funduszu emerytalnym oszczędziłeś 200 tys. złotych. Wybierz, w jaki sposób wolałbyś otrzymać środki przechodząc na emeryturę: Wypłata natychmiast całej sumy ALBO comiesięczna renta 1000 zł wypłacana do końca życia. (przy przeciętnej dalszej długości życia, 18 lat x 12 mies. x 1000zł ≈ 2000zł)",
        1: "1 Na koncie w funduszu emerytalnym oszczędziłeś 200 tys. złotych. Wybierz, w jaki sposób wolałbyś otrzymać środki przechodząc na emeryturę: Wypłata natychmiast całej sumy ALBO comiesięczna renta 1000 zł wypłacana do końca życia, która gwarantuje ci stały dochód przez całą emeryturę. (przy przeciętnej dalszej długości życia, 18 lat x 12 mies. x 1000zł ≈ 2000zł)",
        2: "2 Na koncie w funduszu emerytalnym oszczędziłeś 200 tys. złotych. Wybierz, w jaki sposób wolałbyś otrzymać środki przechodząc na emeryturę: Wypłata natychmiast całej sumy ALBO comiesięczna renta 1000 zł wypłacana do końca życia, która nie gwarantuje wypłaty całych oszczędności w razie przedwczesnej śmierci. (przy przeciętnej dalszej długości życia, 18 lat x 12 mies. x 1000zł ≈ 2000zł)",
        3: "3 Na koncie w funduszu emerytalnym oszczędziłeś 200 tys. złotych. Wybierz, w jaki sposób wolałbyś otrzymać środki przechodząc na emeryturę: Wypłata natychmiast całej sumy, którą możesz zarządzać lub inwestować dowolnie ALBO comiesięczna renta 1000 zł wypłacana do końca życia. (przy przeciętnej dalszej długości życia, 18 lat x 12 mies. x 1000zł ≈ 2000zł)",
        4: "4 Na koncie w funduszu emerytalnym oszczędziłeś 200 tys. złotych. Wybierz, w jaki sposób wolałbyś otrzymać środki przechodząc na emeryturę: Wypłata natychmiast całej sumy, która zostawia Cię bez stałego dochodu ALBO comiesięczna renta 1000 zł wypłacana do końca życia. (przy przeciętnej dalszej długości życia, 18 lat x 12 mies. x 1000zł ≈ 2000zł)",
    }
    
    # Fetch the question for the current treatment, or provide a default
    question = questions.get(treatment_id, "placeholder")
    
    PAGE1_OPTIONS = [{"label": "Natychmiastowa wypłata", "value": "0"},
    {"label": "Miesięczna renta do końca życia", "value": "1"}]

    
    if request.method == 'POST':
        selected_option = request.form.get('page1_answer')
        if selected_option not in ['0', '1']:
            error = "Wybór jest nieprawidłowy. Proszę wybierz jedną z opcji."
            randomized_options = random.sample(PAGE1_OPTIONS, len(PAGE1_OPTIONS))
            return render_template('page1.html', treatment_id=treatment_id, options=randomized_options, question=question, error=error)
        save_response(session['respondent_id'], {'page1_answer': selected_option})
        return redirect(url_for('page2'))
    
    # For GET request, randomize the order of options
    randomized_options = random.sample(PAGE1_OPTIONS, len(PAGE1_OPTIONS))
    session['page1_options'] = randomized_options  # Store the order in session
    return render_template('page1.html', treatment_id=treatment_id, options=randomized_options, question=question)


@app.route('/page2', methods=['GET', 'POST'])
def page2():
    if request.method == 'POST':
        try:
            answer1 = int(request.form.get('page2_answer1'))
            answer2 = int(request.form.get('page2_answer2'))
            answer3 = int(request.form.get('page2_answer3'))
            if not all(1 <= ans <= 5 for ans in [answer1, answer2, answer3]):
                raise ValueError
        except (ValueError, TypeError):
            return "Invalid input for Page 2. Please enter numbers between 1 and 5.", 400
        save_response(session['respondent_id'], {
            'page2_answer1': answer1,
            'page2_answer2': answer2,
            'page2_answer3': answer3
        })
        return redirect(url_for('page3'))
    return render_template('page2.html')

@app.route('/page3', methods=['GET', 'POST'])
def page3():
    if request.method == 'POST':
        try:
            answer1 = int(request.form.get('page3_answer1'))
            answer2 = int(request.form.get('page3_answer2'))
            answer3 = int(request.form.get('page3_answer3'))
            answer4 = int(request.form.get('page3_answer4'))
            if not all(0 <= ans <= 100000 for ans in [answer1, answer2, answer3, answer4]):
                raise ValueError
        except (ValueError, TypeError):
            return "Invalid input for Page 3. Please enter numbers between 0 and 100000.", 400
        save_response(session['respondent_id'], {
            'page3_answer1': answer1,
            'page3_answer2': answer2,
            'page3_answer3': answer3,
            'page3_answer4': answer4
        })
        export_to_csv()
        session.clear()
        return render_template('thank_you.html')
    return render_template('page3.html')
    
@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)