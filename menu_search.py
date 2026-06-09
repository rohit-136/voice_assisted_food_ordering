#This is the python code. The goal of this code is to take a menu as an input and via the terminal only interact
#witht the customer. The cutomer can place an order and this code will then calculate the total cost of the
#customer's order. 
#For version 1 we will assume that the food item ordered is available in the shop 

from dotenv import load_dotenv
from pypdf import PdfReader
import re
import os, sys
import json
_ = load_dotenv()
from rich import print_json

from openai import OpenAI
Client = OpenAI()

structured_menu = [] #it is a list of dictionaries of the form {"food item":";"price"}
order_list = [] #It is also to be a list of dictionaries having 3 values - food_item, price, quantity


def show_menu():
    reader = PdfReader("Menu.pdf")

    for page in reader.pages:
        text = page.extract_text() or ""
        #print(page)

        for line in text.splitlines():
            print(line)
            match = re.fullmatch(
                r"(.+?)\s*\.{2,}\s*\$?(\d+(?:\.\d{2})?)",
                line.strip()
            )

            if match:
                key = match.group(1).strip().lower()
                price_text = match.group(2)
                price = float(price_text) if "." in price_text else int(price_text)
                structured_menu.append({key: price})

def check_price(food_item):
    for item in structured_menu:
        for food in item:
            if (food == food_item):
                return int(item[food])
    return 0


def take_order(food_item, quantity = 1):
    "This function takes in the user order"
    #first we check the price of that item
    price = check_price(food_item)

    if price != 0:
        order_list.append({
            "food_item": food_item,
            "quantity" : quantity,
            "bill": price*quantity
        })
    else:
        print(f"I do not what {food_item} is. Please check your spelling again. I am not placing that order currently")

available_tools = [
    {
        "type":"function",
        "function":
        {
            "name": "take_order",
            "description": "The role of this function is to take the order of the user. What is essentially does is "
            "that it takes in the name of the food item,  the quantitiy required and a list of dictionaries that"
            "contains the orders till now. It then accesses the menu via the check_price function to see"
            "whether we serve that particular food item or not. If we do serve, it multiplies the price of that food item"
            "with the quantitiy required and returns an updated list. If we do not serve that food item, it simply"
            "says that sorry we do not serve your required food item",

            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "food_item": {
                        "type":"string",
                        "description" : "The name of the food item that the user wants to order"
                    },
                    "quantity":{
                        "type": "integer",
                        "description":"The number of the food items that the user wants to order"
                    },
                    "order_list":{
                        "type":"array",
                        "description":"The combined total order list till now. It is a list of dictionaries"
                    }
                },
                "required":["food_item","quantity","order_list"]
            }
        }
    }
]


def main():
    "this is the main function"
    print("Hello there! What can I order for you today ?")
    show_menu()
    user_input = input()
    i = 0
    
    while(user_input):
        "continue with the function"

        message = [
        {"role":"system","content":"You are a order taking agent. Your job is to ask the user what they want "
        "to order and based on that you need to place their order and show what their total bill is.  The"
        "user might also order 2 or more items of the same kind. So take care of that as well. Use all the tools"
        "that you have been provided access to. If the user does not mention how many quantities of the food item they want,"
        "assume by default that they want 1 quantity of the food item."},
        {"role":"user","content": user_input.lower()}
        ]

    
        response = Client.chat.completions.create(
            model= "gpt-4o",
            messages= message,
            temperature=1,
            tools=available_tools,
        )

        temp_message = response.choices[0].message
        message.append(response.choices[0].message)


        for i in range(len(temp_message.tool_calls)):
            tool_call = temp_message.tool_calls[i]
            call_id = tool_call.id
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "take_order":
                function_response = take_order(
                    food_item=function_args.get("food_item"),
                    quantity= function_args.get("quantity")
                )

            message.append({
                "role":"tool",
                "tool_call_id": call_id,
                "name": function_name,
                "content": json.dumps(function_response)
            }
            )

        response = Client.chat.completions.create(
            model = "gpt-4o",
            messages=message
        )

            
        temp_message = response.choices[0].message.content

        print(" Would you like to order anything else? Y/N")
        temp_input = input()

        if(temp_input.lower() == "y"):
            print("Please state your order ")
            user_input = input()
        else:
            user_input = None
    
    print("\033[H\033[J", end="")
    print("Here is your total bill ! ")

    for order in order_list:
        print(f"{order["food_item"]}...........{order["quantity"]}........{order["bill"]}")

    print(" \n \n")


if __name__ == "__main__":
    main()
