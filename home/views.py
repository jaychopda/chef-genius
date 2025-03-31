from django.shortcuts import render, HttpResponse, redirect
from datetime import datetime

import numpy as np
from home.models import Contact,UserRegisterForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from newsapi import NewsApiClient
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

# from read_barcode import scan_barcode  # Import barcode scanner method
from pyzbar.pyzbar import decode
import cv2

import requests
from bs4 import BeautifulSoup

from supabase import create_client, Client
from httpx import ConnectError  # Import ConnectError for handling connection issues

# cap = cv2.VideoCapture(0)  # Open the default camera
SUPABASE_URL= "https://cjykkqroxpdmmpclfibc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNqeWtrcXJveHBkbW1wY2xmaWJjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMyNDQ1MzgsImV4cCI6MjA1ODgyMDUzOH0.UsKGIJ2pksd2nK4O3lVKvqujSzN-U-nlZrFmjU2WcwM"

# Create Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def invetory(request):
    try:
        # Fetch data from Supabase
        response = supabase.table("overall_stock").select("*").order("id").execute()  # Sort by id in ascending order
        data = response.data if response.data else []  # Handle cases where data is None

        # Log an error message if no data is retrieved
        if not data:
            print("No data retrieved from Supabase or an error occurred.")
            print(data)

        # Pass the fetched data to the template
        return render(request, 'invetory.html', context={"mylist": data})
    except ConnectError as e:
        print(f"Connection error: {str(e)}")
        messages.error(request, "Unable to connect to the database. Please try again later.")
        return render(request, 'invetory.html', context={"mylist": []})
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'invetory.html', context={"mylist": []})




def process_sale(item_name, quantity):
    """
    Process a sale, update stock in Supabase.
    """
    # Step 1: Fetch raw materials required for the item
    response = supabase.table("rawmaterials").select("raw_materials").eq("item_name", item_name).execute()
    
    if not response.data:
        print("Error: Item not found in RawMaterials2")
        return

    raw_materials = response.data[0]["raw_materials"]  # JSONB object (list of dicts)

    # Step 2: Iterate over required raw materials
    for material in raw_materials:
        material_name = material["name"]
        required_qty = material["stock_required"] * quantity  # Calculate total required quantity

        # Step 3: Fetch stock from stock_expire, ordered by nearest expiry date
        stock_response = supabase.table("stock_expire").select("*").eq("name", material_name).order("purchase_date", desc=False).execute()
 
        stock_rows = stock_response.data  # List of stock entries

        # Step 4: Subtract stock starting from the nearest expiry date
        for stock_row in stock_rows:
            stock_id = stock_row["id"]
            available_stock = stock_row["stock"]

            if required_qty <= 0:
                break  # No more stock needed

            if available_stock >= required_qty:
                # Enough stock available, just subtract
                new_stock = available_stock - required_qty
                supabase.table("stock_expire").update({"stock": new_stock}).eq("id", stock_id).execute()
                required_qty = 0  # Stock requirement fulfilled
            else:
                # Not enough stock in this batch, subtract what's available
                supabase.table("stock_expire").update({"stock": 0}).eq("id", stock_id).execute()
                required_qty -= available_stock  # Reduce remaining required quantity

        # Step 5: If required_qty is still > 0, it means stock is insufficient
        if required_qty > 0:
            print(f"⚠ Warning: Not enough {material_name} in stock!")

    # Step 6: Insert the sale into the Sales table
    supabase.table("sales").insert({"name": item_name, "quantity": quantity}).execute()

    print(f"✅ Sale processed: {quantity} x {item_name}")


@csrf_exempt
def process_cart(request):
    """
    Process the cart items and call process_sale for each item.
    """
    if request.method == "POST":
        try:
            cart_data = json.loads(request.body)  # Expecting a JSON object with cart items
            print("Received cart data:", cart_data)  # Debugging log
            for item in cart_data:
                item_name = item["name"]
                quantity = item["quantity"]
                process_sale(item_name, quantity)  # Call process_sale for each item
            return JsonResponse({"status": "success", "message": "Cart processed successfully!"})
        except Exception as e:
            print("Error processing cart:", str(e))  # Debugging log
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

def menu(request):
    return render(request, 'menu_optimization.html')

def cart(request):
    return render(request, 'cart.html')

def dashboard(request):
    return render(request, 'dashboard.html', context={"daily_sales": calculate_daily_sales()})


