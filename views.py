import pprint
from datetime import datetime, timedelta

from flask import Flask, jsonify
from flask import g, request
from flask_cors import CORS, cross_origin
from flask_jwt import JWT, jwt_required, current_identity
from flask_login import LoginManager, logout_user
from werkzeug.security import safe_str_cmp

from be.models import initialize, User, Tasks, Projects
from be.schemas import user_schema, project_schema, task_schema

app = Flask(__name__)
app.secret_key = "super key"
app.config['JWT_AUTH_URL_RULE'] = '/login'

cors = CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
login_manager = LoginManager(app)
login_manager.login_view = 'login'


def authenticate(username, password):
    user = User.filter(User.username == username).first()
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user
    return None


def identity(payload):
    user_id = payload['identity']
    return User.get(id=user_id)


jwt = JWT(app, authenticate, identity)


@app.before_request
def before_request():
    g.user = current_identity


@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = 'http://localhost:5000'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response


@login_manager.user_loader
def load_user(id):
    return User.get(id=int(id))


@app.route("/logout")
@cross_origin()
@jwt_required()
def logout():
    logout_user()
    return jsonify({'message': 'Is logout! Bye!!!'}), 200


@app.route("/registration", methods=["POST"])
@cross_origin()
def new_user():
    json_data = request.json
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    data, errors = user_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    name, password = data.username, data.password
    user = User.select().filter(username=name).first()
    if user is None:
        User.create(username=name, password=password)
        return jsonify({"message": "Created new user: {}".format(name)})
    return jsonify({"message": "Can't Created user: {} is alredy exist".format(name)})


# projects

@app.route("/project", methods=["POST"])
@cross_origin()
@jwt_required()
def new_project():
    json_data = request.json
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    data, errors = project_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    name, color, user = data.name, data.color, data.to_user
    Projects.create(name=name, color=color, to_user=user)
    return jsonify({"message": "Created new project: {}".format(name)})


@app.route("/projects", methods=["GET"])
@cross_origin()
@jwt_required()
def get_projects():
    return jsonify(project_schema.dump(Projects.select().join(User).where(Projects.to_user == g.user.get_id()),
                                       many=True).data), 200


