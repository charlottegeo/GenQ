import google.generativeai as genai
import dotenv
import os
import re
from transformers import pipeline
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))
dotenv.load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

qa_pipeline = pipeline("question-answering")

#Instructions for the AI to format the content such that it can be parsed consistently
quiz_format_instructions = """
Generate each question as a separate paragraph.
Start each question, both multiple-choice and free-response, with a number followed by a period (e.g., "1. What is...").
List the multiple-choice options below the question, each on a new line and labeled with a letter (e.g., "a. Option 1").
For free-response questions, simply state the question without any options.
After all the questions, provide an answer key. Start the answer key with the text "ANSWER KEY" on a new line.
List the answers in the same order as the questions, each on a new line. Start each answer with the question number, a period, and a space (e.g., "1. Answer to question 1").
For multiple-choice questions, provide the letter of the correct answer (e.g., "1. a"). Do not include the question number in the answer for multiple-choice questions (e.g., "a" instead of "1. a". Also do not include the answer text for multiple-choice questions (e.g., "a" instead of "1. a. Option 1)
"""

guide_format_instructions = """
When writing key terms, make sure to define them.
When writing bullet points, use a dash followed by a space (e.g., "- This is a bullet point").
When writing paragraphs, separate them with two new lines.
"""

def load_info(subj, top, subtop, conc, num, grade, result_type):
    global grade_level
    global subject
    global topic
    global subtopic
    global concept
    global num_questions
    global resultType
    grade_level = grade
    subject = subj
    topic = top
    subtopic = subtop
    concept = conc
    num_questions = num
    resultType = result_type
    print(f"Grade: {grade_level}, Subject: {subject}, Topic: {topic}, Subtopic: {subtopic}, Concept: {concept}, Number of Questions: {num_questions}, Result Type: {resultType}")
    match resultType:
        case "quiz":
            make_quiz(num_questions)
        case "study guide":
            make_study_guide()


def make_quiz(num_questions):
    num_questions = int(num_questions)
    num_mcqs = num_questions * 6 // 10  # 60% of the questions
    num_frqs = num_questions - num_mcqs  # the rest of the questions

    mcqs = multiple_choice_question(num_mcqs)
    frqs = short_answer_question(num_frqs)

    quiz = mcqs + "\n\n" + frqs
    parsed_quiz = parse_quiz(quiz)
    for question in parsed_quiz[0]:
        print(question)
    for answer in parsed_quiz[1]:
        print(answer or "No answer found")
    return quiz
def make_study_guide():
    if concept:
        response = model.generate_content(f"Write a study guide on {concept} in {subtopic} in {topic} in {subject} for {grade_level} grade students." + guide_format_instructions)
    else:
        response = model.generate_content(f"Write a study guide on {subtopic} in {topic} in {subject} for {grade_level} grade students." + guide_format_instructions)
    if response:
        generated_text = response.text
        generated_text = generated_text.replace("*", "")
        print(generated_text)
    else:
        print("No content was generated.")

def short_answer_question(num_frqs):
    if concept:
        response = model.generate_content(f"Write {num_frqs} short-answer questions on {concept} in {subtopic} in {topic} for {grade_level} grade students." + quiz_format_instructions)
    else:
        response = model.generate_content(f"Write {num_frqs} short-answer questions on {subtopic} in {topic} in {subject} for {grade_level} grade students."  + quiz_format_instructions)
    if response:
        generated_text = response.text
        generated_text = generated_text.replace("*", "")
        return generated_text
    else:
        return None

def multiple_choice_question(num_mcqs):
    if concept:
        response = model.generate_content(f"Write {num_mcqs} multiple choice questions on {concept} in {topic} for {grade_level} grade students." + quiz_format_instructions)
    else:
        response = model.generate_content(f"Write {num_mcqs} multiple choice questions on {topic} in {subject} for {grade_level} grade students." + quiz_format_instructions)
    if response:
        generated_text = response.text

        generated_text = generated_text.replace("*", "")
        mcqs = []
        for i in range(num_mcqs):
            mcq = generated_text.split("\n\n")[i]
            mcqs.append(mcq)
        return generated_text
    else:
        return None

import re

def parse_quiz(quiz_text):
    if "ANSWER KEY" not in quiz_text:
        print("No answer key found in quiz text.")
        return [], []

    sections = quiz_text.split("\n\nANSWER KEY\n\n")
    questions_section = sections[0]
    answers_section = sections[1] if len(sections) > 1 else ""

    question_blocks = questions_section.split("\n\n")
    answer_blocks = answers_section.split("\n\n") if answers_section else []

    questions = []
    for block in question_blocks:
        lines = block.split("\n")
        question_text = lines[0]
        if len(lines) > 1:
            # This is a multiple choice question
            options = lines[1:]
            question_type = "MCQ"
        else:
            # This is a free response question
            options = []
            question_type = "FRQ"
        questions.append({
            "type": question_type,
            "question": question_text,
            "options": options
        })

    answers = []
    for block in answer_blocks:
        lines = block.split("\n")
        for line in lines:
            match = re.match(r"(\d+)\. (.+)", line)
            if match:
                question_number = int(match.group(1))
                answer_text = match.group(2)
                answers.append({
                    "question_number": question_number,
                    "answer": answer_text
                })

    return questions, answers

def grade_frq_responses(user_answer, question, correct_answer):
    result = qa_pipeline({
        "context" : correct_answer,
        "question" : question,
        "answers" : user_answer
    })
    correct_answer = result['answer']
    if correct_answer == user_answer:
        return True
    else:
        return False
