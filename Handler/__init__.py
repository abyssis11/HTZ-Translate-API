
import logging
import azure.functions as func
from flask import Flask, request, jsonify
from ..TranslateFunctions.parsing import translate as pars_translate
from ..TranslateFunctions.prompting import translate as prompt_translate
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

@app.route("/prompting-translate", methods = ["POST"])
def get_request_data_prompting():
    request_data = request.get_json()
    response = prompt_translate(request_data)

    return jsonify(response), 200

@app.route("/parsing-translate", methods = ["POST"])
def get_request_data_parsing():
    request_data = request.get_json()
    
    edit_api_request = request_data["EditAPI"]
    traslate_api_request = request_data["TranslateAPI"]
    response = pars_translate(edit_api_request, traslate_api_request)

    return jsonify(response), 200
 