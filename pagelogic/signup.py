
#sign up account for doctor, 
from flask import jsonify
from repository.user_repo import user_repo


def doctorSignUp(username, email):
    if username == '' or email == '':
        return jsonify({
            "error": "invalid input"
        }, 400) #bad practice, 应该只返回一个error message和空的user，之后会改
    
    role = "doctor"
    user = user_repo.UserRepository.create_user(username, email, role)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }), 201 #bad practice, 应该返回user，而不是直接返回response body，之后会改