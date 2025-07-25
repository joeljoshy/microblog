import sqlalchemy as sa
import sqlalchemy.orm as so

from app import app, db
from app.models import User, Post


@app.shell_context_processor
def make_shell_context():
    """Registers application objects in the shell context.

    This function is a shell context processor. When the Flask shell is
    started, it will invoke this function and register the items returned
    by it in the shell session. The function returns a dictionary of
    items that can be accessed in the shell session.

    The dictionary contains the following items:

    - `sa`: The SQLAlchemy module.
    - `so`: The SQLAlchemy ORM module.
    - `db`: The database instance.
    - `User`: The User model.
    - `Post`: The Post model.

    The items can be accessed from the shell session as follows:

         from yourapplication import db
         db.create_all()

    """
    return {'sa': sa, 'so': so, 'db': db, 'User': User, 'Post': Post}