from __future__ import print_function

from botocore.vendored import requests
import urllib

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Magic the Gathering price checker. " \
                    "Get a card price by saying, " \
                    "what is the price of counterspell."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please get a card price by saying, " \
                    "what is the price of lightning bolt."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Bye"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def generate_generic_failed_search(cardname):
    return "I was unable to find information about the card " +\
           cardname + ". Please try again."

def get_card_price(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True
    
    fuzzy_search_url = 'https://api.scryfall.com/cards/named?fuzzy='
    
    if 'CardName' in intent['slots']:
        mtg_card_name = intent['slots']['CardName']['value']
        url = fuzzy_search_url + urllib.quote(mtg_card_name)
        print("fetching url=" + url)
        
        resp = requests.get(url)
        data = resp.json()
        if 'object' in data:
            if data['object'] == 'card':
                if 'name' in data and 'usd' in data:
                    formatted_price = '${:,.2f}'.format(float(data['usd']))
                    speech_output = "The current price for " + data['name'] + \
                                    " is " + formatted_price + "."
                    reprompt_text = generate_generic_failed_search(mtg_card_name)
                else:
                    speech_output = generate_generic_failed_search(mtg_card_name)
                    reprompt_text = generate_generic_failed_search(mtg_card_name)
            elif data['object'] == 'error' and data['code'] == 'not_found':
                if 'type' in data and data['type'] == 'ambiguous':
                    speech_output = "The card name " + mtg_card_name + " matches too many cards. " \
                                    "Please try again."
                    reprompt_text = "The card name " + mtg_card_name + " matches too many cards. " \
                                    "Please try again."
                else:
                    speech_output = generate_generic_failed_search(mtg_card_name)
                    reprompt_text = generate_generic_failed_search(mtg_card_name)
        else:
            speech_output = generate_generic_failed_search(mtg_card_name)
            reprompt_text = generate_generic_failed_search(mtg_card_name)
    else:
        speech_output = "I'm not sure what that card is. Please try again."
        reprompt_text = "I'm not sure what that card is. Please try again."
    
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "GetCardPrice":
        return get_card_price(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])


def handle(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