def waste_analysis(request):
    try:
        # Fetch data from the "waste" table in Supabase
        response = supabase.table("waste").select("*").order("id").execute()  # Sort by id in ascending order
        data = response.data if response.data else []  # Handle cases where data is None

        # Log an error message if no data is retrieved
        if not data:
            print("No data retrieved from the waste table or an error occurred.")
            print(data)

        # Pass the fetched data to the template
        return render(request, 'waste_analysis.html', context={"mylist": data})
    except ConnectError as e:
        print(f"Connection error: {str(e)}")
        messages.error(request, "Unable to connect to the database. Please try again later.")
        return render(request, 'waste_analysis.html', context={"mylist": []})
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'waste_analysis.html', context={"mylist": []})

def order(request):
    try:
        # Fetch data from Supabase
        # Fetch and Print Table Data
        response = supabase.table("sales").select("*").execute()
        for row in response.data:
            print(row , "\n")

        # Pass the fetched data to the template
        return render(request, 'menu.html', context={"mylist": response.data})
    except ConnectError as e:
        print(f"Connection error: {str(e)}")
        messages.error(request, "Unable to connect to the database. Please try again later.")
        return render(request, 'menu.html', context={"mylist": []})
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'menu.html', context={"mylist": []})


def calculate_daily_sales():
    """
    Fetches today's total orders, calculates total revenue, and computes the Average Order Value (AOV).
    """
    # Get today's date
    today_date = datetime.today().strftime("%Y-%m-%d")

    # Fetch today's sales data
    sales_response = (
        supabase.table("sales")
        .select("name", "quantity")
        .filter("date", "gte", f"{today_date} 00:00:00")
        .filter("date", "lt", f"{today_date} 23:59:59")
        .execute()
    )

    # If no sales found
    if not sales_response.data:
        print(f"⚠ No sales found for {today_date}!")
        return

    # Total Orders Count
    total_orders = sum(sale["quantity"] for sale in sales_response.data)

    # Fetch item prices from rawmaterials
    price_response = supabase.table("rawmaterials").select("item_name", "price").execute()
    
    # Create a dictionary {item_name: price}
    price_dict = {item["item_name"]: item["price"] for item in price_response.data}

    # Calculate total revenue
    total_revenue = sum(sale["quantity"] * price_dict.get(sale["name"], 0) for sale in sales_response.data)

    # Calculate Average Order Value (AOV)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

    # Print Results
    print("📊 Today's Sales Summary")
    print(f"🛒 Total Orders: {total_orders}")
    print(f"💰 Total Revenue: ₹{total_revenue}")
    print(f"📈 Average Order Value (AOV): ₹{avg_order_value:.2f}")
    
    return [total_orders,total_revenue,avg_order_value]

def barcode_scanner_page(request):
    return render(request, "barcode_scanner.html")

