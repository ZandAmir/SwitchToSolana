import telebot
import requests
import json
import time
import threading

# Telegram Bot Token
BOT_TOKEN = "7593167212:AAGgMbgHbRPGrxLy-z4D8MkZ-oiMK4OJpok"

# Initialize Telegram Bot
bot = telebot.TeleBot(BOT_TOKEN)

# Global variables for tracking data
user_data = {}
running_threads = {}

# Fetch real-time prices from Binance
def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        response = requests.get(url)
        data = response.json()
        return float(data["price"])
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

# Handle /start command
@bot.message_handler(commands=['start'])
def start_command(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    bot.send_message(chat_id, "Welcome to SWITCH TO SOLANA Bot! Please enter the Number of AVAX:")

# Handle user input
@bot.message_handler(func=lambda message: True)
def handle_input(message):
    chat_id = message.chat.id
    text = message.text

    if chat_id not in user_data:
        user_data[chat_id] = {}

    if "A" not in user_data[chat_id]:  # Number of AVAX
        try:
            user_data[chat_id]["A"] = float(text)
            bot.send_message(chat_id, "Enter the Number of SOLANA:")
        except ValueError:
            bot.send_message(chat_id, "Invalid input! Please enter a number.")
    
    elif "SOL" not in user_data[chat_id]:  # Number of SOLANA
        try:
            user_data[chat_id]["SOL"] = float(text)
            bot.send_message(chat_id, "Enter the Desired Difference % (e.g., 5 for 5%):")
        except ValueError:
            bot.send_message(chat_id, "Invalid input! Please enter a number.")
    
    elif "threshold" not in user_data[chat_id]:  # Desired Difference %
        try:
            user_data[chat_id]["threshold"] = float(text) / 100  # Convert to decimal
            user_data[chat_id]["B"] = get_price("AVAXUSDT")  # Store initial AVAX price
            user_data[chat_id]["D_start"] = get_price("SOLUSDT")  # Store initial SOL price
            bot.send_message(chat_id, "Monitoring started! I will notify you when the difference is reached.")

            # Start monitoring in a separate thread
            thread = threading.Thread(target=monitor_prices, args=(chat_id,))
            thread.start()
            running_threads[chat_id] = thread

        except ValueError:
            bot.send_message(chat_id, "Invalid input! Please enter a number.")

# Function to continuously monitor prices
def monitor_prices(chat_id):
    while chat_id in running_threads:
        A = user_data[chat_id].get("A")
        SOL = user_data[chat_id].get("SOL")
        B = user_data[chat_id].get("B")  # Initial AVAX price
        D_start = user_data[chat_id].get("D_start")  # Initial SOL price
        threshold = user_data[chat_id].get("threshold")

        C = get_price("AVAXUSDT")  # Current AVAX price
        D = get_price("SOLUSDT")   # Current SOLANA price

        if None in [A, SOL, B, C, D, D_start, threshold]:
            bot.send_message(chat_id, "Error fetching prices! Retrying...")
            continue  # Retry

        avax_growth = (C - B) / B  # AVAX growth from start
        sol_growth = (D - D_start) / D_start  # SOL growth from start
        percentage_diff = avax_growth - sol_growth  # Difference

        solana_profit = (A * (C - B)) / D  # Calculate SOLANA PROFIT

        # Send live update to user
        bot.send_message(chat_id, f"AVAX Price: ${C}\nSOLANA Price: ${D}\nSOLANA PROFIT: {solana_profit:.4f}\nAVAX % Over SOLANA: {percentage_diff:.2%}")

        # Check if threshold is met
        if percentage_diff >= threshold:
            bot.send_message(chat_id, "🚀 Threshold Reached! AVAX has exceeded SOLANA by your desired percentage!")
            break

        time.sleep(30)  # Wait before rechecking

# Handle /stop command
@bot.message_handler(commands=['stop'])
def stop_command(message):
    chat_id = message.chat.id
    if chat_id in running_threads:
        del running_threads[chat_id]  # Stop the monitoring loop
        bot.send_message(chat_id, "⏹️ Monitoring stopped.")
    else:
        bot.send_message(chat_id, "No active monitoring session found.")

# Handle /close command (Stop bot execution)
@bot.message_handler(commands=['close'])
def close_command(message):
    bot.send_message(message.chat.id, "🛑 Shutting down bot...")
    time.sleep(1)
    exit()

# Start the bot polling loop
bot.polling(none_stop=True)
