print ("command_parser.py")
import openai
import os
import re
import json

import mail_utils
import language

my_lang = language()

def get_command_language():
   return my_lang.get_language()
   
## Setup for OpenAI
openai.api_key      = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORG")
request_model       = "gpt-3.5-turbo" #"text-davinci-003""gpt-3.5-turbo"
request_max_tokens  = 500

def save_object( obj, filename):
   with open(filename, 'w') as file_object:  #open the file in write mode
       json.dump(obj, file_object)   # json.dump() function to stores the set of numbers in numbers.json file

def load_object( filename):
    with open(filename, 'r') as file_object:  
        data = json.load(file_object)  
        return data
        
internal_state = load_object("internals.json")
config_data    = load_object("config.json")

text = "Add potatoes, rice, salad cheese, strawberry yoghurt and bananas to my shopping list."
#text = "Please delete my shoppinglist."

def parse_command(t):
    response_exit = False
    response_text = "I didn't understand that."
    
    add_to_shopping_list = r"(please\s+)?(\s*add\s+)(?P<items>.*)(\s+to\s+my\s+shopping\s*list)(.*)"
    query_shopping_list  = r"(what)(\s+is|\'s)(\s+on\s+(my|the)\s+shopping\s*list)(.*)"
    empty_shopping_list  = r"(please\s+)?(\s*delete\s+my\s+shopping\s*list)(.*)"
    send_shopping_list   = r"(please\s+)?\s*(send|email)\s+(my|the)(\s+shopping\s*list)(?P<to_addr>\s+to\s+\w+)?(.*)"
    ask_chatGPT          = r"(A|a)(sk\s+)(chat)?(\s*gpt)?(?P<query>.*)"
    exit_command         = r"(that)(\s+is|\'s)\s+all.*"
    email_strip          = r"(\s*to\s+)(?P<mail_name>\w+)"
    change_to_english    = r"(\s*change\s+to\s+(english|English))"
    change_to_persian    = r"(\s*change\s+to\s+(persian|Persian|farsi|Farsi))"

    ### Change to English ###
    m = re.match(change_to_english, t.lower())
    if m != None:
      my_lang.set_to_english()
      response_text = "Lanquage has been changed to English."

    ### Change to Farsi ###
    m = re.match(change_to_persian, t.lower())
    if m != None:
      my_lang.set_to_farsi()
      response_text = "Lanquage has been changed to Persian."
      
    ### Add to shopping list ###
    m = re.match(add_to_shopping_list, t.lower())
    if m != None:
        items = []
        c     = m.group("items").split(",")
        print("c=", str(c))
        for cs in c:
            o = cs.split("and")
            for i in o:        
               items.append(i.strip().title())
        print("items=", str(items))
        for i in items:
           if i not in internal_state["shopping_list"]:
               internal_state["shopping_list"].append(i)
        response_text = "The items have been added."    

    ### Query shopping list ###
    m = re.match(query_shopping_list, t.lower())
    if m != None:
        items = internal_state["shopping_list"]
        print("items=", str(items))
        if len(internal_state["shopping_list"]) > 0:
            response_text = "Your shopping list contains "
            for i in internal_state["shopping_list"]:
               response_text += i + ", "
        else:
            response_text = "Your shopping list is empty."
            
    ### Delete shopping list ###
    m = re.match(empty_shopping_list, t.lower())
    if m != None:
        internal_state["shopping_list"] = []
        response_text = "The shopping list has been deleted."
        
    print("internal_state=", str(internal_state))    

    ### Send shopping list ###
    m = re.match(send_shopping_list, t.lower())
    if m != None:
         my_shopping_list = ""
         n = 1
         for i in internal_state["shopping_list"]:
             my_shopping_list += str(n) + ". " + i + "\n"
             n += 1
             
         # find the to address
         if m.group("to_addr") != None:
              email_to_match = re.match(email_strip, m.group("to_addr").lower())

              email_to = config_data["email_addresses"][email_to_match.group("mail_name")]
              print("emailing to ", email_to)
         else:
              email_to = "pearcemark21@gmail.com"
              print("default email")              
         mail_utils.send_email("markpearce47@gmail.com", email_to, "Shopping List", my_shopping_list)
         response_text = "Your shopping list has been sent."


    ### Ask ChatGPT ###
    m = re.match(ask_chatGPT, t)
    if m != None:
        q = m.group("query")
        messages =[{"role":"user", "content": q}]
        ChatGPT_response = openai.ChatCompletion.create(model       = request_model, 
                                                        messages    = messages, 
                                                        temperature = 0, 
                                                        max_tokens  = request_max_tokens)
        response_text = "ChatGPT Responded..."
        for r in ChatGPT_response["choices"]:
            response_text += r["message"]["content"] + "\n"
        print("response_text=", response_text)
    
    ### Exit Command ####
    m = re.match(exit_command, t.lower())
    if m != None:
        response_text = "Good bye."
        response_exit = True
    #
    # Command has been processed so save the updated internal state
    #
    save_object(internal_state, "internals.json")
    
    return response_text, response_exit
