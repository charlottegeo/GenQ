from flask_socketio import SocketIO
from app import socketio
from app.utils.content_manager import load_info
@socketio.on('message')
def handle_message(data):
    print(f'message: {data}')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('formSubmitted')
def handle_form(data):
    load_info(data['subject'], data['topic'], data['concept'], data['num_questions'], data['grade_level'], data['result_type'])
