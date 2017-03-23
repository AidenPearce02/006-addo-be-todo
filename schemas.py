from marshmallow import ValidationError
from marshmallow import fields, validate, validates
from marshmallow_peewee import ModelSchema
from be.models import Task, Project, User
from datetime import datetime
from marshmallow_peewee import Related


class UserSchema(ModelSchema):
    name = fields.Str(validate=[validate.Length(max=70)])
    password = fields.Str()

    class Meta:
        model = User


class ProjectSchema(ModelSchema):
    name = fields.Str(validate=[validate.Length(min=3, max=10)])
    color = fields.Str(validate=[validate.Length(min=3, max=10)])
    user = Related(nested=UserSchema)

    class Meta:
        model = Project

    @validates('user')
    def validate_user(self, value):
        if not User.filter(User.id == value).exists():
            raise ValidationError("Can't find user")


class TaskSchema(ModelSchema):
    name = fields.Str(validate=[validate.Length(min=3, max=10)])
    date = fields.Date(default=datetime.now())
    project = Related(nested=ProjectSchema)
    priority = fields.Int(default=0)
    endTask = fields.Bool(default=False)

    class Meta:
        model = Task

    @validates('project')
    def validate_project(self, value):
        if not Project.filter(Project.id == value).exists():
            raise ValidationError("Can't find project")


user_schema = UserSchema()
project_schema = ProjectSchema()
task_schema = TaskSchema()

