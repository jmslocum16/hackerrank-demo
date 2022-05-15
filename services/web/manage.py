from flask.cli import FlaskGroup

from project import app


cli = FlaskGroup(app)

"""
@cli.command("create_db")
def create_db():
    print("creating db")
    db.drop_all()
    db.create_all()
    
    db.session.commit()
"""

if __name__ == "__main__":
    cli()
