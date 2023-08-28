import os
import telebot
from telebot import types
from math import radians, sin, cos, sqrt, atan2
from flask import Flask, request

# Replace 'YOUR_BOT_TOKEN' with your actual bot token obtained from BotFather on Telegram
bot = telebot.TeleBot('6502481073:AAFJbvGP7lz_XVHv5OdNatrEbab7WmmVAMM')

server = Flask(__name__)

@server.route('/' + bot.token, methods=['POST'])
def get_message():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://your-heroku-app-url.herokuapp.com/' + bot.token)
    return "!", 200

# A dictionary to store donor data (replace with a database in a real implementation)
donors = {}

# Function to save user data to the list.txt file
def save_to_list(user_data):
    with open('list.txt', 'a') as file:
        file.write(user_data + '\n')

# Function to load donor data from the list.txt file
def load_donors():
    donors_list = []
    with open('list.txt', 'r') as file:
        donors_list = file.read().splitlines()
    return donors_list

# Function to display the main menu
def display_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=1)
    item_donate = types.KeyboardButton("I Want to Donate")
    item_find_donor = types.KeyboardButton("Donor Finder")
    item_profile = types.KeyboardButton("My Profile")
    markup.add(item_donate, item_find_donor, item_profile)
    bot.send_message(chat_id, "Welcome to Blood Donor Finder Bot!", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    display_main_menu(message.chat.id)

# A dictionary to store user information during blood group selection
user_selection_data = {}

# Add a handler for the "I Want to Donate" option
@bot.message_handler(func=lambda message: message.text == "I Want to Donate")
def start_donate(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)

    # Create keyboard buttons for different blood groups
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    blood_buttons = [types.KeyboardButton(group) for group in blood_groups]
    markup.add(*blood_buttons)

    msg = bot.send_message(chat_id, "Select your blood group:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_blood_group_selection)

def process_blood_group_selection(message):
    chat_id = message.chat.id
    selected_blood_group = message.text

    # Store the selected blood group in the dictionary
    user_selection_data[chat_id] = {'blood_group': selected_blood_group}

    msg = bot.send_message(chat_id, "Enter your name:")
    bot.register_next_step_handler(msg, process_name_for_donation)

def process_name_for_donation(message):
    chat_id = message.chat.id
    name = message.text
    user_selection_data[chat_id]['name'] = name

    msg = bot.send_message(chat_id, "Enter your location:")
    bot.register_next_step_handler(msg, process_location_for_donation)

def process_location_for_donation(message):
    chat_id = message.chat.id
    location_text = message.text  # User enters location as text
    user_selection_data[chat_id]['location'] = location_text

    msg = bot.send_message(chat_id, "Enter your mobile number:")
    bot.register_next_step_handler(msg, process_mobile_number_for_donation)

def process_mobile_number_for_donation(message):
    chat_id = message.chat.id
    mobile_number = message.text
    user_selection_data[chat_id]['mobile_number'] = mobile_number
    # Save user data to the list.txt file
    blood_group = user_selection_data[chat_id]['blood_group']
    name = user_selection_data[chat_id]['name']
    location = user_selection_data[chat_id]['location']
    mobile_number = user_selection_data[chat_id]['mobile_number']

    user_data = f"{name},{blood_group},{location},{mobile_number}"
    save_to_list(user_data)

    bot.send_message(chat_id, "Thank you for registering as a donor!")
    display_main_menu(chat_id)



@bot.message_handler(func=lambda message: message.text == "My Profile")
def profile(message):
    chat_id = message.chat.id
    if chat_id in donors:
        donor_info = donors[chat_id]
        profile_text = f"Name: {donor_info.get('name', 'N/A')}\nBlood Type: {donor_info.get('blood_type', 'N/A')}\nLocation: {donor_info.get('location', 'N/A')}\nMobile Number: {donor_info.get('mobile_number', 'N/A')}"
        bot.send_message(chat_id, profile_text)
    else:
        bot.send_message(chat_id, "You haven't registered as a donor yet.")

@bot.message_handler(func=lambda message: message.text == "Donor Finder")
def start_donor_finder(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(row_width=2)
    back_button = types.KeyboardButton("Back")
    markup.add(back_button)
    # Create keyboard buttons for different blood groups
    blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    blood_buttons = [types.KeyboardButton(group) for group in blood_groups]
    markup.add(*blood_buttons)
    msg = bot.send_message(chat_id, "Enter blood type to search for:", reply_markup=markup)
    bot.register_next_step_handler(msg, process_blood_type_for_finder)

def process_blood_type_for_finder(message):
    chat_id = message.chat.id
    blood_type = message.text
    user_selection_data[chat_id] = {'blood_type': blood_type}
    msg = bot.send_message(chat_id, "Enter location to search for:")
    bot.register_next_step_handler(msg, process_location_for_finder)

def process_location_for_finder(message):
    chat_id = message.chat.id
    location = message.location
    user_selection_data[chat_id]['latitude'] = location.latitude
    user_selection_data[chat_id]['longitude'] = location.longitude
    display_matching_donors(chat_id)
    
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of the Earth in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance


def display_matching_donors(chat_id, max_distance=10.0):
    donors_list = load_donors()
    user_info = user_selection_data[chat_id]
    
    # Check if user's location data exists
    if 'latitude' not in user_info or 'longitude' not in user_info:
        bot.send_message(chat_id, "Your location data is missing.")
        display_main_menu(chat_id)
        return
    
    user_latitude = user_info['latitude']
    user_longitude = user_info['longitude']
    
    matching_donors = []
    for donor in donors_list:
        donor_info = donor.split(',')
        if len(donor_info) >= 4:  # Ensure enough data exists
            donor_latitude = float(donor_info[2])
            donor_longitude = float(donor_info[3])
            distance = haversine_distance(user_latitude, user_longitude, donor_latitude, donor_longitude)
            
            if distance <= max_distance:
                matching_donors.append(donor)
    
    if matching_donors:
        markup = types.ReplyKeyboardMarkup(row_width=1)
        donor_buttons = [types.KeyboardButton(f"{donor.split(',')[0]} ({donor.split(',')[1]})") for donor in matching_donors]
        markup.add(*donor_buttons)
        msg = bot.send_message(chat_id, "Select a donor:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_selected_donor)
    else:
        response = "No matching donors found."
        bot.send_message(chat_id, response)
        display_main_menu(chat_id)
        
def process_selected_donor(message):
    chat_id = message.chat.id
    selected_donor = message.text.split('(')[0].strip()
    matching_donor = [donor for donor in load_donors() if selected_donor in donor]
    if matching_donor:
        donor_info = matching_donor[0].split(',')
        donor_name, donor_blood_type, donor_location, donor_mobile_number = donor_info
        response = f"Donor: {donor_name}\nBlood Type: {donor_blood_type}\nLocation: {donor_location}\nMobile Number: {donor_mobile_number}"
    else:
        response = "Selected donor not found."
    bot.send_message(chat_id, response)
    display_main_menu(chat_id)

while True:
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"An error occurred: {e}")
        # Add any additional logging or error handling here

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
