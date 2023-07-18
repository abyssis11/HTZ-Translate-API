
import logging
import azure.functions as func
from flask import Flask, request, jsonify
#from FlaskApp import app

app = Flask(__name__)

# azure functions code
def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """Each request is redirected to the WSGI handler.
    """
    return func.WsgiMiddleware(app.wsgi_app).handle(req, context)

# flask code
@app.route("/")
def index():
    return (
        "Try /hello/Chris for parameterized Flask route.\n"
        "Try /module for module import guidance"
    )

@app.route("/hello/<name>", methods=['GET'])
def hello(name: str):
    logging.info("Python HTTP trigger function processed a request")
    return f"hello {name}"