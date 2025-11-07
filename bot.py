import json
import os
import secrets
import string
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from flask import Flask, request

app = Flask(__name__)

BOT_TOKEN = "8289354732:AAFWkTDFPWi7ef8Z1doenceorlD988AtL_c"
SUPPORT_USERNAME = "@SunsetUsdt"
ADMIN_USERNAME = "@SunsetUsdt"
REFERRAL_BONUS = 0.1
MAIN_IMAGE_PATH = "me1.jpg"

ADDING_TON, ADDING_CARD, DEAL_AMOUNT, DEAL_DESCRIPTION, ADMIN_TAKE_DEAL, ADMIN_COMPLETE_DEAL, ADD_SUCCESSFUL_DEALS = range(7)

DATA_FILE = "bot_data.json"

class Database:
    def __init__(self):
        self.data = self._load_data()
    
    def _load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "users": {},
            "deals": {},
            "admins": []
        }
    
    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
    
    def get_user(self, user_id: int):
        return self.data["users"].get(str(user_id), {})
    
    def save_user(self, user_id: int, user_data: dict):
        self.data["users"][str(user_id)] = user_data
        self.save_data()
    
    def create_deal(self, deal_id: str, deal_data: dict):
        self.data["deals"][deal_id] = deal_data
        self.save_data()
    
    def get_deal(self, deal_id: str):
        return self.data["deals"].get(deal_id, {})
    
    def update_deal(self, deal_id: str, updates: dict):
        if deal_id in self.data["deals"]:
            self.data["deals"][deal_id].update(updates)
            self.save_data()
    
    def get_all_deals(self):
        return self.data["deals"]
    
    def delete_deal(self, deal_id: str):
        if deal_id in self.data["deals"]:
            del self.data["deals"][deal_id]
            self.save_data()
    
    def is_admin(self, user_id: int):
        return str(user_id) in self.data["admins"]
    
    def add_admin(self, user_id: int):
        if str(user_id) not in self.data["admins"]:
            self.data["admins"].append(str(user_id))
            self.save_data()

db = Database()

