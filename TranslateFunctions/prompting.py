from playwright.sync_api import sync_playwright 
import json
import openai
import tiktoken
import uuid
import os

openai.api_key = os.environ["OPENAI_API_KEY"]
UNCHANGED_URLS = ["https://content-service-future.croatia.hr/api/company/params", "https://content-service-future.croatia.hr/api/entities/types", "https://content-service-future.croatia.hr/api/seo/currenturl", "https://content-service-future.croatia.hr/api/entities", "https://content-service-future.croatia.hr/api/entities/services", "https://content-service-future.croatia.hr/api/v1/Menu"]
RESONING_DELIMITER = "***"
INSTRUCTION_DELIMITER = "---"
URL_DELIMITER = ":::"
JSON_DELIMITER = "###"
SYSTEM_MESSAGE = f"""
As a translator, your goal is to translate specific sections of a JSON file from Croatian into a designated language. \
Your translations should be captivating and appealing to a carefully selected target audience. \
Consider the unique characteristics and preferences of this group to tailor the translations accordingly. \
Throughout the translation process, strive for exceptional quality and linguistic fluency. \
Pay attention to detail, grammar, and style, while maintaining a persuasive and appealing tone.\
Additionally, the translations should be relevant for a specific period of the year in Croatia. \
Take into account the seasonal context and events \
occurring during that time to make the translations more engaging and relatable to visitors in Croatia. \
Your output should be a JSON file in the same format as the input, but with certain values translated.

Follow these steps in translation, instructions are provided after {INSTRUCTION_DELIMITER}:

Step 1: User will provide instructions to inform you about the target language, the specific audience, and the relevant time period. \
Identify the language for translation, the intended audience, and the timeframe to understand the context.

Step 2: After {URL_DELIMITER} URL of endpoint will be provided. \
determine the category that the URL represents. Here are the possible categories:
1. languageexpressions
2. current event
3. static content
4. page
5. company params
6. menu
7. types
8. currenturl
9. breadcrumbs
10. entities
11. region
12. services
13. events

Step 3: Depending on the previous category, you need to translate or change the values \
of the following JSON keys in the provided JSON file if it contains them:
1. languageexpressions
    a. change IDLanguage to choosen translation language
    b. translate Value
2. current event
    a. DO NOT add keys and values if original JSON does not contain them 
    b. DO NOT translate any path that has cmsmedia in it
    c. DO NOT translate Title in Place
    d. in Data translate Title, Overtitle, Subtitle, ShortDescription, ListDescription
    e. in Data translate and change SefUrl to match translation language code, for example hr-hr into en-gb
    f. in Data translate and change Link
    g. in Media translate MediaAltText and MediaDescription
    h. Add language code at the end of ExternalLink
3. static content
    a. DO NOT add keys and values if original JSON does not contain them 
    b. DO NOT translate any path that has cmsmedia in it
    c. in Media translate MediaAltText and MediaDescription
4. page
    a. DO NOT add keys and values if original JSON does not contain them
    b. in Data translate Title and ShortDescription
    c. in Data translate and change SefUrl to match translation language code, for example hr-hr into en-gb
5. company params
    a.  No translation required, return the original JSON
6. menu
    a. DO NOT add keys and values if original JSON does not contain them 
    b. DO NOT translate any path that has cmsmedia in it
    c. in Items translate Name
    d. in Items translate and change SefUrl to match translation language code, for example hr-hr into en-gb
7. types
    a.  No translation required, return the original JSON
8. currenturl
    a.  No translation required, return the original JSON
9. breadcrumbs
    a. DO NOT add keys and values if original JSON does not contain them
    b. translate BreadcrumbText
    c. translate and change SefUrl to match translation language code, for example hr-hr into en-gb
10. entities
    a. No translation required, return the original JSON
11. region
    a. DO NOT add keys and values if original JSON does not contain them 
    b. in Data translate Title
    c. in Data translate and change SefUrl to match translation language code, for example hr-hr into en-gb
12. services
    a.  No translation required, return the original JSON
13. events
    a. DO NOT add keys and values if original JSON does not contain them 
    b. DO NOT translate any path that has cmsmedia in it
    c. DO NOT translate Title in Place
    d. in Data objects translate Title, Subtitle, ShortDescription
    e. in Data translate and change SefUrl to match translation language code, for example hr-hr into en-gb
    f. in Tag translate Title
    g. in Media translate MediaAltText and MediaDescription
    h. Add language code at the end of ExternalLink

Step 4: 
After {JSON_DELIMITER}, JSON file will be provided.\
Translate or change the values exclusively of specific keys from step 3 into the designated language, \
tailored for the target audience and timeframe specified in step 1. \
The category for translation is determined in step 2. \
Ensure that the output JSON file maintains the same format as the input an DO NOT add any new content to JSON file.

Output in the following format:
Step 1: <step 1 reasoning summary in 2 sentences maximal>
Step 2: <step 2 reasoning summary in 2 sentences maximal>
Step 3: <step 3 reasoning summary in 2 sentences maximal>
Response to user: {RESONING_DELIMITER} <translated JSON file>

Strictly follow every step and format, Response to user must be in same JSON format as user input \
DO NOT FORGET BRACKETS, especially closing brackets of Media!
"""

