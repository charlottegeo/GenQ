
from flask_socketio import SocketIO
from app import socketio
from app.utils.content_manager import load_info, get_subjects, get_topics, get_subtopics


@socketio.on('message')
def handle_message(data):
    print(f'message: {data}')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('formSubmitted')
def handle_form(data):
    load_info(data['subject'], data['topic'], data['subtopic'], data['concept'], data['num_questions'], data['result_type'])

@socketio.on('getSubjects')
def handle_get_subjects():
    print('Getting subjects')
    subjects = get_subjects()
    socketio.emit('subjects', subjects)

@socketio.on('getTopics')
def handle_get_topics(data):
    subject_id = data['subjectId']
    topics = get_topics(subject_id)
    socketio.emit('topics', topics)

@socketio.on('getSubtopics')
def handle_get_subtopics(data):
    topic_id = data['topicId']
    subtopics = get_subtopics(topic_id)
    socketio.emit('subtopics', subtopics)