TEXTS = {
    'ru': {
        'welcome': """Добро пожаловать в ELF OTC – надежный P2P-гарант

- Покупайте и продавайте всё, что угодно – безопасно!  
От Telegram-подарков и NFT до токенов и фиата – сделки проходят легко и без риска.

- Удобное управление кошельками  
- Реферальная система  
- Безопасные сделки с гарантией  

Выберите нужный раздел ниже:""",
        'my_deals': "📋 Мои сделки",
        'manage_details': "💼 Управление реквизитами",
        'create_deal': "💰 Создать сделку",
        'referral_link': "👥 Реферальная ссылка",
        'change_language': "🌐 Сменить язык",
        'support': "🆘 Поддержка",
        'no_active_deals': "📭 У вас пока нет активных сделок.",
        'choose_action': "Выберите действие:",
        'add_ton_wallet': "➕ Добавить TON кошелек",
        'add_card': "➕ Добавить карту",
        'view_details': "👀 Просмотреть реквизиты",
        'back': "🔙 Назад",
        'receive_card': "💳 Получить на карту",
        'receive_ton': "👛 Получить на TON кошелек",
        'choose_payment_method': "Выберите способ получения средств:",
        'no_details': "❌ Сначала добавьте реквизиты!",
        'no_card': "❌ Сначала добавьте карту!",
        'no_ton': "❌ Сначала добавьте TON кошелек!",
        'active_deal_exists': "❌ У вас уже есть активная сделка! Завершите ее перед созданием новой.",
        'enter_ton_wallet': "Введите ваш TON кошелек:",
        'enter_card': "Введите номер вашей карты:",
        'ton_added': "✅ TON кошелек добавлен!",
        'card_added': "✅ Карта добавлена!",
        'enter_deal_amount': "Введите сумму сделки:",
        'enter_deal_description': "Укажите, что вы предалагаете в этой сделке: \n Пример: 10 кепок и пепе",
        'deal_created': """✅ Сделка создана!

ID сделки: #{deal_id}
Сумма: {amount}
Способ получения: {payment_method}
Описание: {description}

Ссылка для второго участника:
{deal_link}

Поделитесь этой ссылкой со вторым участником.""",
        'referral_info': """Ваша реферальная ссылка:

{ref_link}

Количество рефералов: {ref_count}  
Заработано с рефералов: {ref_earned} TON""",
        'choose_language': "Выберите язык:",
        'language_changed': "Язык изменен на русский!",
        'support_text': """🆘 Поддержка

По всем вопросам обращайтесь к нашему специалисту:""",
        'contact_support': "📞 Написать в поддержку",
        'delete_deal': "❌ Удалить сделку",
        'exit_deal': "🚪 Выйти из сделки",
        'confirm_delete': "❓ Вы уверены, что хотите удалить сделку #{deal_id}?",
        'confirm_exit': "❓ Вы уверены, что хотите выйти из сделку #{deal_id}?",
        'yes_delete': "✅ Да, удалить",
        'no_delete': "❌ Нет, оставить",
        'yes_exit': "✅ Да, выйти",
        'no_exit': "❌ Нет, остаться",
        'deal_deleted': "✅ Сделка удалена!",
        'delete_cancelled': "✅ Удаление отменено.",
        'exited_deal': "✅ Вы вышли из сделки!",
        'exit_cancelled': "✅ Вы остались в сделке.",
        'deal_not_found': "❌ Сделка не найдена!",
        'no_rights': "❌ Сделка не найдена или у вас нет прав!",
        'admin_taken': "❌ Нельзя удалить сделку, которую уже взял админ!",
        'admin_view_deals': "📋 Просмотреть сделки",
        'admin_take_deal': "✅ Взять сделку",
        'admin_complete_deal': "🏁 Завершить сделку",
        'admin_add_successful_deals': "➕ Добавить успешные сделки",
        'no_active_deals_admin': "📭 Нет активных сделок",
        'enter_deal_id_take': "Введите ID сделки которую хотите взять:",
        'enter_deal_id_complete': "Введите ID сделки для завершения:",
        'deal_taken': "✅ Вы взяли сделку #{deal_id}. Свяжитесь с участниками в ЛС",
        'deal_completed': "✅ Сделка #{deal_id} завершена и удалена из системы!",
        'deal_not_found_admin': "❌ Сделка не найдена!",
        'you_are_admin': "✅ Вы теперь админ!",
        'cancel': "Отменено",
        'details_not_added': "Реквизиты не добавлены",
        'ton_wallet': "TON кошелек: {wallet}",
        'card': "Карта: {card}",
        'buyer_deal_info': """Информация о сделке #{deal_id}

Вы покупатель в сделке.
✔ Продавец: @{seller_username} ({seller_id})
• Успешные сделки: {successful_deals}

• Вы покупаете: {description}

📌 Адрес для оплаты:
{ton_wallet}

📌 Сумма к оплате: {amount} TON
✅ Комментарий к платежу (мемо):
{deal_id}

🔍 Пожалуйста, убедитесь в правильности данных перед оплатой. Комментарий (мемо) обязателен!

В случае если вы отправили транзакцию без комментария заполните форму — @OtcElfSup""",
        'open_tonkeeper': "👛 Открыть Tonkeeper",
        'confirm_payment': "✅ Подтвердить оплату",
        'payment_confirmed_seller': """💸 Покупатель совершил оплату!

Сделка #{deal_id}
Покупатель: @{buyer_username}
Сумма: {amount} TON

📦 Отправьте подарок админу: {admin_username}""",
        'payment_confirmed_buyer': """✅ Оплата подтверждена!

Ожидайте подтверждения получения от продавца.""",
        'wait_admin_contact': """⏳ Ожидайте подключения администратора

Админ свяжется с вами для подтверждения сделки.""",
        'waiting_for_admin': "⏳ Ожидайте подключения администратора для подтверждения оплаты",
        'only_admin_can_confirm': "❌ Подтвердить оплату может только администратор сделки",
        'enter_successful_deals': "Введите количество успешных сделок для добавления:",
        'successful_deals_added': "✅ Количество успешных сделок обновлено!",
        'admin_contact_info': "🛡️ Администратор сделки: {admin_username} - обратитесь к нему после получения уведомления об успешной оплате",
    },
    'en': {
        'welcome': """Welcome to ELF OTC – reliable P2P guarantee

- Buy and sell anything – safely!  
From Telegram gifts and NFTs to tokens and fiat – transactions go smoothly and risk-free.

- Convenient wallet management  
- Referral system  
- Secure guaranteed deals  

Choose the desired section below:""",
        'my_deals': "📋 My Deals",
        'manage_details': "💼 Manage Details",
        'create_deal': "💰 Create Deal",
        'referral_link': "👥 Referral Link",
        'change_language': "🌐 Change Language",
        'support': "🆘 Support",
        'no_active_deals': "📭 You have no active deals yet.",
        'choose_action': "Choose action:",
        'add_ton_wallet': "➕ Add TON Wallet",
        'add_card': "➕ Add Card",
        'view_details': "👀 View Details",
        'back': "🔙 Back",
        'receive_card': "💳 Receive to Card",
        'receive_ton': "👛 Receive to TON Wallet",
        'choose_payment_method': "Choose payment method:",
        'no_details': "❌ Please add payment details first!",
        'no_card': "❌ Please add a card first!",
        'no_ton': "❌ Please add TON wallet first!",
        'active_deal_exists': "❌ You already have an active deal! Complete it before creating a new one.",
        'enter_ton_wallet': "Enter your TON wallet:",
        'enter_card': "Enter your card number:",
        'ton_added': "✅ TON wallet added!",
        'card_added': "✅ Card added!",
        'enter_deal_amount': "Enter deal amount:",
        'enter_deal_description': "Describe what the deal is for (product/service):",
        'deal_created': """✅ Deal created!

Deal ID: #{deal_id}
Amount: {amount}
Payment method: {payment_method}
Description: {description}

Link for the second participant:
{deal_link}

Share this link with the second participant.""",
        'referral_info': """Your referral link:

{ref_link}

Referrals count: {ref_count}  
Earned from referrals: {ref_earned} TON""",
        'choose_language': "Choose language:",
        'language_changed': "Language changed to English!",
        'support_text': """🆘 Support

For any questions, contact our specialist:""",
        'contact_support': "📞 Contact Support",
        'delete_deal': "❌ Delete Deal",
        'exit_deal': "🚪 Exit Deal",
        'confirm_delete': "❓ Are you sure you want to delete deal #{deal_id}?",
        'confirm_exit': "❓ Are you sure you want to exit deal #{deal_id}?",
        'yes_delete': "✅ Yes, delete",
        'no_delete': "❌ No, keep",
        'yes_exit': "✅ Yes, exit",
        'no_exit': "❌ No, stay",
        'deal_deleted': "✅ Deal deleted!",
        'delete_cancelled': "✅ Deletion cancelled.",
        'exited_deal': "✅ You exited the deal!",
        'exit_cancelled': "✅ You stayed in the deal.",
        'deal_not_found': "❌ Deal not found!",
        'no_rights': "❌ Deal not found or you don't have rights!",
        'admin_taken': "❌ Cannot delete a deal that has been taken by an admin!",
        'admin_view_deals': "📋 View Deals",
        'admin_take_deal': "✅ Take Deal",
        'admin_complete_deal': "🏁 Complete Deal",
        'admin_add_successful_deals': "➕ Add Successful Deals",
        'no_active_deals_admin': "📭 No active deals",
        'enter_deal_id_take': "Enter the deal ID you want to take:",
        'enter_deal_id_complete': "Enter the deal ID to complete:",
        'deal_taken': "✅ You took deal #{deal_id}. Contact participants in DM",
        'deal_completed': "✅ Deal #{deal_id} completed and removed from the system!",
        'deal_not_found_admin': "❌ Deal not found!",
        'you_are_admin': "✅ You are now an admin!",
        'cancel': "Cancelled",
        'details_not_added': "Payment details not added",
        'ton_wallet': "TON wallet: {wallet}",
        'card': "Card: {card}",
        'buyer_deal_info': """Deal Information #{deal_id}

You are the buyer in the deal.
✔ Seller: @{seller_username} ({seller_id})
• Successful deals: {successful_deals}

• You are buying: {description}

📌 Payment address:
{ton_wallet}

📌 Amount to pay: {amount} TON
✅ Payment comment (memo):
{deal_id}

🔍 Please verify the data before payment. Comment (memo) is mandatory!

If you sent a transaction without a comment, fill out the form — @OtcElfSup""",
        'open_tonkeeper': "👛 Open Tonkeeper",
        'confirm_payment': "✅ Confirm Payment",
        'payment_confirmed_seller': """💸 Buyer confirmed payment!

Deal #{deal_id}
Buyer: @{buyer_username}
Amount: {amount} TON

📦 Send the gift to admin: {admin_username}""",
        'payment_confirmed_buyer': """✅ Payment confirmed!

Wait for seller's receipt confirmation.""",
        'wait_admin_contact': """⏳ Wait for administrator connection

Admin will contact you to confirm the deal.""",
        'waiting_for_admin': "⏳ Wait for administrator connection to confirm payment",
        'only_admin_can_confirm': "❌ Only the deal administrator can confirm payment",
        'enter_successful_deals': "Enter the number of successful deals to add:",
        'successful_deals_added': "✅ Successful deals count updated!",
        'admin_contact_info': "🛡️ Deal administrator: {admin_username} - contact them to confirm payment",
    }
}