def translate(api_request):
    response_jsons = []
    response_urls = []
    trasnlated_page = []
    fragmented_json = None

    url = api_request["Url"]
    language = api_request["Language"]
    persona = api_request["Persona"]
    timeframe = api_request["Timeframe"]

    with sync_playwright() as p:
        def handle_response(response): 
            # the endpoint we are insterested in 
            if ("content-service-future.croatia.hr" in response.url):
                if any(url == response.url for url in UNCHANGED_URLS):
                    pass
                else:
                    #print(response.url)
                    #print(json.dumps(response.json()))
                    response_json = json.dumps(response.json())
                    token_count = num_tokens_from_string((response_json),"cl100k_base")
                    #print(response.url)
                    #print(token_count)
                    if token_count > 1000:
                        id = generate_id()
                        s = token_count // 950
                        if "Data" in response_json:
                            #print("object")
                            rj = json.loads(response_json)
                            rj["FragmentID"] = id
                            rj["FragmentType"] = "object"
                            data_list = rj["Data"]
                            data_list_len = len(data_list)
                            size = data_list_len // s 
                            sublists = split_list_equal(data_list, size)
                            for i in range(len(sublists)):
                                rj["FragmentPart"] = i
                                rj["Data"] = sublists[i]
                                response_json = json.dumps(rj)
                                response_urls.append(response.url)
                                response_jsons.append(response_json)
                        elif type(json.loads(response_json)) == list:
                            #print("lista")
                            rj = {
                                "FragmentID": id,
                                "FragmentType": "list"
                            }
                            data_list = json.loads(response_json)
                            data_list_len = len(data_list)
                            size = data_list_len // s
                            #print(size)
                            sublists = split_list_equal(data_list, size)
                            for i in range(len(sublists)):
                                rj["FragmentPart"] = i
                                rj["Data"] = sublists[i]
                                response_json = json.dumps(rj)
                                response_urls.append(response.url)
                                response_jsons.append(response_json)
                    else:
                        response_urls.append(response.url)
                        response_jsons.append(response_json)
            
        browser = p.chromium.launch() 
        page = browser.new_page() 
        page.on("response", handle_response) 
        page.goto(url, wait_until="networkidle") 
        page.context.close() 
        browser.close()

    for i in range(len(response_urls)):
        messages =  [  
        {'role':'system', 
        'content': SYSTEM_MESSAGE},    
        {'role':'user', 
        'content': user_message(response_urls[i], response_jsons[i], language, persona, timeframe)},  
        ]
        gpt_response = get_completion_from_messages(messages)
        #print("original json: ")
        #print(response_jsons[i])
        #print("-------")
        #print("GPT response: ")
        try:
            final_response = gpt_response.split(RESONING_DELIMITER)[-1].strip()
        except Exception as e:
            final_response = "ChatGPT response isn't following formating steps" 

        try:
            final_response = json.loads(final_response)
        except Exception as e:
            print("invalid json")
            print(e)
            #print(final_response)
            final_response = {
                "Error": "Broken fragment"
            }

        if "FragmentID" in final_response:
            #print("Fragment")
            if fragmented_json != None and final_response["FragmentID"] != fragmented_json["FragmentID"]:
                # vrati i resetiraj
                if fragmented_json["FragmentType"] == "object":
                    del fragmented_json["FragmentPart"]
                    del fragmented_json["FragmentID"]
                    del fragmented_json["FragmentType"]
                    trasnlated_page.append(fragmented_json)
                elif fragmented_json["FragmentType"] == "list":
                    trasnlated_page.append(fragmented_json["Data"])
                fragmented_json = None

            if final_response["FragmentPart"] == 0:
                fragmented_json = final_response
            else:
                fragmented_json["Data"] += final_response["Data"]
        else: 
            trasnlated_page.append(final_response)

    if fragmented_json != None:
        if fragmented_json["FragmentType"] == "object":
            del fragmented_json["FragmentPart"]
            del fragmented_json["FragmentID"]
            del fragmented_json["FragmentType"]
            trasnlated_page.append(fragmented_json)
        elif fragmented_json["FragmentType"] == "list":
            trasnlated_page.append(fragmented_json["Data"])

    #print(json.dumps(trasnlated_page))
    return trasnlated_page



def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=1500):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def generate_id():
    id = str(uuid.uuid4())
    return id

def split_list_equal(lst, size):
    return [lst[i:i+size] for i in range(0, len(lst), size)]

def user_message(response_url, response_json, language, persona, timeframe):
    messgae = f"""
    {INSTRUCTION_DELIMITER} \
    Translate the following JSON file into {language} in a way that is appeling to {persona} \
    visiting Croatia in {timeframe} \
    {URL_DELIMITER} \
    {response_url} \
    {JSON_DELIMITER} \
    {response_json}
    """
    return messgae

