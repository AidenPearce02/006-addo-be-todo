from flask import Flask, request, jsonify
from be.models import Task, Project, initialize
from be.schemas import project_schema, task_schema
from datetime import datetime

from flask_cors import CORS

app = Flask(__name__)
CORS(app=app)
today = datetime.today().strftime("%Y-%m-%d")
day7 = datetime(datetime.today().year, datetime.today().month, datetime.today().day + 6).strftime("%Y-%m-%d")


@app.route('/api/projects', methods=["POST"])
def create_project():
    project, errors = project_schema.load(request.json)

    if errors:
        return jsonify(errors), 400

    project.save()

    return jsonify(project_schema.dump(project).data), 201


@app.route('/api/projects/<int:id>', methods=["PUT"])
def update_project(id):
    try:
        project = Project.get(id=id)
    except Task.DoesNotExist:
        return jsonify({"message": "Can't find project with id - `{id}`".format(id=id)}), 404

    project, errors = project_schema.load(request.json, instance=project)

    if errors:
        return jsonify(errors), 400

    project.save()

    return jsonify(project_schema.dumps(project).data), 200


@app.route('/api/projects/<int:id>', methods=["DELETE"])
def delete_project(id):
    is_project_exists = Project.select().filter(id=id).exists()

    if not is_project_exists:
        return jsonify({"message": "Can't find project with id - `{id}`".format(id=id)}), 404

    is_empty = Task.select().filter(project=id).first()
    if is_empty:
        return jsonify({"message": "Project `{id}` is not empty".format(id=id)}), 404

    Project.delete().where(Project.id == id).execute()
    return jsonify({}), 204


@app.route('/api/projects', methods=["GET"])
def get_projects():
    projects = list(Project.select())
    if not projects:
        return jsonify({"message": "List with projects is empty"})
    return jsonify(project_schema.dump(projects, many=True).data)


@app.route('/api/projects/<int:id>', methods=["GET"])
def get_one_project(id):
    try:
        project = Project.get(id=id)
        tasks = list(Task.select().filter(project=project.get_id()).filter(endTask=False))
        if not tasks:
            return jsonify({"message": "Project with id - `{id}` is empty".format(id=id)})
        return jsonify(task_schema.dump(tasks, many=True).data)
    except Project.DoesNotExist:
        return jsonify({"message": "Can't find project with id - `{id}`".format(id=id)}), 404


@app.route('/api/tasks', methods=["POST"])
def create_task():
    task, errors = task_schema.load(request.json)

    if errors:
        return jsonify(errors), 400

    task.save()

    return jsonify(task_schema.dump(task).data), 201


@app.route('/api/tasks', methods=["GET"])
def get_tasks():
    tasks = list(Task.select().filter(endTask=False))
    if not tasks:
        return jsonify({"message": "List with tasks is empty"})
    return jsonify(task_schema.dump(tasks, many=True).data), 200


@app.route('/api/tasks/today', methods=["GET"])
def get_tasks_today():
    tasks = list(Task.select().filter(endTask=False).filter(date=today))
    if not tasks:
        return jsonify({"message": "List with tasks is empty"})
    return jsonify(task_schema.dump(tasks, many=True).data), 200


@app.route('/api/tasks/days7', methods=["GET"])
def get_tasks_days7():
    tasks = list(Task.select().filter(endTask=False))
    if not tasks:
        return jsonify({"message": "List with tasks is empty"})
    return jsonify(task_schema.dump(tasks, many=True).data), 200


@app.route('/api/tasks/end', methods=["GET"])
def get_tasks_end():
    tasks = list(Task.select().filter(endTask=True))
    if not tasks:
        return jsonify({"message": "List with tasks is empty"})
    return jsonify(task_schema.dump(tasks, many=True).data)


@app.route('/api/tasks/<int:id>', methods=["PUT"])
def update_task(id):
    try:
        task = Task.get(id=id)
    except Task.DoesNotExist:
        return jsonify({"message": "Can't find task with id - `{id}`".format(id=id)}), 404

    task, errors = task_schema.load(request.json, instance=task)

    if errors:
        return jsonify(errors), 400

    task.save()

    return jsonify(task_schema.dumps(task).data), 200


@app.route('/api/tasks/<int:id>', methods=["DELETE"])
def delete_task(id):
    is_task_exists = Task.select().filter(id=id).exists()

    if not is_task_exists:
        return jsonify({"message": "Can't find task with id - `{id}`".format(id=id)}), 404

    Task.delete().where(Task.id == id).execute()
    return jsonify({}), 204


if __name__ == '__main__':
    initialize()
    app.run(use_reloader=True)
