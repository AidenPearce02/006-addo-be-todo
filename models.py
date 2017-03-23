import peewee as pw

db = pw.SqliteDatabase('database.db')


def initialize():
    Project.create_table(fail_silently=True)
    Task.create_table(fail_silently=True)
    User.create_table(fail_silently=True)
    try:
        User.create(
            username='root',
            password='123'
        )
    except pw.IntegrityError:
        pass


class BaseModel(pw.Model):
    class Meta:
        database = db


class User(BaseModel):
    username = pw.CharField(max_length=70, unique=True)
    password = pw.CharField(max_length=70)

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.state

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)


class Project(BaseModel):
    name = pw.CharField(max_length=100)
    color = pw.CharField(max_length=100)
    user = pw.ForeignKeyField(User)


class Task(BaseModel):
    name = pw.CharField(max_length=100)
    date = pw.DateField()
    priority = pw.IntegerField()
    project = pw.ForeignKeyField(Project)
    endTask = pw.BooleanField(default=False)


