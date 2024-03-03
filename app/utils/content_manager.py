
from flask import jsonify
import google.generativeai as genai
import dotenv
import os
import re
from app import socketio
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from flask_socketio import SocketIO, emit
uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.GenQ
dotenv.load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')


#Instructions for the AI to format the content such that it can be parsed consistently
quiz_format_instructions = """
Please generate a set of questions in HTML format suitable for a web quiz application, focusing exclusively on multiple-choice questions (MCQs). Each question should be clearly presented with a question stem followed by several options, each option being a separate line with a radio button input. Ensure each option is within a <label> tag for accessibility. Use unique names for radio button groups based on the question number and provide a placeholder for the option value.

After generating the questions, provide an answer key in a clear, structured format labeled 'ANSWER KEY:' that can be easily parsed. List the correct option letter for each MCQ.

Example format for MCQs:
  <div class='question mcq'>
    <p>1. What is the capital of France?</p>
    <label><input type='radio' name='q1' value='a'>Paris</label><br>
    <label><input type='radio' name='q1' value='b'>London</label><br>
    <label><input type='radio' name='q1' value='c'>Berlin</label><br>
    <label><input type='radio' name='q1' value='d'>Madrid</label>
  </div>

ANSWER KEY:
MCQs:
1. a
"""


guide_format_instructions = """
Generate the content in HTML format. When writing key terms, make sure to define them and highlight them using <b> tags (e.g., "<b>Key Term</b>: Definition").
When writing bullet points, start each point with a dash and a space, and separate them with <br> (e.g., "- This is a bullet point<br>- This is another bullet point").
When writing paragraphs, separate them with <br><br>.
Please include <b> tags around key terms or important concepts to emphasize them.
"""


def load_info(subj_id, top_id, subtop, conc, num, result_type):
    global subject_name
    global topic_name
    global subtopic
    global concept
    global num_questions
    global resultType

    subject_document = db.Subjects.find_one({"_id": ObjectId(subj_id)})
    subject_name = subject_document['name'] if subject_document else 'Unknown Subject'

    topic_document = db.Topics.find_one({"_id": ObjectId(top_id)})
    topic_name = topic_document['name'] if topic_document else 'Unknown Topic'

    subtopic = subtop
    concept = conc
    num_questions = num
    resultType = result_type
    print(f"Subject: {subject_name}, Topic: {topic_name}, Subtopic: {subtopic}, Concept: {concept}, Number of Questions: {num_questions}, Result Type: {resultType}")
    match resultType:
        case "quiz":
            make_quiz(num_questions)
        case "study guide":
            make_study_guide()



def make_quiz(num_questions):
    num_questions = int(num_questions)

    mcqs = multiple_choice_question(num_questions)
    mcqs = parse_quiz(mcqs)
    if mcqs:
        socketio.emit('quizGenerated', {'quiz': mcqs})
    else:
        socketio.emit('quizGenerated', {'quiz': 'Failed to generate quiz.'})

def make_study_guide():
    if concept:
        response = model.generate_content(f"Write a study guide on {concept} in {subtopic} in {topic_name} in {subject_name}" + guide_format_instructions)
    else:
        response = model.generate_content(f"Write a study guide on {subtopic} in {topic_name} in {subject_name}." + guide_format_instructions)
    if response:
        generated_text = response.text
        generated_text = generated_text.replace("```html\n", "")
        generated_text = generated_text.replace("\n```", "")
        socketio.emit('studyGuideGenerated', {'text': generated_text})
    else:
        socketio.emit('studyGuideGenerated', {'text': 'Failed to generate study guide.'})

def short_answer_question(num_frqs):
    if concept:
        response = model.generate_content(f"Write {num_frqs} short-answer questions on {concept} in {subtopic} in {topic_name} in {subject_name}." + quiz_format_instructions)
    else:
        response = model.generate_content(f"Write {num_frqs} short-answer questions on {subtopic} in {topic_name} in {subject_name}."  + quiz_format_instructions)
    if response:
        generated_text = response.text
        generated_text = generated_text.replace("*", "") #AI likes to add * for bolded text, we don't need that
        return generated_text
    else:
        return None

def multiple_choice_question(num_mcqs):
    if concept:
        response = model.generate_content(f"Write {num_mcqs} multiple choice questions on {concept} in {subtopic} in {topic_name} in {subject_name}." + quiz_format_instructions)
    else:
        response = model.generate_content(f"Write {num_mcqs} multiple choice questions on {subtopic} in {topic_name} in {subject_name}." + quiz_format_instructions)
    
    if response:
        generated_text = response.text
        return generated_text.replace("*", "") #AI likes to add * for bolded text, we don't need that
    else:
        return None



def parse_quiz(quiz_text):
    questions_section, answers_section = quiz_text.split("ANSWER KEY:")
    questions = []
    answers = {}
    question_re = re.compile(r"<div class='question mcq'>\s*<p>(\d+)\. (.+?)</p>(.*?)</div>", re.DOTALL)
    option_re = re.compile(r"<label><input type='radio' name='\w+' value='(\w+)'>\s*(.+?)</label>")
    answer_re = re.compile(r"MCQs:\s*((?:\d+\.\s*\w+\s*)*)")

    for match in question_re.finditer(questions_section):
        question_number, question_text, options_html = match.groups()
        question_type = "mcq"
        question_number = int(question_number)
        
        options = option_re.findall(options_html)
        
        questions.append({
            "type": question_type,
            "number": question_number,
            "text": question_text.strip(),
            "options": options
        })

    answer_re = re.compile(r"(\d+)\. (\w)")
    for match in answer_re.finditer(answers_section):
        question_number, correct_option = match.groups()
        answers[int(question_number)] = correct_option.strip()
    return questions, answers


def get_subjects():
    subjects_cursor = db.Subjects.find({}, {'name': 1})
    subjects = []
    for subject in subjects_cursor:
        subject['_id'] = str(subject['_id'])
        subjects.append(subject)
    return subjects 

def get_topics(subject_id):
    topics_cursor = db.Topics.find({"subjectId": subject_id}, {'name': 1, 'description': 1})
    topics = []
    for topic in topics_cursor:
        topic['_id'] = str(topic['_id'])
        topics.append(topic)
    return topics

def get_subtopics(topic_id):
    topic_object_id = ObjectId(topic_id)
    topic_document = db.Topics.find_one({"_id": topic_object_id}, {'subtopics': 1})
    subtopics = []
    if topic_document and 'subtopics' in topic_document:
        subtopics = topic_document['subtopics']
    
    return subtopics
