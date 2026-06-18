#This is the python code. The goal of this code is to take a menu as an input and via the terminal only interact
#witht the customer. The cutomer can place an order and this code will then calculate the total cost of the
#customer's order. 
#For version 1 we will assume that the food item ordered is available in the shop 

from dotenv import load_dotenv
from tabulate import tabulate
import re
import os, sys
import json
_ = load_dotenv()
from rich import print_json
import base64
from pydantic import BaseModel, Field
import fitz

from openai import OpenAI
Client = OpenAI()

structured_menu = [] #it is a list of dictionaries of the form {"food item":";"price"}
order_list = [] #It is also to be a list of dictionaries having 3 values - food_item, price, quantity
table_rows = []  #this is list of all the food item name and their corresponding prices
price_lookup = {} #A dictionary to store the corresponding the food item - price mapping

def ready_menu(menu_list):
    for food in menu_list["items"]:
        table_rows.append([
            food["name"],
            food["price"],
        ])
    
    for food in table_rows:
        price_lookup[food[0].lower()] = food[1]
    


def print_menu():
    print("Printing from Show Menu")
    headers = ["Item Name","Item Price"]
    print(tabulate(table_rows, headers=headers, tablefmt="grid", colalign=("left", "centre")))
    return ("Here's your menu. Please let me know what would you like to have today?")
   #print(table_rows)


def check_item(food_item):
    print(f"checking item {food_item}")
    if(food_item in price_lookup):
        return 1
    else:
        return 0

def get_price(food_item, quantity = 1):
    print(f"getting the price of {food_item}")
    if(check_item(food_item)):
        return(price_lookup[food_item]*quantity)
    else:
        return("The ordered food item does not exist")


def print_final_bill():
    #print("\033[H\033[J", end="")
    print("Here is your total bill from the function! ")
    bill_total = 0
    table_rows = []
    for order in order_list:
        table_rows.append([
            order["food_item"],
            order["quantity"],
            order["bill"],
        ])
        bill_total += order["bill"]

    #print(table_rows)
    headers = ["Food Item", "Quantity", "Bill"]
    print(tabulate(table_rows, headers=headers, tablefmt="grid"))
    print(f"Your total order is {bill_total}")
    print(" \n \n")
    sys.exit()

def done_ordering():
    print("Thank you for ordering with us today. bon apetitie! ")
    sys.exit()


def cancel_everything():
    order_list.clear()
    return("I have successfully cleared all your order list")


def cancel_order(food_item):
    bool = False
    food_item = food_item.strip().lower()
    for food in order_list:
        if(food["food_item"]==food_item):
            bool = True
    if bool:
        order_list[:] = [
            order for order in order_list
            if order["food_item"] != food_item
            ]
        return(f"The order for {food_item} has been successfully cancelled" )
    else:
        return("Please place your order first before you can cancel the order")


def add_order(food_item, quantity = 1):
    food_item = food_item.strip().lower()
    for food in order_list:
        if food["food_item"] == food_item:
            food["quantity"] += quantity
            food["bill"] = get_price(food_item, quantity)
            return "Your order has been updated"
    return take_order(food_item, quantity)


def take_order(food_item, quantity = 1):
    "This function takes in the user order"
    print("Taking in the order now")
    food_item = food_item.strip().lower()
    
    available = check_item(food_item)
    print(f"the food item is {available}")

    if available:
        order_list.append({
            "food_item": food_item,
            "quantity" : quantity,
            "bill": get_price(food_item)*quantity
        })
        return("Your order has been successfully placed! ")
    else:
        return("The ordered food item does note exist")


