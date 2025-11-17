import telebot, random, json, os, threading, time
from telebot import types

TOKEN = "8301662833:AAGCNpUE-0A2MKgoCBd618vCtnwJbWGykKA"
bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"

# ================== ДАННЫЕ ==================
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except:
            data = {}
else:
    data = {}

if "users" not in data:
    data["users"] = {}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def get_user(uid, first_name=None):
    uid = str(uid)
    if uid not in data["users"]:
        data["users"][uid] = {
            "balance": 100,
            "click_power": 1,
            "click_level": 0,
            "passive_level": 0,
            "passive_income": 0,
            "game": None,
            "name": first_name or f"Игрок {uid}",
            "tutorial_done": False,
            "notify_passive": True
        }
    user = data["users"][uid]
    # defaults
    defaults = {"balance":100,"click_power":1,"click_level":0,
                "passive_level":0,"passive_income":0,"game":None,
                "name":first_name or f"Игрок {uid}",
                "tutorial_done":False,"notify_passive":True}
    for k,v in defaults.items():
        if k not in user: user[k]=v
    save_data()
    return user

# ================== ПАССИВНЫЙ ДОХОД ==================
PASSIVE_LEVELS = [
    {"income":10,"price":1000},
    {"income":100,"price":15000},
    {"income":1000,"price":150000},
    {"income":5000,"price":750000},
    {"income":20000,"price":2000000}
]

def passive_loop():
    while True:
        time.sleep(60)
        for uid, u in data["users"].items():
            inc = u.get("passive_income",0)
            if inc>0:
                u["balance"]+=inc
                if u.get("notify_passive",True):
                    try: bot.send_message(uid,f"💰 Пассивный доход: +{inc}. Баланс: {u['balance']}")
                    except: pass
        save_data()
threading.Thread(target=passive_loop,daemon=True).start()

# ================== КЛАВИАТУРЫ ==================
def main_kb(): kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("Заработать деньги","Играть","Магазин"); kb.add("Топ игроков","Настройки"); return kb
def earn_kb(): kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("Клик","Баланс"); kb.add("Назад"); return kb
def shop_kb(): kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("Прокачка клика","Пассивный доход"); kb.add("Назад"); return kb
def click_kb(u): kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add(f"Улучшить клик за {10000*(u['click_level']+1)}","Назад"); return kb
def passive_kb(u):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    l=u['passive_level']
    if l<len(PASSIVE_LEVELS):
        info=PASSIVE_LEVELS[l]
        kb.add(f"Купить {info['income']} в минуту за {info['price']}")
    kb.add("Назад")
    return kb
def diff_kb(): kb=types.ReplyKeyboardMarkup(resize_keyboard=True); kb.add("Легкий (1-10 ×1.5)","Средний (1-20 ×2)","Сложный (1-50 ×3)"); kb.add("Назад"); return kb
def number_kb(n): kb=types.ReplyKeyboardMarkup(resize_keyboard=True,row_width=5); kb.add(*[str(i) for i in range(1,n+1)]); kb.add("Выйти"); return kb

def ask_stake(msg):
    u=get_user(msg.from_user.id)
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Назад")
    bot.send_message(msg.chat.id,f"Введите ставку (100-{u['balance']}) или нажмите 'Назад':",reply_markup=kb)
    bot.register_next_step_handler(msg,set_stake)

# ================== СТАРТ ==================
@bot.message_handler(commands=['start'])
def start_bot(msg):
    get_user(msg.from_user.id, msg.from_user.first_name)
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("Начать")
    bot.send_message(msg.chat.id,"Привет! 100 валюты для старта.\nНажми 'Начать'.",reply_markup=kb)

@bot.message_handler(func=lambda m: m.text=="Начать")
def show_main(msg):
    u=get_user(msg.from_user.id)
    if not u["tutorial_done"]:
        bot.send_message(msg.chat.id,"🎓 Туториал:\n1.Клик для денег\n2.Магазин\n3.Играть и ставить\nУдачи!",reply_markup=main_kb())
        u["tutorial_done"]=True; save_data()
    else:
        bot.send_message(msg.chat.id,"Главное меню:",reply_markup=main_kb())

