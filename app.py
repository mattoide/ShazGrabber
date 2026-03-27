import os
from flask import Flask, render_template
from flask_cors import CORS
import config

from api.routes_upload   import bp as upload_bp
from api.routes_folder   import bp as folder_bp
from api.routes_match    import bp as match_bp
from api.routes_download import bp as download_bp

app = Flask(__name__)
app.config["UPLOAD_FOLDER"]    = config.UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_MB * 1024 * 1024

CORS(app)

app.register_blueprint(upload_bp)
app.register_blueprint(folder_bp)
app.register_blueprint(match_bp)
app.register_blueprint(download_bp)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    os.makedirs(config.UPLOAD_FOLDER,   exist_ok=True)
    os.makedirs(config.DOWNLOAD_FOLDER, exist_ok=True)
    print("ShazGrabber avviato -> http://localhost:5000")
    app.run(debug=False, threaded=True, port=5000)
