var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

socket.on('connect', function() {
    console.log('Connected');
});

socket.on('message', function(data) {
    console.log('Message received: ' + data);
});

function submitForm() {
    var subject = document.getElementById('subject').value;
    var topic = document.getElementById('topic').value;
    var subtopic = document.getElementById('subtopic').value;
    var concept = document.getElementById('concept').value;
    var num_questions = document.getElementById('numQuestions').value;
    var grade_level = document.getElementById('gradeLevel').value;
    var result_type = document.getElementById('quizType').value;
    socket.emit('formSubmitted', {
        subject: subject,
        topic: topic,
        subtopic: subtopic,
        concept: concept,
        num_questions: num_questions,
        grade_level: grade_level,
        result_type: result_type
    });
}

function changeQuizType(){
    var quizType = document.getElementById('quizType').value;
    if(quizType == "quiz"){
        document.getElementById('numQuestions').disabled = false;
        document.getElementById('formQuestion').textContent = "What material do you want in your quiz?";
    } else {
        document.getElementById('numQuestions').disabled = true;
        document.getElementById('formQuestion').textContent = "What material do you want in your study guide?";
    }
}

function toggleConcept(){
    var concept = document.getElementById('concept');
    //if concept is visible, hide it
    if(concept.style.display === "block"){
        concept.style.display = "none";
    } else {
        concept.style.display = "block";
    }
}