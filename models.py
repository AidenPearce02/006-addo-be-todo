import peewee as pw

db = pw.SqliteDatabase('database.db')


def initialize():
    Project.create_table(fail_silently=True)
    Task.create_table(fail_silently=True)


class BaseModel(pw.Model):
    class Meta:
        database = db


class Project(BaseModel):
    name = pw.CharField(max_length=100)
    color = pw.CharField(max_length=100)


class Task(BaseModel):
    name = pw.CharField(max_length=100)
    date = pw.DateField()
    priority = pw.IntegerField()
    project = pw.ForeignKeyField(Project)
    endTask = pw.BooleanField(default=False)