@csrf_exempt
def process_barcode(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print("Received data:", data)  # Debugging log
        barcode_number = data.get("barcode")

        if not barcode_number:
            return JsonResponse({"error": "No barcode provided"}, status=400)

        item_code = int(barcode_number[:9])
        quantity = int(barcode_number[9:])

        response = supabase.table("raw_item_expire").select("item_name").eq("code", item_code).execute()
        if not response.data:
            return JsonResponse({"error": f"Item with code {item_code} not found"}, status=404)

        item_name = response.data[0]["item_name"]
        purchase_date = datetime.today().date().isoformat()  # Fixed incorrect usage of datetime.date.today()

        supabase.table("stock_expire").insert({
            "name": item_name,
            "stock": quantity,
            "purchase_date": purchase_date
        }).execute()

        return JsonResponse({
            "message": "Stock Updated",
            "barcode": barcode_number,
            "item": item_name,
            "quantity": quantity,
            "date": purchase_date
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

from PIL import Image

@csrf_exempt
def process_uploaded_barcode(request):
    if request.method == "POST" and request.FILES.get("image"):
        try:
            # Read the uploaded image
            image = request.FILES["image"]
            img = Image.open(image)

            # Decode the barcode from the image
            barcodes = decode(img)
            if not barcodes:
                return JsonResponse({"status": "error", "message": "No barcode detected in the image."})

            barcode_data = barcodes[0].data.decode("utf-8")
            item_code = int(barcode_data[:9])  # Extract first 9 digits as item code
            quantity = int(barcode_data[9:])  # Extract last digits as quantity

            # Fetch item details from raw_item_expire using item_code
            response = supabase.table("raw_item_expire").select("item_name").eq("code", item_code).execute()
            if not response.data:
                return JsonResponse({"status": "error", "message": f"Item with code {item_code} not found."})

            item_name = response.data[0]["item_name"]
            purchase_date = datetime.today().strftime("%Y-%m-%d")  # Today's date

            # Insert new stock entry into stock_expire
            supabase.table("stock_expire").insert({
                "name": item_name,
                "stock": quantity,
                "purchase_date": purchase_date
            }).execute()

            return JsonResponse({
                "status": "success",
                "barcode": barcode_data,
                "item": item_name,
                "quantity": quantity,
                "date": purchase_date
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request."})

def update_log(request):

    # 1️⃣ Set date to today if not provided
    date = datetime.today().date().isoformat()  # Fixed incorrect usage of datetime.date.today()

    print(f"📅 Processing stock log for date: {date}")

    # 2️⃣ Fetch sales data for the given date (ignoring time)
    sales_response = (
        supabase.table("sales")
        .select("name", "quantity")
        .filter("date", "gte", f"{date} 00:00:00")
        .filter("date", "lt", f"{date} 23:59:59")
        .execute()
    )

    if not sales_response.data:
        print(f"⚠ No sales data found for {date}!")
        return

    # 3️⃣ Process sales and calculate total raw materials used
    used_materials = {}

    for sale in sales_response.data:
        item_name = sale["name"]
        quantity = sale["quantity"]

        # Fetch raw materials for the sold item
        raw_response = supabase.table("rawmaterials").select("raw_materials").eq("item_name", item_name).execute()

        if raw_response.data:
            raw_materials = raw_response.data[0]["raw_materials"]
            for material in raw_materials:
                mat_name = material["name"]
                required_qty = material["stock_required"] * quantity

                # Add the used raw material quantity to the total
                used_materials[mat_name] = used_materials.get(mat_name, 0) + required_qty

    # 4️⃣ Fetch current stock from overall_stock
    stock_response = supabase.table("overall_stock").select("name", "stock").execute()
    
    if not stock_response.data:
        print("⚠ No stock data found!")
        return

    current_stock = {item["name"]: item["stock"] for item in stock_response.data}

    # 5️⃣ Calculate stock left after usage
    remaining_stock = {}
    for mat_name, used_qty in used_materials.items():
        remaining_stock[mat_name] = max(current_stock.get(mat_name, 0) - used_qty, 0)

    # 6️⃣ Insert remaining stock into stock_log
    insert_response = supabase.table("stock_log").insert({
        "date": date,
        "item_stock": remaining_stock  # Stores only remaining stock in JSON format
    }).execute()

    print(f"✅ Stock log updated for {date}")
    print(f"📉 Remaining Stock After Sales: {remaining_stock}")
    

    data = zip(remaining_stock.keys(), remaining_stock.values())

    return render(request, 'update_log.html', context={"mylist": data})

@csrf_exempt
def add_to_waste(request):
    print("Hello .....0")
    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse the JSON data from the request
            item_name = data.get("item_name")
            quantity = int(data.get("quantity"))  # Convert quantity to an integer
            reason = data.get("reason")
            print("Hello .....1")


            if not item_name or not quantity or not reason:
                return JsonResponse({"status": "error", "message": "All fields are required."}, status=400)
            print("Hello .....2")
            # Insert the waste entry into the waste table
            supabase.table("waste").insert({
                "item_name": item_name,
                "quantity": quantity,
                "reason": reason,
                "date": datetime.today().strftime("%Y-%m-%d")
            }).execute()
            print("Hello .....3")
            # Delete the specified quantity from stock_expire
            stock_response = supabase.table("stock_expire").select("*").eq("name", item_name).order("purchase_date", desc=False).execute()
            stock_rows = stock_response.data

            for stock_row in stock_rows:
                stock_id = stock_row["id"]
                available_stock = stock_row["stock"]

                if quantity <= 0:
                    break

                if available_stock >= quantity:
                    # Subtract the quantity from the current stock
                    new_stock = available_stock - quantity
                    supabase.table("stock_expire").update({"stock": new_stock}).eq("id", stock_id).execute()
                    quantity = 0
                else:
                    # Remove the entire stock from this batch
                    supabase.table("stock_expire").update({"stock": 0}).eq("id", stock_id).execute()
                    quantity -= available_stock

            return JsonResponse({"status": "success", "message": "Item added to waste and stock updated."})
        except Exception as e:
            print(f"Error in add_to_waste: {str(e)}")  # Log the error for debugging
            return JsonResponse({"status": "error", "message": "An unexpected error occurred. Please try again later."}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request method."}, status=405)