# ================== ЗАРАБОТАТЬ ДЕНЬГИ ==================
@bot.message_handler(func=lambda m: m.text=="Заработать деньги")
def earn_money(msg): bot.send_message(msg.chat.id,"Выберите действие:",reply_markup=earn_kb())

@bot.message_handler(func=lambda m: m.text=="Клик")
def click(msg):
    u=get_user(msg.from_user.id)
    u["balance"]+=u["click_power"]
    save_data()
    bot.send_message(msg.chat.id,f"Заработано {u['click_power']}! Баланс: {u['balance']}",reply_markup=earn_kb())

@bot.message_handler(func=lambda m: m.text=="Баланс")
def balance(msg):
    u=get_user(msg.from_user.id)
    bot.send_message(msg.chat.id,f"Баланс: {u['balance']}\nПассивный доход: {u['passive_income']}/мин",reply_markup=earn_kb())

@bot.message_handler(func=lambda m: m.text=="Назад")
def back(msg):
    bot.send_message(msg.chat.id,"Главное меню:",reply_markup=main_kb())

# ================== МАГАЗИН ==================
@bot.message_handler(func=lambda m: m.text=="Магазин")
def shop_menu(msg): bot.send_message(msg.chat.id,"Выберите:",reply_markup=shop_kb())

@bot.message_handler(func=lambda m: m.text=="Прокачка клика")
def click_shop(msg):
    u=get_user(msg.from_user.id)
    bot.send_message(msg.chat.id,f"Клик: {u['click_power']}\nБаланс: {u['balance']}",reply_markup=click_kb(u))

@bot.message_handler(func=lambda m: m.text and "Улучшить клик" in m.text)
def buy_click(msg):
    u=get_user(msg.from_user.id)
    price=10000*(u["click_level"]+1)
    if u["balance"]>=price:
        u["balance"]-=price; u["click_power"]+=1; u["click_level"]+=1
        save_data()
        bot.send_message(msg.chat.id,f"Клик улучшен! Теперь {u['click_power']} за клик. Баланс: {u['balance']}",reply_markup=main_kb())
    else:
        bot.send_message(msg.chat.id,f"Недостаточно валюты! Баланс: {u['balance']}",reply_markup=main_kb())

@bot.message_handler(func=lambda m: m.text=="Пассивный доход")
def passive_shop(msg):
    u=get_user(msg.from_user.id)
    bot.send_message(msg.chat.id,f"Пассивный доход: {u['passive_income']}/мин\nБаланс: {u['balance']}",reply_markup=passive_kb(u))

@bot.message_handler(func=lambda m: m.text and "Купить" in m.text)
def buy_passive(msg):
    u=get_user(msg.from_user.id)
    l=u["passive_level"]
    if l<len(PASSIVE_LEVELS):
        info=PASSIVE_LEVELS[l]
        if u["balance"]>=info["price"]:
            u["balance"]-=info["price"]
            u["passive_level"]+=1
            u["passive_income"]=info["income"]
            save_data()
            bot.send_message(msg.chat.id,f"Куплено! Пассивный доход: {u['passive_income']}/мин\nБаланс: {u['balance']}",reply_markup=main_kb())
        else:
            bot.send_message(msg.chat.id,f"Недостаточно валюты! Баланс: {u['balance']}",reply_markup=main_kb())

# ================== ИГРАТЬ ==================
@bot.message_handler(func=lambda m: m.text=="Играть")
def choose_diff(msg):
    u = get_user(msg.from_user.id)
    # Обновляем имя при каждом нажатии "Играть"
    u["name"] = msg.from_user.first_name or u["name"]
    save_data()
    bot.send_message(msg.chat.id,"Выберите сложность:",reply_markup=diff_kb())

