from flask import Flask, request, jsonify
from parsing import translate as pars_translate
from prompting import translate as prompt_translate

app = Flask(__name__)

@app.route("/")
def index():
    return (
        "Try /hello/Chris for parameterized Flask route.\n"
        "Try /module for module import guidance"
    )

@app.route("/hello/<name>", methods=['GET'])
def hello(name: str):
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


if __name__ == "__main__":
    app.run()