def get_text(user_data, key, **kwargs):
    language = user_data.get('language', 'ru')
    text = TEXTS[language].get(key, key)
    return text.format(**kwargs) if kwargs else text

def get_main_keyboard(user_data):
    language = user_data.get('language', 'ru')
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'my_deals'), callback_data="my_deals")],
        [InlineKeyboardButton(get_text(user_data, 'manage_details'), callback_data="manage_details")],
        [InlineKeyboardButton(get_text(user_data, 'create_deal'), callback_data="create_deal")],
        [InlineKeyboardButton(get_text(user_data, 'referral_link'), callback_data="referral_link")],
        [InlineKeyboardButton(get_text(user_data, 'change_language'), callback_data="change_language")],
        [InlineKeyboardButton(get_text(user_data, 'support'), callback_data="support")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_details_keyboard(user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'add_ton_wallet'), callback_data="add_ton")],
        [InlineKeyboardButton(get_text(user_data, 'add_card'), callback_data="add_card")],
        [InlineKeyboardButton(get_text(user_data, 'view_details'), callback_data="view_details")],
        [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_payment_method_keyboard(user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'receive_card'), callback_data="receive_card")],
        [InlineKeyboardButton(get_text(user_data, 'receive_ton'), callback_data="receive_ton")],
        [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_deal_actions_keyboard(deal_id, user_data, user_role="creator"):
    if user_role == "creator":
        keyboard = [
            [InlineKeyboardButton(get_text(user_data, 'delete_deal'), callback_data=f"confirm_delete_{deal_id}")],
            [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="my_deals")]
        ]
    else:  
        keyboard = [
            [InlineKeyboardButton(get_text(user_data, 'exit_deal'), callback_data=f"confirm_exit_{deal_id}")],
            [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="my_deals")]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_confirm_delete_keyboard(deal_id, user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'yes_delete'), callback_data=f"delete_deal_{deal_id}")],
        [InlineKeyboardButton(get_text(user_data, 'no_delete'), callback_data=f"keep_deal_{deal_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirm_exit_keyboard(deal_id, user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'yes_exit'), callback_data=f"exit_deal_{deal_id}")],
        [InlineKeyboardButton(get_text(user_data, 'no_exit'), callback_data=f"stay_deal_{deal_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_language_keyboard(user_data):
    keyboard = [
        [InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")],
        [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
        [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_keyboard(user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'admin_view_deals'), callback_data="admin_view_deals")],
        [InlineKeyboardButton(get_text(user_data, 'admin_take_deal'), callback_data="admin_take_deal")],
        [InlineKeyboardButton(get_text(user_data, 'admin_complete_deal'), callback_data="admin_complete_deal")],
        [InlineKeyboardButton(get_text(user_data, 'admin_add_successful_deals'), callback_data="admin_add_successful_deals")],
        [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_my_deals_keyboard(user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_support_keyboard(user_data):
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'contact_support'), url=f"https://t.me/{SUPPORT_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_buyer_deal_keyboard(deal_id, ton_wallet, amount, user_data, deal_status='waiting_admin'):
    tonkeeper_url = f"https://tonkeeper.com/"
    
    keyboard = [
        [InlineKeyboardButton(get_text(user_data, 'open_tonkeeper'), url=tonkeeper_url)],
    ]
    
    if deal_status == 'in_progress':
        keyboard.append([InlineKeyboardButton(get_text(user_data, 'confirm_payment'), callback_data=f"confirm_payment_{deal_id}")])
    
    keyboard.append([InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def generate_deal_id():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

def generate_ref_code(user_id: int):
    return f"ref_{user_id}_{secrets.token_hex(4)}"

def format_user_details(user_data: dict):
    details = []
    if user_data.get('ton_wallet'):
        details.append(get_text(user_data, 'ton_wallet', wallet=user_data['ton_wallet']))
    if user_data.get('card'):
        details.append(get_text(user_data, 'card', card=user_data['card']))
    if not details:
        return get_text(user_data, 'details_not_added')
    
    return "\n".join(details)

def get_user_deals(user_id):
    deals = db.get_all_deals()
    user_deals = []
    
    for deal_id, deal in deals.items():
        if deal.get('user1_id') == user_id or deal.get('user2_id') == user_id:
            user_deals.append((deal_id, deal))
    
    return user_deals

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user_id = update.message.from_user.id
        message = update.message
    else:
        user_id = update.callback_query.from_user.id
        message = update.callback_query.message
        
    user_data = db.get_user(user_id)
    
    if update.message and context.args:
        if context.args[0].startswith('ref_'):
            ref_code = context.args[0]
            try:
                referrer_id = int(ref_code.split('_')[1])
                if not user_data:
                    referrer_data = db.get_user(referrer_id)
                    if referrer_data:
                        referrer_data['ref_count'] = referrer_data.get('ref_count', 0) + 1
                        referrer_data['ref_earned'] = referrer_data.get('ref_earned', 0) + REFERRAL_BONUS
                        db.save_user(referrer_id, referrer_data)
            except:
                pass
        
        elif context.args[0].startswith('deal_'):
            deal_id = context.args[0].replace('deal_', '')
            deal = db.get_deal(deal_id)
            if deal and deal.get('status') == 'active':
                
                if deal.get('user1_id') == user_id:
                    await message.reply_text("❌ Вы уже создатель этой сделки!", reply_markup=get_main_keyboard(user_data))
                    return
                
                if deal.get('user2_id'):
                    await message.reply_text("❌ В этой сделке уже есть второй участник!", reply_markup=get_main_keyboard(user_data))
                    return
                
                seller_id = deal.get('user1_id')
                seller_data = db.get_user(seller_id) if seller_id else {}
                seller_username = deal.get('user1_username', 'Unknown')
                successful_deals = seller_data.get('successful_deals', 0)
                
                seller_ton_wallet = seller_data.get('ton_wallet', '')
                if not seller_ton_wallet:
                    await message.reply_text("❌ У продавца не настроен TON кошелек!", reply_markup=get_main_keyboard(user_data))
                    return
                
                deal['user2_id'] = user_id
                deal['user2_username'] = update.effective_user.username
                deal['status'] = 'waiting_admin'  
                db.update_deal(deal_id, deal)
                
                buyer_text = get_text(user_data, 'buyer_deal_info',
                                    deal_id=deal_id,
                                    seller_username=seller_username,
                                    seller_id=seller_id,
                                    successful_deals=successful_deals,
                                    description=deal.get('description', ''),
                                    ton_wallet=seller_ton_wallet,
                                    amount=deal.get('amount', ''))
                
                if seller_id:
                    buyer_info = db.get_user(user_id)
                    buyer_successful_deals = buyer_info.get('successful_deals', 0)
    
                    await context.bot.send_message(
                        seller_id, 
f"""✅ К вашей сделке присоединился покупатель!

👤 Покупатель: @{update.effective_user.username}
📊 Успешных сделок: {buyer_successful_deals}
💰 Сделка #{deal_id}
💵 Сумма: {deal.get('amount', 'N/A')} TON

Ожидайте подключения администратора."""
    )
                
                await message.reply_text(
                    buyer_text + f"\n\n{get_text(user_data, 'waiting_for_admin')}", 
                    reply_markup=get_buyer_deal_keyboard(deal_id, seller_ton_wallet, deal.get('amount', ''), user_data, 'waiting_admin')
                )
                return
    
    if not user_data:
        user_data = {
            'language': 'ru',
            'ton_wallet': None,
            'card': None,
            'ref_code': generate_ref_code(user_id),
            'ref_count': 0,
            'ref_earned': 0.0,
            'username': update.effective_user.username,
            'successful_deals': 0
        }
        db.save_user(user_id, user_data)
    
    welcome_text = get_text(user_data, 'welcome')
    
    if os.path.exists(MAIN_IMAGE_PATH):
        if update.message:
            await update.message.reply_photo(
                photo=open(MAIN_IMAGE_PATH, 'rb'),
                caption=welcome_text,
                reply_markup=get_main_keyboard(user_data)
            )
        else:
            await update.callback_query.message.delete()
            await update.callback_query.message.reply_photo(
                photo=open(MAIN_IMAGE_PATH, 'rb'),
                caption=welcome_text,
                reply_markup=get_main_keyboard(user_data)
            )
    else:
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard(user_data))
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=get_main_keyboard(user_data))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    callback_data = query.data
    
    if callback_data == "back_to_main":
        await start(update, context)
        return ConversationHandler.END
    
    elif callback_data == "my_deals":
        user_deals = get_user_deals(user_id)
        
        if not user_deals:
            await query.message.delete()
            await query.message.reply_text(get_text(user_data, 'no_active_deals'), reply_markup=get_my_deals_keyboard(user_data))
            return
        
        text = "📋 Ваши сделки:\n\n" if user_data.get('language', 'ru') == 'ru' else "📋 Your deals:\n\n"
        for deal_id, deal in user_deals:
            role = "👤 Создатель" if deal.get('user1_id') == user_id else "👥 Участник"
            status = deal.get('status', 'active')
            status_text = {
                'active': '🟢 Активна',
                'waiting_admin': '🟡 Ожидает админа', 
                'in_progress': '🔵 В работе у админа',
                'completed': '🟣 Завершена'
            }.get(status, status)
            
            text += f"""🔹 Сделка #{deal_id}
{role}
💵 Сумма: {deal.get('amount', 'N/A')}
📝 Описание: {deal.get('description', 'N/A')}
📊 Статус: {status_text}
"""
            
            if status == 'in_progress' and deal.get('admin_username'):
                text += f"🛡️ Админ: {deal.get('admin_username')}\n"
            
            text += "------------------------\n"
        
        keyboard = []
        for deal_id, deal in user_deals:
            if deal.get('status') in ['active', 'waiting_admin', 'in_progress']:
                if deal.get('user1_id') == user_id:
                    keyboard.append([InlineKeyboardButton(f"❌ {get_text(user_data, 'delete_deal')} #{deal_id}", callback_data=f"confirm_delete_{deal_id}")])
                else:
                    keyboard.append([InlineKeyboardButton(f"🚪 {get_text(user_data, 'exit_deal')} #{deal_id}", callback_data=f"confirm_exit_{deal_id}")])
        
        keyboard.append([InlineKeyboardButton(get_text(user_data, 'back'), callback_data="back_to_main")])
        
        await query.message.delete()
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif callback_data == "manage_details":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'choose_action'), reply_markup=get_details_keyboard(user_data))
    
    elif callback_data == "create_deal":
        if not user_data.get('ton_wallet') and not user_data.get('card'):
            await query.message.delete()
            await query.message.reply_text(get_text(user_data, 'no_details'), reply_markup=get_details_keyboard(user_data))
            return
        
        user_deals = get_user_deals(user_id)
        active_deals = [deal for deal_id, deal in user_deals if deal.get('status') in ['active', 'waiting_admin', 'in_progress']]
        if active_deals:
            await query.message.delete()
            await query.message.reply_text(get_text(user_data, 'active_deal_exists'), reply_markup=get_main_keyboard(user_data))
            return
        
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'choose_payment_method'), reply_markup=get_payment_method_keyboard(user_data))
    
    elif callback_data == "referral_link":
        ref_link = f"https://t.me/{(await context.bot.get_me()).username}?start={user_data['ref_code']}"
        text = get_text(user_data, 'referral_info', 
                       ref_link=ref_link,
                       ref_count=user_data.get('ref_count', 0),
                       ref_earned=user_data.get('ref_earned', 0))
        
        await query.message.delete()
        await query.message.reply_text(text, reply_markup=get_main_keyboard(user_data))
    
    elif callback_data == "change_language":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'choose_language'), reply_markup=get_language_keyboard(user_data))
    
    elif callback_data == "support":
        support_text = get_text(user_data, 'support_text')
        await query.message.delete()
        await query.message.reply_text(support_text, reply_markup=get_support_keyboard(user_data))
    
    elif callback_data == "add_ton":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'enter_ton_wallet'))
        context.user_data['action'] = 'adding_ton'
        return ADDING_TON
    
    elif callback_data == "add_card":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'enter_card'))
        context.user_data['action'] = 'adding_card'
        return ADDING_CARD
    
    elif callback_data == "view_details":
        details = format_user_details(user_data)
        await query.message.delete()
        await query.message.reply_text(details, reply_markup=get_details_keyboard(user_data))
    
    elif callback_data in ["receive_card", "receive_ton"]:
        if callback_data == "receive_card" and not user_data.get('card'):
            await query.message.delete()
            await query.message.reply_text(get_text(user_data, 'no_card'), reply_markup=get_details_keyboard(user_data))
            return
        elif callback_data == "receive_ton" and not user_data.get('ton_wallet'):
            await query.message.delete()
            await query.message.reply_text(get_text(user_data, 'no_ton'), reply_markup=get_details_keyboard(user_data))
            return
        
        context.user_data['deal_payment_method'] = 'card' if callback_data == "receive_card" else 'ton'
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'enter_deal_amount'))
        context.user_data['action'] = 'deal_amount'
        return DEAL_AMOUNT
    
    elif callback_data == "lang_ru":
        user_data['language'] = 'ru'
        db.save_user(user_id, user_data)
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'language_changed'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data == "lang_en":
        user_data['language'] = 'en'
        db.save_user(user_id, user_data)
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'language_changed'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data.startswith("confirm_delete_"):
        deal_id = callback_data.replace("confirm_delete_", "")
        deal = db.get_deal(deal_id)
        
        if not deal or deal.get('user1_id') != user_id:
            await query.answer(get_text(user_data, 'no_rights'), show_alert=True)
            return
        
        if deal.get('status') == 'in_progress':
            await query.answer(get_text(user_data, 'admin_taken'), show_alert=True)
            return
        
        await query.message.delete()
        await query.message.reply_text(
            get_text(user_data, 'confirm_delete', deal_id=deal_id),
            reply_markup=get_confirm_delete_keyboard(deal_id, user_data)
        )
    
    elif callback_data.startswith("delete_deal_"):
        deal_id = callback_data.replace("delete_deal_", "")
        deal = db.get_deal(deal_id)
        
        if not deal or deal.get('user1_id') != user_id:
            await query.answer(get_text(user_data, 'deal_not_found'), show_alert=True)
            return
        
        if deal.get('status') == 'in_progress':
            await query.answer(get_text(user_data, 'admin_taken'), show_alert=True)
            return
        
        user2_id = deal.get('user2_id')
        if user2_id:
            await context.bot.send_message(user2_id, f"❌ Создатель удалил сделку #{deal_id}")
        
        admin_id = deal.get('admin')
        if admin_id:
            await context.bot.send_message(admin_id, f"❌ Сделка #{deal_id} удалена создателем")
        
        db.delete_deal(deal_id)
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'deal_deleted'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data.startswith("keep_deal_"):
        deal_id = callback_data.replace("keep_deal_", "")
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'delete_cancelled'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data.startswith("confirm_exit_"):
        deal_id = callback_data.replace("confirm_exit_", "")
        deal = db.get_deal(deal_id)
        
        if not deal or deal.get('user2_id') != user_id:
            await query.answer(get_text(user_data, 'deal_not_found'), show_alert=True)
            return
        
        if deal.get('status') == 'in_progress':
            await query.answer(get_text(user_data, 'admin_taken'), show_alert=True)
            return
        
        await query.message.delete()
        await query.message.reply_text(
            get_text(user_data, 'confirm_exit', deal_id=deal_id),
            reply_markup=get_confirm_exit_keyboard(deal_id, user_data)
        )
    
    elif callback_data.startswith("exit_deal_"):
        deal_id = callback_data.replace("exit_deal_", "")
        deal = db.get_deal(deal_id)
        
        if not deal or deal.get('user2_id') != user_id:
            await query.answer(get_text(user_data, 'deal_not_found'), show_alert=True)
            return
        
        user1_id = deal.get('user1_id')
        if user1_id:
            await context.bot.send_message(
                user1_id, 
                f"❌ Второй участник @{query.from_user.username} покинул сделку #{deal_id}. Сделка снова активна."
            )
        
        db.update_deal(deal_id, {
            'user2_id': None,
            'user2_username': None,
            'status': 'active'
        })
        
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'exited_deal'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data.startswith("stay_deal_"):
        deal_id = callback_data.replace("stay_deal_", "")
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'exit_cancelled'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data.startswith("confirm_payment_"):
        deal_id = callback_data.replace("confirm_payment_", "")
        deal = db.get_deal(deal_id)
        
        if not deal or deal.get('user2_id') != user_id:
            await query.answer(get_text(user_data, 'deal_not_found'), show_alert=True)
            return
        
        if deal.get('status') != 'in_progress':
            await query.answer(get_text(user_data, 'waiting_for_admin'), show_alert=True)
            return
        
        db.update_deal(deal_id, {
            'status': 'payment_confirmed',
            'payment_confirmed': True
        })
        
        seller_id = deal.get('user1_id')
        if seller_id:
            seller_data = db.get_user(seller_id)
            
            seller_text = get_text(seller_data, 'payment_confirmed_seller',
                                 deal_id=deal_id,
                                 buyer_username=query.from_user.username,
                                 amount=deal.get('amount', ''),
                                 admin_username=deal.get('admin_username', ADMIN_USERNAME))
            
            await context.bot.send_message(seller_id, seller_text)
        
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'payment_confirmed_buyer'), reply_markup=get_main_keyboard(user_data))
    
    elif callback_data == "admin_view_deals":
        deals = db.get_all_deals()
        if not deals:
            await query.message.delete()
            await query.message.reply_text(get_text(user_data, 'no_active_deals_admin'), reply_markup=get_admin_keyboard(user_data))
        else:
            text = "📋 Активные сделки:\n\n" if user_data.get('language', 'ru') == 'ru' else "📋 Active deals:\n\n"
            for deal_id, deal in deals.items():
                status = deal.get('status', 'active')
                admin = deal.get('admin_username', 'Не назначен')
                user2 = deal.get('user2_username', 'Ожидает участника')
                text += f"""🔹 Сделка #{deal_id}
💵 Сумма: {deal.get('amount', 'N/A')}
📝 Описание: {deal.get('description', 'N/A')}
👤 Создатель: @{deal.get('user1_username', 'N/A')}
👥 Участник: @{user2}
🛡️ Админ: {admin}
📊 Статус: {status}
------------------------
"""
            await query.message.delete()
            await query.message.reply_text(text, reply_markup=get_admin_keyboard(user_data))
    
    elif callback_data == "admin_take_deal":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'enter_deal_id_take'))
        context.user_data['action'] = 'admin_take_deal'
        return ADMIN_TAKE_DEAL
    
    elif callback_data == "admin_complete_deal":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'enter_deal_id_complete'))
        context.user_data['action'] = 'admin_complete_deal'
        return ADMIN_COMPLETE_DEAL
    
    elif callback_data == "admin_add_successful_deals":
        await query.message.delete()
        await query.message.reply_text(get_text(user_data, 'enter_successful_deals'))
        context.user_data['action'] = 'add_successful_deals'
        return ADD_SUCCESSFUL_DEALS

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    user_data = db.get_user(user_id)
    
    action = context.user_data.get('action')
    
    if action == 'adding_ton':
        user_data['ton_wallet'] = text
        db.save_user(user_id, user_data)
        
        await update.message.reply_text(get_text(user_data, 'ton_added'), reply_markup=get_main_keyboard(user_data))
        context.user_data.clear()
        return ConversationHandler.END
    
    elif action == 'adding_card':
        user_data['card'] = text
        db.save_user(user_id, user_data)
        
        await update.message.reply_text(get_text(user_data, 'card_added'), reply_markup=get_main_keyboard(user_data))
        context.user_data.clear()
        return ConversationHandler.END
    
    elif action == 'deal_amount':
        context.user_data['deal_amount'] = text
        
        await update.message.reply_text(get_text(user_data, 'enter_deal_description'))
        context.user_data['action'] = 'deal_description'
        return DEAL_DESCRIPTION
    
    elif action == 'deal_description':
        description = text
        
        deal_id = generate_deal_id()
        payment_method = context.user_data['deal_payment_method']
        deal_data = {
            'user1_id': user_id,
            'user1_username': update.message.from_user.username,
            'amount': context.user_data['deal_amount'],
            'description': description,
            'payment_method': payment_method,
            'status': 'active',
            'deal_link': f"https://t.me/{(await context.bot.get_me()).username}?start=deal_{deal_id}"
        }
        
        db.create_deal(deal_id, deal_data)
        
        context.user_data.clear()
        
        payment_method_text = 'Карта' if payment_method == 'card' else 'TON кошелек'
        if user_data.get('language') == 'en':
            payment_method_text = 'Card' if payment_method == 'card' else 'TON wallet'
        
        message_text = get_text(user_data, 'deal_created',
                              deal_id=deal_id,
                              amount=deal_data['amount'],
                              payment_method=payment_method_text,
                              description=description,
                              deal_link=deal_data['deal_link'])
        
        await update.message.reply_text(message_text, reply_markup=get_main_keyboard(user_data))
        return ConversationHandler.END
    
    elif action == 'admin_take_deal':
        deal_id = text
        deal = db.get_deal(deal_id)
        
        if deal:
            admin_username = update.message.from_user.username
            if not admin_username:
                admin_username = update.message.from_user.first_name
            
            db.update_deal(deal_id, {
                'admin': user_id,
                'admin_username': f"@{admin_username}" if admin_username else "Админ",
                'status': 'in_progress'
            })
            
            user1_id = deal.get('user1_id')
            user2_id = deal.get('user2_id')
            
            if user1_id:
                user1_data = db.get_user(user1_id)
                admin_contact_text = get_text(user1_data, 'admin_contact_info', admin_username=f"@{admin_username}")
                await context.bot.send_message(user1_id, admin_contact_text)
            
            if user2_id:
                user2_data = db.get_user(user2_id)
                admin_contact_text = get_text(user2_data, 'admin_contact_info', admin_username=f"@{admin_username}")
                
                seller_id = deal.get('user1_id')
                seller_data = db.get_user(seller_id) if seller_id else {}
                seller_ton_wallet = seller_data.get('ton_wallet', '')
                
                buyer_text = get_text(user2_data, 'buyer_deal_info',
                                    deal_id=deal_id,
                                    seller_username=deal.get('user1_username', 'Unknown'),
                                    seller_id=seller_id,
                                    successful_deals=seller_data.get('successful_deals', 0),
                                    description=deal.get('description', ''),
                                    ton_wallet=seller_ton_wallet,
                                    amount=deal.get('amount', ''))
                
                await context.bot.send_message(
                    user2_id, 
                    buyer_text + f"\n\n{admin_contact_text}", 
                    reply_markup=get_buyer_deal_keyboard(deal_id, seller_ton_wallet, deal.get('amount', ''), user2_data, 'in_progress')
                )
            
            await update.message.reply_text(
                get_text(user_data, 'deal_taken', deal_id=deal_id),
                reply_markup=get_admin_keyboard(user_data)
            )
        else:
            await update.message.reply_text(get_text(user_data, 'deal_not_found_admin'), reply_markup=get_admin_keyboard(user_data))
        
        context.user_data.clear()
        return ConversationHandler.END
    
    elif action == 'admin_complete_deal':
        deal_id = text
        deal = db.get_deal(deal_id)
        
        if deal:
            seller_id = deal.get('user1_id')
            if seller_id:
                seller_data = db.get_user(seller_id)
                seller_data['successful_deals'] = seller_data.get('successful_deals', 0) + 1
                db.save_user(seller_id, seller_data)
            
            user1_id = deal.get('user1_id')
            user2_id = deal.get('user2_id')
            
            if user1_id:
                await context.bot.send_message(user1_id, f"✅ Сделка #{deal_id} завершена!")
            
            if user2_id:
                await context.bot.send_message(user2_id, f"✅ Сделка #{deal_id} завершена!")
            
            db.delete_deal(deal_id)
            
            await update.message.reply_text(
                get_text(user_data, 'deal_completed', deal_id=deal_id),
                reply_markup=get_admin_keyboard(user_data)
            )
        else:
            await update.message.reply_text(get_text(user_data, 'deal_not_found_admin'), reply_markup=get_admin_keyboard(user_data))
        
        context.user_data.clear()
        return ConversationHandler.END
    
    elif action == 'add_successful_deals':
        try:
            successful_deals = int(text)
            user_data['successful_deals'] = user_data.get('successful_deals', 0) + successful_deals
            db.save_user(user_id, user_data)
            
            await update.message.reply_text(
                get_text(user_data, 'successful_deals_added'),
                reply_markup=get_admin_keyboard(user_data)
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Пожалуйста, введите число!",
                reply_markup=get_admin_keyboard(user_data)
            )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    await start(update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = db.get_user(user_id)
    
    await update.message.reply_text(get_text(user_data, 'cancel'), reply_markup=get_main_keyboard(user_data))
    context.user_data.clear()
    return ConversationHandler.END

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_data = db.get_user(user_id)
    
    db.add_admin(user_id)
    
    await update.message.reply_text(get_text(user_data, 'you_are_admin'), reply_markup=get_admin_keyboard(user_data))

# Создаем приложение бота
def create_bot_application():
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_callback, pattern="^(add_ton|add_card|receive_card|receive_ton|admin_take_deal|admin_complete_deal|admin_add_successful_deals)$")
        ],
        states={
            ADDING_TON: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            ADDING_CARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            DEAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            DEAL_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            ADMIN_TAKE_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            ADMIN_COMPLETE_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            ADD_SUCCESSFUL_DEALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(handle_callback, pattern="^back_to_main$")
        ],
    )
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("sunsetteam", admin_command))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    return application

# Создаем экземпляр бота
bot_application = create_bot_application()

def setup_webhook():
    """Синхронная функция для установки вебхука"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    if webhook_url.startswith("https://"):
        # Используем asyncio для асинхронного вызова
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot_application.bot.set_webhook(webhook_url))
            print(f"Webhook установлен: {webhook_url}")
        finally:
            loop.close()
    else:
        print("Не удалось установить webhook - неверный URL")

# Flask маршруты
@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Обработчик вебхуков от Telegram"""
    if request.headers.get('content-type') == 'application/json':
        try:
            # Получаем JSON данные
            json_data = request.get_json()
            if json_data:
                update = Update.de_json(json_data, bot_application.bot)
                bot_application.process_update(update)
        except Exception as e:
            print(f"Error processing webhook: {e}")
    return 'OK'

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Установка вебхука (вызовите этот URL один раз после деплоя)"""
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
    result = bot_application.bot.set_webhook(webhook_url)
    return f"Webhook set to: {webhook_url}<br>Result: {result}"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check для Render"""
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    
    # Устанавливаем вебхук
    setup_webhook()
    
    print(f"Бот запущен на порту {port}!")
    app.run(host='0.0.0.0', port=port)