@bot.message_handler(func=lambda m: m.text in ["Легкий (1-10 ×1.5)","Средний (1-20 ×2)","Сложный (1-50 ×3)"])
def set_diff(msg):
    u=get_user(msg.from_user.id)
    t={"Легкий (1-10 ×1.5)":{"r":10,"m":1.5},"Средний (1-20 ×2)":{"r":20,"m":2},"Сложный (1-50 ×3)":{"r":50,"m":3}}
    info=t[msg.text]
    u["game"]={"range":info["r"],"multiplier":info["m"],"attempts":5,"stake":0}
    save_data()
    ask_stake(msg)

def set_stake(msg):
    u=get_user(msg.from_user.id)
    
    if msg.text=="Назад":
        bot.send_message(msg.chat.id,"Главное меню:",reply_markup=main_kb())
        return
    
    try: amount=int(msg.text)
    except:
        bot.send_message(msg.chat.id,"Нужно число!")
        ask_stake(msg)
        return

    if amount<100 or amount>u["balance"]:
        bot.send_message(msg.chat.id,f"Ставка должна быть 100-{u['balance']}")
        ask_stake(msg)
        return

    u["balance"]-=amount
    u["game"]["stake"]=amount
    u["game"]["number"]=random.randint(1,u["game"]["range"])
    save_data()
    bot.send_message(msg.chat.id,f"Игра началась! Осталось попыток: {u['game']['attempts']}\nУгадай число 1-{u['game']['range']}",reply_markup=number_kb(u["game"]["range"]))

@bot.message_handler(func=lambda m: m.text.isdigit())
def check_guess(msg):
    u=get_user(msg.from_user.id)
    if not u["game"]: bot.send_message(msg.chat.id,"Сначала выбери уровень и ставку",reply_markup=main_kb()); return
    guess=int(msg.text)
    u["game"]["attempts"]-=1
    number=u["game"]["number"]; stake=u["game"]["stake"]; mult=u["game"]["multiplier"]
    if guess==number:
        reward=int(stake*mult)
        u["balance"]+=reward; u["game"]=None; save_data()
        bot.send_message(msg.chat.id,f"Угадал! Выигрыш: {reward}. Баланс: {u['balance']}",reply_markup=main_kb())
    else:
        if u["game"]["attempts"]==0:
            u["game"]=None; save_data()
            bot.send_message(msg.chat.id,f"Проиграл. Число было {number}. Баланс: {u['balance']}",reply_markup=main_kb())
        else:
            save_data()
            bot.send_message(msg.chat.id,f"Неправильно, осталось попыток: {u['game']['attempts']}",reply_markup=number_kb(u["game"]["range"]))

# ================== ТОП ==================
@bot.message_handler(func=lambda m: m.text=="Топ игроков")
def top_players(msg):
    users=data.get("users",{})
    top_list=sorted(users.items(),key=lambda x:x[1].get("balance",0),reverse=True)[:10]
    msg_txt="🏆 <b>ТОП 10 игроков:</b>\n\n"
    for i,(uid,u) in enumerate(top_list,start=1):
        name = u.get("name") or f"Игрок {uid}"
        msg_txt+=f"{i}. {name} — {u.get('balance',0)} 💰\n"
    bot.send_message(msg.chat.id,msg_txt,parse_mode="HTML",reply_markup=main_kb())

# ================== НАСТРОЙКИ ==================
@bot.message_handler(func=lambda m: m.text=="Настройки")
def settings_menu(msg):
    u = get_user(msg.from_user.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if u.get("notify_passive", True):
        kb.add("Отключить уведомления пассивного дохода")
    else:
        kb.add("Включить уведомления пассивного дохода")
    kb.add("Назад")
    bot.send_message(msg.chat.id, "Настройки:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["Отключить уведомления пассивного дохода","Включить уведомления пассивного дохода"])
def toggle_notify(msg):
    u = get_user(msg.from_user.id)
    if msg.text == "Отключить уведомления пассивного дохода":
        u["notify_passive"] = False
        bot.send_message(msg.chat.id, "Уведомления о пассивном доходе отключены.", reply_markup=main_kb())
    else:
        u["notify_passive"] = True
        bot.send_message(msg.chat.id, "Уведомления о пассивном доходе включены.", reply_markup=main_kb())
    save_data()

# ================== ЗАПУСК ==================
bot.skip_pending=True
bot.polling(none_stop=True)
