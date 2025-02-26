from flask.cli import FlaskGroup

import os
from project import app

cli = FlaskGroup(app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=os.environ['BACKEND_PORT'])

