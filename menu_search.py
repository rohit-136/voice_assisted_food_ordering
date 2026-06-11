#This is the python code. The goal of this code is to take a menu as an input and via the terminal only interact
#witht the customer. The cutomer can place an order and this code will then calculate the total cost of the
#customer's order. 
#For version 1 we will assume that the food item ordered is available in the shop 

from dotenv import load_dotenv
from pypdf import PdfReader
from tabulate import tabulate
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

def print_final_bill():
    print("\033[H\033[J", end="")
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

def done_ordering():
    print("Thank you for ordering with us today. bon apetitie! ")
    sys.exit()


def cancel_everything():
    order_list.clear()
    print("I have successfully cleared all your order list")
    return


def cancel_order(food_item):
    bool = False
    for food in order_list:
        if(food["food_item"]==food_item):
            bool = True
    if bool:
        order_list[:] = [
            order for order in order_list
            if order["food_item"] != food_item
            ]
        print(f"The order for {food_item} has been successfully cancelled" )
        return
    else:
        print("Please place your order first before you can cancel the order")
        return


def add_order(food_item, quantity = 1):
    food_item = food_item.strip().lower()

    for food in order_list:
        if (food["food_item"].strip().lower() == food_item):
            food["quantity"] += quantity
            food["bill"] = food["quantity"] * check_price(food_item)
            print("Your order has been updated")
            return
    print("Please place the order first before updating")
    return

def update_order(food_item, quantity = 1):
    food_item = food_item.strip().lower()

    for food in order_list:
        if (food["food_item"].strip().lower() == food_item):
            food["quantity"] = quantity
            food["bill"] = food["quantity"] * check_price(food_item)
            print("Your order has been updated")
            return
    print("Please place the order first before updating")
    return


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
    },
    {
        "type": "function",
        "function": {
            "name":"update_order",
            "description":"This function is used to update the order of the user.",
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
                        "description":"This is the updated quantity of the food item that the user wants to order"
                },
            },
            "required":["food_item", "quantity"]
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name":"add_order",
            "description":"This function is used to add more items to the user's already existing order.",
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
    }
]


def main():
    "this is the main function"
    show_menu()
    print("Order bolo Order Order oooooorrrrrdddddeeeeerrrrrrrrrrrrrrrrrrrr")
    
    user_input = input()
    i = 0
    message = [
        {"role":"system","content":"You are a order taking agent. Your job is to ask the user what they want "
        "to order and based on that you need to place their order and show what their total bill is.  The"
        "user might also order 2 or more items of the same kind. So take care of that as well. Use all the tools"
        "that you have been provided access to. If the user does not mention how many quantities of the food item they want,"
        "assume by default that they want 1 quantity of the food item. "},
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
                
                if function_name == "update_order":
                    function_response = update_order(
                        food_item= function_args.get("food_item"),
                        quantity= function_args.get("quantity")
                    )

                if function_name == "add_order":
                    function_response = add_order(
                        food_item= function_args.get("food_item"),
                        quantity= function_args.get("quantity")
                    )
                
                if function_name == "print_final_bill":
                    function_response = print_final_bill()
                
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