available_tools = [
    {
        "type":"function",
        "function":
        {
            "name": "take_order",
            "description": "The role of this function is to take the order of the user.",
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
    },
    {
        "type": "function",
        "function": {
            "name":"add_order",
            "description":"This function is used to add more items to the user's order.",
            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "food_item":{
                        "type":"string",
                        "description":"This field contains the name of the food item that the user wants to"
                        "update the order for"
                    },
                    "quantity":{
                        "type":"integer",
                        "description":"This is the extra quantity of the food item that the user wants to order"
                },
            },
            "required":["food_item", "quantity"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"cancel_order",
            "description":"This function is used to cancel the order for a particular food item by the user. It takes "
            "as input the name of the food item if the food item exists and deletes it from the order list.",
            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "food_item":{
                        "type":"string",
                        "description":"This field contains the name of the food item that the user wants to"
                        "update the order for"
                    },
                
            },
            "required":["food_item"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"get_price",
            "description":"This functions returns the price of an ordered food item",
            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "food_item":{
                        "type":"string",
                        "description":"This field contains the name of the food item that the user wants to"
                        "update the order for"
                    },
                    "quantity":{
                        "type":"integer",
                        "description":"This is the extra quantity of the food item that the user wants to order"
                },
                
            },
            "required":["food_item", "quantity"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"check_item",
            "description":"This functions checks if a food item exists in the menu or not",
            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "food_item":{
                        "type":"string",
                        "description":"This field contains the name of the food item that the user wants to"
                        "update the order for"
                    },
                
            },
            "required":["food_item"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"cancel_everything",
            "description":"This function is used to cancel all the orders for the user.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"print_final_bill",
            "description":"This function is used to print the final bill. Once the user has decided that they "
            "are done ordering and that they do not want to order any more food item, "
            "or they want to checkout,  we will print the final "
            "bill for the user and break out the program",
            "parameters": {
                "type": "object",
                "properties": {},
            }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"done_ordering",
            "description":"This function is used to break out of the code, when the user is done with their"
            "order",
            "parameters": {
                "type": "object",
                "properties": {},
            }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"print_menu",
            "description":"This function prints the menu.",
            "parameters": {
                "type": "object",
                "properties": {},
            }
    }
    }
]


class menu_data(BaseModel):
    name: str = Field(description="The name of each food item in the menu provided")
    price: float = Field(description="The price of each food item in the corresponding menu")

class MenuResponse(BaseModel):
    items: list[menu_data]

def pdf_to_png(path):
    doc = fitz.open(path)
    images = []

    for page in doc:
        pix = page.get_pixmap(dpi = 200)
        images.append(base64.b64encode(pix.tobytes("png")).decode())
    
    return images

def extract_menu_from_images(images):
    content = [
        {
            "type":"text",
            "text":"You are smart text extractor agent. Your job is to extract the name of the food items from"
            "the menu provided along with the price of each food item. Return ONLY valid JSON matching this schema: "
            '{"items": [{"name": "...", "price": ...}]}'
        }
    ]

    for img in images:
        content.append(
            {
                "type":"image_url",
                "image_url":{"url":f"data:image/png;base64,{img}"}
            }
        )
    
    response = Client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role":"user",
                "content": content
            }
        ],
        response_format={"type":"json_object"}
    )

    raw = response.choices[0].message.content

    return raw


def main():
    "this is the main function"

   #print("\033[H\033[J", end="")
    print("/n /n /n")
    print("New Code Running")

    path = "Menu_img_1.jpg"

    images = pdf_to_png(path)
    menu_list = extract_menu_from_images(images)
    menu_list = MenuResponse.model_validate_json(menu_list)  # validates structure
    
    ready_menu(menu_list.model_dump())

    print(table_rows)
    print("**************************")
    print(price_lookup)

    print("Please place your order")
    user_input = input().strip().lower()

    #print("Checking the item first ")
    #print(check_item(user_input))

    #print("Getting the price now. ")
    #print(get_price(user_input))

    
    #i = 0
    message = [
        {"role":"system","content":"You are an order taking agent. Your job is to take the users food order."
        "You have access to certain functions that performs functions as such - taking in the user order,"
        "checking if the ordered food item is available or not, updating the user's order, cancelling an order"
        "if the user requests for it, or cancelling all the orders if the user requests so, printing the final bill for the user."
        "You have access to the menu file that has already been converted from an image pdf file to a dictionary that will be"
        "used to traverse the food items that are available."
        "Also all the prices are to be in Indian Rupees, use it's symbol and not dollars"
        },
        {"role":"user","content": user_input.lower()}
        ]
    
    value = True
    while(value):
        "continue with the function"
    
        response = Client.chat.completions.create(
            model= "gpt-4o",
            messages= message,
            temperature=1,
            tools=available_tools,
        )

        temp_message = response.choices[0].message
        message.append(response.choices[0].message)

        if(temp_message.tool_calls):
            for i in range(len(temp_message.tool_calls)):
                tool_call = temp_message.tool_calls[i]
                call_id = tool_call.id
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"Calling the function. {function_name}")

                if function_name == "take_order":
                    function_response = take_order(
                        food_item=function_args.get("food_item"),
                        quantity= function_args.get("quantity")
                    )
                
                if function_name == "cancel_everything":
                    function_response = cancel_everything()
                
                if function_name == "cancel_order":
                    function_response = cancel_order(
                        food_item= function_args.get("food_item")
                    )
                
                if function_name == "get_price":
                    function_response = get_price(
                        food_item= function_args.get("food_item"),
                        quantity= function_args.get("quantity")
                    )
                
                if function_name == "check_item":
                    function_response = check_item(
                        food_item= function_args.get("food_item")
                    )

                if function_name == "add_order":
                    function_response = add_order(
                        food_item= function_args.get("food_item"),
                        quantity= function_args.get("quantity")
                    )
                
                if function_name == "print_final_bill":
                    function_response = print_final_bill()
                
                if function_name == "print_menu":
                    function_response = print_menu()
                
                if function_name == "done_ordering":
                    function_response = done_ordering()


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

        print(temp_message)
        #print("Printed your message")
        user_input = input()
        #print(f"Your input text is {user_input}")

        message.append(
            {
                "role":"user",
                "content":user_input
            }
        )

        
    

if __name__ == "__main__":
    main()