@app.route("/project/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_project(id):
    try:
        project = Projects.select().where(Projects.id == id).filter(Projects.to_user == g.user.get_id())
        return jsonify(project_schema.dump(project, many=True).data), 200
    except Projects.DoesNotExist:
        return jsonify({'message': 'Can not find project'}), 404


@app.route("/project/<int:id>", methods=["PUT"])
@cross_origin()
@jwt_required()
def update_project(id):
    try:
        project = Projects.select().where(Projects.id == id).filter(Projects.to_user == g.user.get_id())
    except Projects.DoesNotExist:
        return jsonify({'message': 'Can not find project'}), 404

    newProject, errors = project_schema.load(request.json, instance=project)

    if errors:
        return jsonify(errors), 400

    newProject.save()

    return jsonify(project_schema.dump(newProject).data), 200


@app.route("/project/<int:id>", methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_project(id):
    is_exist = Projects.select().where(Projects.id == id).filter(Projects.to_user == g.user.get_id()).exists()
    if not is_exist:
        return jsonify({'message': "Can't find project"}), 404

    Projects.delete().where(Projects.id == id).execute()
    return jsonify({})


# users

@app.route("/user", methods=["GET"])
@cross_origin()
@jwt_required()
def get_users():
    return jsonify(user_schema.dump(User.select()).data), 200


@app.route("/user/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_user(id):
    try:
        user = User.get(id=id)
        return jsonify(user_schema.dump(User.select().where(User.id == id)).data), 200
    except User.DoesNotExist:
        return jsonify({'message': 'Can not find user'}), 404


@app.route('/user/<int:id>', methods=["PUT"])
@cross_origin()
@jwt_required()
def update_user(id):
    try:
        user = User.get(id=id)
    except User.DoesNotExist:
        return jsonify({'message': 'Can not find user'}), 404

    newUser, errors = user_schema.load(request.json, instance=user)

    if errors:
        return jsonify(errors), 400

    newUser.save()

    return jsonify(user_schema.dump(newUser).data), 200


@app.route('/user/<int:id>', methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_user(id):
    is__exists = User.select().filter(id=id).exists()

    if not is__exists:
        return jsonify({"message": "Can't find user with id - `{id}`".format(id=id)}), 404

    User.delete().where(User.id == id).execute()
    return jsonify({}), 204


# tasks

@app.route("/task", methods=["POST"])
@cross_origin()
@jwt_required()
def set_task():
    json_data = request.json
    if not json_data:
        return jsonify({'message': 'No input data provided'}), 400
    data, errors = task_schema.load(json_data)
    if errors:
        return jsonify(errors), 422
    name, text, date, status, priority, to_project_id, to_user_id = data.name, data.text, data.date, data.status, data.priority, data.to_project, data.to_user
    Tasks.create(name=name, text=text, date=date, status=status, priority=priority, to_project=to_project_id,
                 to_user=to_user_id)
    return jsonify({"message": "Created new task: {}".format(name)})


@app.route("/tasks", methods=["GET"])
@cross_origin()
@jwt_required()
def get_tasks():
    params = request.args
    try:
        page = int(params.get('page'))
    except TypeError:
        return jsonify({"message": "Not int"}), 404
    if page <= 0:
        return jsonify({"message": "Too small a number"}), 404
    return jsonify(task_schema.dump(Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id(),
                                                                                       Tasks.status == False).order_by(
        +Tasks.priority, Tasks.date)[(page - 1) * 10: page * 10], many=True).data), 200


@app.route("/task/<int:id>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_task(id):
    try:
        task = Tasks.select().where(Tasks.id == id).filter(Tasks.to_user == g.user.get_id())
        return jsonify(task_schema.dump(task, many=True).data), 200
    except Tasks.DoesNotExist:
        return jsonify({'message': 'Can not find task'}), 404


@app.route("/tasks/next/<int:days>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_next_tasks(days):
    params = request.args
    try:
        page = int(params.get('page'))
    except TypeError:
        return jsonify({"message": "Not int"}), 404
    if page <= 0:
        return jsonify({"message": "Too small a number"}), 404
    today = datetime.today().strftime("%Y-%m-%d")
    nextDays = (datetime.today() + timedelta(days=days)).strftime("%Y-%m-%d")
    task = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id(),
                                                              Tasks.status == False).order_by(
        'id')[(page - 1) * 10: page * 10]
    task_next = task.filter(Tasks.date >= today, Tasks.date < nextDays)
    return jsonify(task_schema.dump(task_next, many=True).data), 200


@app.route("/tasks/archive>", methods=["GET"])
@cross_origin()
@jwt_required()
def get_archive_tasks():
    params = request.args
    try:
        page = int(params.get('page'))
    except TypeError:
        return jsonify({"message": "Not int"}), 404
    if page <= 0:
        return jsonify({"message": "Too small a number"}), 404
    task = Tasks.select(Tasks, Projects).join(Projects).where(Tasks.to_user == g.user.get_id()).where(
        Tasks.status == True).order_by(
        +Tasks.priority, Tasks.date)[(page - 1) * 10: page * 10]
    return jsonify(task_schema.dump(task, many=True).data), 200


@app.route('/task/<int:id>', methods=["PUT"])
@cross_origin()
@jwt_required()
def update_task(id):
    try:
        task = Tasks.select().where(Tasks.id == id).filter(Tasks.to_user == g.user.get_id())

    except Tasks.DoesNotExist:
        return jsonify({"message": "Can't find task with id - `{id}`".format(id=id)}), 404

    newTask, errors = task_schema.load(request.json, instance=task)

    if errors:
        return jsonify(errors), 400

    newTask.save()

    return jsonify(project_schema.dump(newTask).data), 200


@app.route('/task/<int:id>', methods=["DELETE"])
@cross_origin()
@jwt_required()
def delete_task(id):
    is__exists = Tasks.select().where(Tasks.id == id).filter(Tasks.to_user == g.user.get_id()).exists()

    if not is__exists:
        return jsonify({"message": "Can't find task with id - `{id}`".format(id=id)}), 404

    Tasks.delete().where(Tasks.id == id).execute()
    return jsonify({}), 204


if __name__ == "__main__":
    initialize()
    app.run(use_reloader=True)
