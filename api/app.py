from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def welcome():
    return render_template("index.html")


@app.route("/query")
def submit():
    return render_template("query.html")
