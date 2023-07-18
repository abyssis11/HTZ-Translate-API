import json
import openai
import requests
import os

openai.api_key = os.environ["OPENAI_API_KEY"]
# defining the api-endpoint
# API_ENDPOINT_EVENTS = "https://content-service-future.croatia.hr/api/v1/Event"
#API_ENDPOINT_GET_TYPE = "https://content-service-future.croatia.hr/api/entities/typeid"
API_ENDPOINT_ALL_BY_TYPE = "https://content-service-future.croatia.hr/api/entities/simple"
# API_ENDPOINT_TYPES = "https://content-service-future.croatia.hr/api/entities/types"


# your API key here
API_KEY = "7pHY6cOBaWxp4weEg5NU0VQVd+viGZXic8aWRMQPqkso7DBD8sZ3SlXZk5uE0/419QtCNeGOhnxQm0ocTzWwHQ=="

""" data_events = {
    "Fields": [
        "SefUrl",
        "ShortDescription",
        "Title",
        "Subtitle",
    ],
    "RelatedFields": {"Place": "Place.Title,Place.ExternalLink", "Tag": "Tag.Title"},
    "MediaTypes": ["unassigned"],
    "FilterByActivePeriods": True,
    "Sort": [{"Field": "StartDate"}],
    "Settings": API_KEY,
    "LanguageID": "hr",
    "Paging": {"Limit": -1, "Offset": 0},
}
data_get_entity_type = {
    "Settings": API_KEY,
    "EntityID": 1157655
} """
data_by_type = {
    "Settings": API_KEY,
    "LanguageID": "hr",
    "EntityTypeID": 1066,
    "IncludeExtendedProperties": True
}
""" data_entities_type = {
    "Settings": API_KEY,
}
 """
DELIMITER = "###"
SYSTEM_MESSAGE = f"""
As a translator, your goal is to translate specific sections of a JSON file from Croatian into a designated language. \
Your translations should be captivating and appealing to a carefully selected target audience. \
Consider the unique characteristics and preferences of this group to tailor the translations accordingly. \
Throughout the translation process, strive for exceptional quality and linguistic fluency. \
Pay attention to detail, grammar, and style, while maintaining a persuasive and appealing tone.\
Additionally, the translations should be relevant for a specific period of the year in Croatia. \
Take into account the seasonal context and events \
occurring during that time to make the translations more engaging and relatable to visitors in Croatia. \
Your output should be a JSON file in the same format as the input, but with translated values.
JSON file to translate will be provided after {DELIMITER}.
"""


def translate(edit_api_request, traslate_api_request):
    # sending post request and saving response as response object
    response = requests.post(url=API_ENDPOINT_ALL_BY_TYPE, data=edit_api_request)
    events = response.json()

    #f = open("demofile2.txt", "w")
    #f.write(response.text)
    #f.close()

    language = traslate_api_request["Language"]
    persona = traslate_api_request["Persona"]
    timeframe = traslate_api_request["Timeframe"]
    n_events = traslate_api_request["NumberOfEvents"]
    i = 0

    for event in events:
        i+=1
        if i > n_events:
            break
        image_to_translate = get_images(event)
        data_to_translate = {
            "Caption": event["Caption"],
            "ListDescription": event["ListDescription"],
            "Overtitle": event["Overtitle"],
            "SefUrl": event["SefUrl"],
            "ShortDescription": event["ShortDescription"],
            "Subtitle": event["Subtitle"],
            "Title": event["Title"],
            "SeoBreadcrumbText": event["SEO"]["BreadcrumbText"],
            "SeoMetaDescription": event["SEO"]["MetaDescription"],
            "SeoMetaKeywords": event["SEO"]["MetaKeywords"],
            "SeoPageTitle": event["SEO"]["PageTitle"],
        }
        #print(image_to_translate)
        event_to_translate = merge(data_to_translate, image_to_translate)
        #print(event_to_translate)
        messages =  [  
        {'role':'system', 
        'content': SYSTEM_MESSAGE},    
        {'role':'user', 
        'content': user_message(event_to_translate, language, persona, timeframe)},  
        ]
        gpt_response = get_completion_from_messages(messages)
        gpt_response_json = json.loads(gpt_response)
        translated_event(event, gpt_response_json)
        #print(event)
    
    #f = open("demofile2.txt", "w")
    #f.write(json.dumps(events))
    #f.close()
        
    return events

def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0, max_tokens=1500):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def user_message(text, language, persona, timeframe):
    messgae = f"""
    Translate the following text into {language} in a way that is appeling to {persona} \
    visiting Croatia in {timeframe} \
    {DELIMITER} \
    {text}
    """
    return messgae

def set_images(event, gpt_json):
    images = event["MediaGallery"][0]["Images"]
    for i in range(len(images)):
        event["MediaGallery"][0]["Images"][i]["MediaAltText"] = gpt_json["image"+str(i)+"AltText"]
        event["MediaGallery"][0]["Images"][i]["MediaDescription"] = gpt_json["image"+str(i)+"Description"]
    
def get_images(event):
    image_to_translate = {}
    images = event["MediaGallery"][0]["Images"]
    for i in range(len(images)):
        image = images[i]
        image_to_translate["image"+str(i)+"AltText"] = image["MediaAltText"]
        image_to_translate["image"+str(i)+"Description"] = image["MediaDescription"]
    
    return image_to_translate

def merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def translated_event(event, gpt_json):
    event["Caption"] = gpt_json["Caption"]
    event["ListDescription"] = gpt_json["ListDescription"]
    event["Overtitle"] = gpt_json["Overtitle"]
    event["SefUrl"] = gpt_json["SefUrl"]
    event["ShortDescription"] = gpt_json["ShortDescription"]
    event["Subtitle"] = gpt_json["Subtitle"]
    event["SEO"]["BreadcrumbText"] = gpt_json["SeoBreadcrumbText"]
    event["SEO"]["SefUrl"] = gpt_json["SefUrl"]
    event["SEO"]["MetaDescription"] = gpt_json["SeoMetaDescription"]
    event["SEO"]["MetaKeywords"] = gpt_json["SeoMetaKeywords"] 
    event["SEO"]["PageTitle"] = gpt_json["SeoPageTitle"]

    set_images(event, gpt_json)
