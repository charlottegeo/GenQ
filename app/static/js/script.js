
var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
var answers = [];
var score = 0;
var totalQuestions;
window.onload = function() {
    document.getElementById('quiz_form').style.display = "flex";
    document.getElementById('studyGuideText').innerHTML = "";
    document.getElementById('quizText').innerHTML = "";
    document.getElementById('subject').value = "";
    document.getElementById('topic').value = "";
    document.getElementById('topic').disabled = true;
    document.getElementById('subtopic').value = "";
    document.getElementById('subtopic').disabled = true;
    document.getElementById('concept').value = "";
    document.getElementById('numQuestions').value = "";
    document.getElementById('quizType').value = "quiz";
    document.getElementById("numQuestionsLbl").style.display = "block";
    document.getElementById('numQuestions').style.display = "block";
    document.getElementById('formQuestion').textContent = "What material do you want in your quiz?";
    document.getElementById('specificCheckbox').checked = false;
    socket.emit('getSubjects');

}

function submitForm() {
    var subject = document.getElementById('subject').value;
    var topic = document.getElementById('topic').value;
    var subtopic = document.getElementById('subtopic').value;
    var concept = document.getElementById('concept').value;
    var num_questions = document.getElementById('numQuestions').value;
    var result_type = document.getElementById('quizType').value;
    socket.emit('formSubmitted', {
        subject: subject,
        topic: topic,
        subtopic: subtopic,
        concept: concept,
        num_questions: num_questions,
        result_type: result_type
    });
    document.getElementById('quiz_form').style.display = "none";
}

function changeQuizType(){
    var quizType = document.getElementById('quizType').value;
    if(quizType == "quiz"){
        document.getElementById('numQuestions').style.display = "block";
        document.getElementById('numQuestionsLbl').style.display = "block";
        document.getElementById('formQuestion').textContent = "What material do you want in your quiz?";
    } else {
        document.getElementById('numQuestions').style.display = "none";
        document.getElementById('numQuestionsLbl').style.display = "none";  
        document.getElementById('formQuestion').textContent = "What material do you want in your study guide?";
    }
}

function toggleConcept(){
    var concept = document.getElementById('concept');
    var conceptLabel = document.getElementById('conceptLbl');
    //if concept is visible, hide it
    if(concept.style.display === "block"){
        concept.style.display = "none";
        conceptLabel.style.display = "none";
    } else {
        concept.style.display = "block";
        conceptLabel.style.display = "block";
    }
}

socket.on('subjects', function(subjects) {
    var subjectSelect = document.getElementById('subject');
    subjects.forEach(function(subject) {
        var option = new Option(subject.name + " - " + subject.description, subject._id);
        subjectSelect.add(option);
    });
});

socket.on('topics', function(topics) {
    var topicSelect = document.getElementById('topic');
    topicSelect.disabled = false;
    topics.forEach(function(topic) {
        var option = new Option(topic.name, topic._id);
        topicSelect.add(option);
    });
});

socket.on('subtopics', function(subtopics) {
    var subtopicSelect = document.getElementById('subtopic');
    subtopicSelect.disabled = false;
    subtopics.forEach(function(subtopic) {
        var option = new Option(subtopic, subtopic); // Assuming subtopics array contains strings
        subtopicSelect.add(option);
    });
});

function changeSubject() {
    var subjectSelect = document.getElementById('subject');
    var topicSelect = document.getElementById('topic');
    var subtopicSelect = document.getElementById('subtopic');
    topicSelect.innerHTML = '<option id="topPlaceholder" value="">Select a Topic</option>';
    topicSelect.disabled = true;
    subtopicSelect.innerHTML = '<option id="subPlaceholder" value="">Select a Subtopic</option>';
    subtopicSelect.disabled = true;

    if(subjectSelect.value) {
        socket.emit('getTopics', { subjectId: subjectSelect.value });
        var placeholder = document.getElementById('subjPlaceholder');
        placeholder.style.display = "none";
    }
}


function changeTopic() {
    var topicSelect = document.getElementById('topic');
    var subtopicSelect = document.getElementById('subtopic');
    subtopicSelect.innerHTML = '<option id="subPlaceholder" value="">Select a Subtopic</option>';
    subtopicSelect.disabled = true;
    if(topicSelect.value) {
        socket.emit('getSubtopics', { topicId: topicSelect.value });
        var placeholder = document.getElementById('topPlaceholder');
        placeholder.style.display = "none";
    }
}


function changeSubtopic(){
    var placeholder = document.getElementById('subPlaceholder');
    placeholder.style.display = "none";
}

socket.on('studyGuideGenerated', function(data) {
    var studyGuideText = document.getElementById('studyGuideText');
    let formattedText = data.text.replace(/\n/g, '<br>');
    formattedText = formattedText.replace(/\*(.*?)\*/g, '<b>$1</b>');
    
    studyGuideText.innerHTML = formattedText;
});

socket.on('quizGenerated', function(data) {
    var quizText = document.getElementById('quizText');
    var questions = data.quiz[0]; // Assuming this structure from your existing code
    answers = data.quiz[1]; // Assuming this is where correct answers are stored
    var questionText = "";
    questionText += "<p id='score'>Correct answers: 0/0</p>";
    for (var i = 0; i < questions.length; i++) {
        questionText += "<div class='question' id='question" + questions[i].number + "'>";
        questionText += "<h3>Question " + questions[i].number + "</h3>";
        questionText += "<p>" + questions[i].text + "</p>";

        for (var j = 0; j < questions[i].options.length; j++) {
            questionText += "<input type='radio' name='question" + questions[i].number + "' value='" + questions[i].options[j][0] + "'>";
            questionText += "<label>" + questions[i].options[j][1] + "</label><br>";
        }

        // Add a Submit button for each question, initially hidden
        questionText += "<button id='submitAnswer" + questions[i].number +"' style='display:none;' onclick='submitAnswer(" + questions[i].number + ")'>Submit</button>";
        questionText += "</div>";
    }

    quizText.innerHTML = questionText;

    // Add event listener to show the Submit button when a radio button is selected
    var radios = quizText.getElementsByTagName('input');
    for (var i = 0; i < radios.length; i++) {
        radios[i].addEventListener('change', function() 
        {
            document.getElementById('submitAnswer' + this.name.slice(-1)).style.display = 'block'; // Show the Submit button
        });
    }
    totalQuestions = Object.keys(answers).length;
    document.getElementById('score').textContent = "Correct answers: " + score + "/" + totalQuestions;
});

function submitAnswer(questionNumber) {
    var selectedOption = document.querySelector('input[name="question' + questionNumber + '"]:checked').value;
    var correctAnswer = answers[questionNumber];
    var submitButton = document.getElementById('submitAnswer' + questionNumber);
    
    var isCorrect = selectedOption === correctAnswer;
    updateScore(isCorrect); // Update the score
    
    if (isCorrect) {
        submitButton.textContent = "✓";
        submitButton.style.backgroundColor = "green";
    } else {
        submitButton.textContent = "✗";
        submitButton.style.backgroundColor = "red";
    }

    submitButton.disabled = true;
    var options = document.querySelectorAll('input[name="question' + questionNumber + '"]');
    for (var i = 0; i < options.length; i++) {
        options[i].disabled = true;
    }
}

function updateScore(isCorrect) {
    if (isCorrect) {
        score++;
    }
    var totalQuestions = Object.keys(answers).length;
    console.log(answers);
    console.log(totalQuestions);
    document.getElementById('score').textContent = "Correct answers: " + score + "/" + totalQuestions;
}