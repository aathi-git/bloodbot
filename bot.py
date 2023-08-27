import telebot
from telebot import types

# Replace 'YOUR_BOT_TOKEN' with your actual bot token obtained from BotFather on Telegram
bot = telebot.TeleBot('6502481073:AAFJbvGP7lz_XVHv5OdNatrEbab7WmmVAMM')

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
    location = message.text
    user_selection_data[chat_id]['location'] = location

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
    location = message.text
    user_selection_data[chat_id]['location'] = location
    display_matching_donors(chat_id)

def display_matching_donors(chat_id):
    donors_list = load_donors()
    donor_info = user_selection_data[chat_id]
    blood_type = donor_info['blood_type']
    location = donor_info['location']
    
    matching_donors = [
        donor for donor in donors_list if (
            donor.split(',')[1] == blood_type and 
            donor.split(',')[2] == location
        )
    ]
    
    if matching_donors:
        markup = types.ReplyKeyboardMarkup(row_width=1)
        donor_buttons = [types.KeyboardButton(f"{donor.split(',')[0]} ({donor.split(',')[1]})") for donor in matching_donors]
        markup.add(*donor_buttons)
        msg = bot.send_message(chat_id, "Select a donor:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_selected_donor)  # This line was missing in the provided code
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

