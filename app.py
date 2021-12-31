import asyncio
import logging
import requests
import re
import random
import time
from aiogram.dispatcher.filters.state import State, StatesGroup
import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, InputFile, CallbackQuery, InlineKeyboardMarkup, \
    InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ContentType
from LiteSQL import lsql
from filters import IsGroupJoin
import datetime
from loader import bot, dp, chats, LOG_CHAT, ADMINS
from test import ThrottlingMiddleware, rate_limit


logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)

sql = lsql('db')
try: sql.select_data(1, 'id')
except: sql.create('id, balance, ref, terms, withdraws, registration_date, last_gift')
class IsPrivate(BoundFilter):
    async def check(self, m: types.Message):
        return m.from_user.id == m.chat.id

class IsNotSub(BoundFilter):
    async def check(self, m: types.Message):
        uid = m.from_user.id
        chatss = []
        for i in chats:
            status = await bot.get_chat_member(i, uid)
            if status.status in ['left', 'kicked']:
                chatss.append(1)
        return len(chatss) >= 1 and m.from_user.id == m.chat.id

u_aye = {}

class Cal(BoundFilter):
    async def check(self, c: CallbackQuery):
        uid = c.from_user.id
        try:
            t = u_aye[f'{uid}']
            if (time.time() - t) < 5:
                return True
            else:
                u_aye[f'{uid}'] = time.time()
                return False
        except: u_aye[f'{uid}'] = time.time(); return False

async def get_now_date():
    date = datetime.datetime.today().strftime("%d.%m.%Y")
    return date

async def check_user(id):
    try: user = sql.select_data(str(id), 'id')[0]; return user
    except: sql.insert_data([(str(id), 0.0, 0, 0, 0, (await get_now_date()), 0.0)], 7); return [id, 0.0, 0, 0, 0, (await get_now_date()), 0.0]


async def update_balance(id, amount, yes=True):
    if yes:
        a = (await check_user(str(id)))[1]
        sql.edit_data('id', str(id), 'balance', a + amount)
    else:
        sql.edit_data('id', str(id), 'balance', amount)

async def check_sub(id):
    uid = id
    chatss = []
    for i in chats:
        status = await bot.get_chat_member(i, uid)
        if status.status in ['left', 'kicked']:
            return False
            break
    return True

async def new_ref(id, ref):
    #await asyncio.sleep(5*60)
    a = await check_sub(id)
    if not a:
        try:
            user = await bot.get_chat(id)
            nams = f'<a href="tg://user?id={id}">{user.first_name}</a>'
            text = f"""❌ У вас мог бы быть рефералл {nams}, но он отписался от одного из каналов в течении 5 минут :("""
            await bot.send_message(ref, text)
        except:
            pass
        return

    await check_user(str(id))
    sql.edit_data('id', str(id), 'ref', str(ref))
    user = await bot.get_chat(id)
    nams = f'<a href="tg://user?id={id}">{user.first_name}</a>'
    text = f"""📎 У вас новый реферал: {nams}"""
    try:
        await bot.send_message(ref, text)
        await update_balance(ref, 1500.0)
    except:
        pass


    ref_2 = (await check_user(ref))
    if ref_2[2] != 0:
        nams = f'<a href="tg://user?id={id}">{user.first_name}</a>'
        text = f"""📎 У вас новый реферал на 2 уровне: {nams}"""
        try:
            await bot.send_message(ref_2[2], text)
            await update_balance(ref_2[2], 500.0)
        except:
            pass

        ref_3 = (await check_user(ref_2[2]))

        if ref_3[2] != 0:
            nams = f'<a href="tg://user?id={id}">{user.first_name}</a>'
            text = f"""📎 У вас новый реферал на 3 уровне: {nams}"""
            try:
                await bot.send_message(ref_3[2], text)
                await update_balance(ref_3[2], 200.0)
            except:
                pass




async def update_withdraws(uid, summ):
    a = (await check_user(str(uid)))[4]
    sql.edit_data('id', uid, 'withdraws', a + summ)

async def get_all_users():
    return sql.get_all_data()

dp.filters_factory.bind(IsGroupJoin, event_handlers=[dp.chat_member_handlers])

main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add('💼 Профиль', '📊 Статистика')
main_kb.add('🚀 О нас', '💸 Заработать')
main_kb.add('Бонус 🎁')

class Wait(StatesGroup):
    wait = State()
''''
@dp.message_handler(IsPrivate(), state=Wait.wait)
async def delete(m: Message, state: FSMContext):
    return await m.delete() '''''


@dp.message_handler(IsPrivate(), commands=['start'])
async def main(m: Message, state: FSMContext):
    uid = m.from_user.id
    chatss = []
    for i in chats: #chatss
        chat = await bot.get_chat(i)
        status = await bot.get_chat_member(i, uid)
        if status.status in ['left', 'kicked']:
            link = await chat.get_url()
            chatss.append(f'<a href="{link}">{chat.title}</a>')
    if len(chatss) >= 1:
        a = "\n".join(chatss)
        msg = m.text.split()
        if len(msg) == 2:
            if msg[1].isdigit():
                await state.update_data(ref_id=int(msg[1]))
            else:
                await state.update_data(ref_id=0)
        else:
            await state.update_data(ref_id=0)
        return await m.reply(f'<b>Вы не подписаны на канал/чат: </b>\n\n{a}\n\n<b>Подпишитесь на все каналы/чаты и после чего я уведомлю вас!\n</b>', reply_markup=ReplyKeyboardRemove(), disable_web_page_preview=True)
    else:
        await m.reply(f'<b> Привет.</b>\n'
                            f'<code>😌 Приятно вас видеть снова!</code>', reply_markup=main_kb)
    if m.text[7:]:
        await m.answer('Чтобы начать работу в боте нужно быть подписаным на каналы не менее 5 минут! Ожидайте полной проверки, спасибо за понимание')
        if sql.select_data(str(m.from_user.id), 'id'):
            return
        else:
            await new_ref(m.from_user.id, m.text[7:])
        await m.answer('Проверка закончена')


@dp.chat_member_handler(is_group_join=True, state='*')
async def new_user_channel(update: types.ChatMemberUpdated, state: FSMContext):
    print('joined')
    try: await bot.get_chat(update.new_chat_member.user.id)
    except:
        try: await state.finish()
        except: pass
        return
    chatss = []
    a = await state.get_data()
    try:
        ref_id = a['ref_id']
    except:
        ref_id = 0
    uid = update.new_chat_member.user.id
    for i in chats:
        status = await bot.get_chat_member(i, uid)
        if status.status in ['left', 'kicked']:
            chatss.append(1)
        if update.new_chat_member.status == 'member':
            chatss == 0
    if len(chatss) == 0:
        user = await check_user(str(uid))
        try:
            await bot.send_message(uid, f'<code>➕ Спасибо за то, что подписались на все каналы! Приступайте к заработку!</code>\n<i>При поддержке</i> - @zz_robot', reply_markup=main_kb)
        except:
            print('no')
        try: await state.finish()
        except: pass
        if user[3] == 0:
            sql.edit_data('id', uid, 'terms', 1)
            await new_ref(uid, ref_id)

@dp.message_handler(IsNotSub(), state='*')
async def msg(m: Message, state: FSMContext):
    try: await state.finish()
    except: pass
    chatss = []
    uid = m.from_user.id
    for i in chats:
        chat = await bot.get_chat(i)
        status = await bot.get_chat_member(i, uid)
        if status.status in ['left', 'kicked']:
            link = await chat.get_url()
            chatss.append(f'<a href="{link}">{chat.title}</a>')
    if len(chatss) >= 1:
        a = "\n".join(chatss)
        await state.update_data(ref_id=0)
        return await m.reply(f'<b>Вы не подписаны на канал:</b>\n\n{a}\n\n<b>Подпишитесь на все каналы и после чего я уведомлю вас!</b>', reply_markup=ReplyKeyboardRemove(), disable_web_page_preview=True)

withdraws = 0
for i in sql.get_all_data():
    withdraws += i[4]

stats = InlineKeyboardMarkup(row_width=2)
a = InlineKeyboardButton(text='🪙 Топ по выводам', callback_data='top_withdraws')
b = InlineKeyboardButton(text='🫂 Топ по рефам', callback_data='top_refs')
c = InlineKeyboardButton(text='💰 Топ по балансу', callback_data='top_balance')
stats.add(a, b, c)
stats.add(InlineKeyboardButton(text='Владелец 🧨', url='https://t.me/CulerVPN'))

def parse2(x: str):
    num = float(x.split(':')[1])
    return num

def parse(x: str):
    num = int(x.split(':')[1])
    return num
   
   

@dp.callback_query_handler(Cal(), state='*')
async def msg(c: CallbackQuery, state: FSMContext):
    uid = c.from_user.id
    a = u_aye[f"{uid}"]
    return await c.answer(f'Попробуйте через {round(5 - (time.time() - a), 2)} секунд', show_alert=True)



@dp.callback_query_handler(text='nazad')
async def msg(c: CallbackQuery):
    uid = c.from_user.id
    try: await state.finish()
    except: pass
    user = await check_user(str(uid))

    day_users = len(sql.select_data((await get_now_date()), 'registration_date'))
    all_users = len(sql.get_all_data())

    text = f"""➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>📊 Статистика бота</b>
➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>✔️ За сегодня:</b>
<code>     </code><b>🥷Пользователей:</b> <code>{day_users}</code>
<b>♾ За всё время:</b>
<code>     </code><b>🥷Пользователей:</b> <code>{all_users}</code>
<code>     </code><b>💸Выведено:</b> <code>{withdraws} TMT</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>При поддержке - @zz_robot</b>"""

    await c.message.edit_text(text, reply_markup=stats)

@dp.callback_query_handler(text_startswith='top_')
async def msg(c: CallbackQuery):
    await c.answer('Загрузка топа...', show_alert=False)
    a = c.data.split('_')[1]
    kb = InlineKeyboardMarkup().add(InlineKeyboardButton(text='⬅️ Назад', callback_data='nazad'))
    if a == 'withdraws':
        w = [f'{i[0]}:{i[4]}' for i in sql.get_all_data()]
        w.sort(key=parse2, reverse=True)

        w = w[:10]

        text = """**📊 Топ по выводам с бота:**

"""
        x = 0
        for i in w:
            x += 1
            uid = int(i.split(':')[0])
            summ = float(i.split(':')[1])
            try:
                user = await bot.get_chat(uid)
                name = user.first_name.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('`', '').replace('*', '').replace('_', '').replace('{', '').replace('}', '').replace('~', '')
            except:
                name = 'Неизвестный'
            nn = f'[{name}](tg://user?id={uid})'
            text += f'{x}. {nn} — `{summ} TMT` \n'
    elif a == 'balance':
        w = [f'{i[0]}:{i[1]}' for i in sql.get_all_data()]
        w.sort(key=parse2, reverse=True)

        w = w[:10]

        text = """**📊 Топ богачей бота:**

"""
        x = 0
        for i in w:
            x += 1
            uid = int(i.split(':')[0])
            summ = round(float(i.split(':')[1]), 2)
            try:
                user = await bot.get_chat(uid)
                name = user.first_name.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('`', '').replace('*', '').replace('_', '').replace('{', '').replace('}', '').replace('~', '')
            except:
                name = 'Неизвестный'
            nn = f'[{name}](tg://user?id={uid})'
            text += f'{x}. {nn} — `{summ} TMT` \n'
    elif a == 'refs':
        users = [i[2] for i in sql.get_all_data()]
        b = []
        for i in [i[0] for i in sql.get_all_data()]:
            b.append(f'{i}:{users.count(i)}')
        b.sort(key=parse, reverse=True)

        b = b[:10]

        text = """**📊 Топ рефоводов бота:**

"""
        x = 0
        for i in b:
            x += 1
            uid = int(i.split(':')[0])
            summ = int(i.split(':')[1])
            try:
                user = await bot.get_chat(uid)
                name = user.first_name.replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace('`', '').replace('*', '').replace('_', '').replace('{', '').replace('}', '').replace('~', '')
            except:
                name = 'Неизвестный'
            nn = f'[{name}](tg://user?id={uid})'
            text += f'{x}. {nn} — `{summ} рефералов` \n'
    await c.message.edit_text(text, reply_markup=kb, parse_mode='Markdown')


@dp.message_handler(IsPrivate(), lambda m: m.text == '📊 Статистика', state='*')
@rate_limit(3, '📊 Статистика')
async def msg(m: Message, state: FSMContext):
    uid = m.from_user.id
    try: await state.finish()
    except: pass
    user = await check_user(str(uid))

    day_users = len(sql.select_data((await get_now_date()), 'registration_date'))
    all_users = len(await get_all_users())

    text = f"""➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>📊 Статистика бота</b>
➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>✔️ За сегодня:</b>
<code>     </code><b>🥷Пользователей:</b> <code>{day_users}</code>
<b>♾ За всё время:</b>
<code>     </code><b>🥷Пользователей:</b> <code>{all_users}</code>
<code>     </code><b>💸Выведено:</b> <code>{withdraws} TMT</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>Идёт набор в спонсоры! Писать в лс Владельцу (кнопка ниже)</b>"""

    await m.reply(text, reply_markup=stats)

zarabot = InlineKeyboardMarkup()
zarabot_btn = InlineKeyboardButton(text='📖 Условия', callback_data='rules')
zarabot.add(zarabot_btn)

zarab = InlineKeyboardMarkup().add(InlineKeyboardButton(text='Назад ⬅️', callback_data='nazad_zarabot'))

@dp.callback_query_handler(text='nazad_zarabot')
async def msg(c: CallbackQuery):
    uid = c.from_user.id
    user = await check_user(str(uid))
    text = f"""<b>💸 Заработок на рефераллах 

1️⃣ Вы получите 15 B с каждого рефералла на 1 уровне

2️⃣ Вы получите 500 IB с каждого рефералла на 2 уровне

3️⃣ Вы получите 200 SB с каждого рефералла на 3 уровне

💸 Ваша реф ссылка, по которой должен перейти рефералл:</b> https://t.me/airdropeasy_bot?start={uid}"""

#💸 Ваша реф ссылка, по которой должен перейти рефералл:</b> https://t.me/lxrefbot?start={uid}"""
    await c.message.edit_text(text, disable_web_page_preview=True, reply_markup=zarabot)

@dp.callback_query_handler(text='rules')
async def msg(c: CallbackQuery):
    text = """<b>📎 Условия реферальной системы

1. Накрутка категорически запрещена

2. Ваш реферал должен подписаться на все каналы и если в течении 5 минут он отпишется хотя бы от одного из, то он не будет защитан вам.

3. Проверка реферала длится 5 минут, поэтому сразу вам не прийдёт уведомление.

4. Вывод только на QIWI / BTC banker

5. Мы не отвечаем за то, что вы ввели неверный номер или ник.</b>"""
    await c.message.edit_text(text, reply_markup=zarab)

@dp.message_handler(IsPrivate(), lambda m: m.text == '💸 Заработать', state='*')
@rate_limit(3, '💸 Заработать')
async def msg(m: Message, state: FSMContext):
    try: await state.finish()
    except: pass
    uid = m.from_user.id
    user = await check_user(str(uid))
    text = f"""<b>💸 Заработок на рефераллах 

1️⃣ Вы получите 1500 TMT с каждого рефералла на 1 уровне

2️⃣ Вы получите 500 TMT с каждого рефералла на 2 уровне

3️⃣ Вы получите 200 TMT с каждого рефералла на 3 уровне


💸 Ваша реф ссылка, по которой должен перейти рефералл:</b> https://t.me/tmzarabotokbot?start={uid}"""

#💸 Ваша реф ссылка, по которой должен перейти рефералл:</b> https://t.me/lxrefbot?start={uid}"""
    await m.reply(text, disable_web_page_preview=True, reply_markup=zarabot)

a = InlineKeyboardButton(text='💸 Канал', url='https://t.me/tm_zarabotok')
b = InlineKeyboardButton(text='🧑‍💻 Владелец', url='https://t.me/CulerVPN')
c = InlineKeyboardButton(text='🧃 Чат', url='https://t.me/tkmzarabotok')

about = InlineKeyboardMarkup(row_width=2)
about.add(a, b, c)

@dp.message_handler(IsPrivate(), lambda m: m.text == '🚀 О нас', state='*')
@rate_limit(3, '🚀 О нас')
async def msg(m: Message, state: FSMContext):
    uid = m.from_user.id
    try: await state.finish()
    except: pass
    user = await check_user(str(uid))

    text = """<b>▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️
▪️▪️ Наш проект был запущен: 31.12.2021
▪️▪️
▪️▪️ У нас 3-ёх уровневая система рефералов
▪️▪️
▪️▪️Администрация бота:
▪️▪️@CulerVPN
▪️▪️@tkmzarabotok
▪️▪️@tm_zarabotok

▪▪    При поддержке:

▪️▪️ @zz_robot

▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️▪️</b>"""

    await m.reply(text, reply_markup=about)

profile = InlineKeyboardMarkup(row_width=2)

a = InlineKeyboardButton(text='💰 Вывести', callback_data='withdraw')
b = InlineKeyboardButton(text='🥃 Заработать', callback_data='zarabotat')

profile.add(a, b)

@dp.callback_query_handler(text='back')
async def msg(c: CallbackQuery):
    uid = c.from_user.id
    user = await check_user(str(uid))
    ref_name = 'Вас никто не пригласил'
    if user[2] != 0:
        ref_name = (await bot.get_chat(user[2])).title
    users = [i[2] for i in sql.get_all_data()]
    your_refs = users.count(str(uid))
    text = f"""➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>✖️ Айди:</b> <code>{uid}</code>
<b>✖️ Баланс:</b> <code>{round(user[1], 2)} TMT</code>
<b>✖️ Пригласивший:</b> <a href='tg://user?id={user[2]}'>{ref_name}</a>
<b>✖️ Дата регистрации:</b> <code>{user[5]}</code>
<b>✖️ Выводы:</b> <code>{user[4]} TMT</code>
<b>✖️ Ваши рефералы:</b> <code>{your_refs}</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖"""
    await c.message.edit_text(text, reply_markup=profile)

@dp.callback_query_handler(text='zarabotat')
async def msg(c: CallbackQuery):
    uid = c.from_user.id
    user = await check_user(str(uid))
    kb = InlineKeyboardMarkup().add(zarabot_btn, InlineKeyboardButton(text='Назад ⬅️', callback_data='back'))

    text = f"""<b>💸 Заработок на рефераллах

1️⃣ Вы получите 1500 TMT с каждого рефералла на 1 уровне

2️⃣ Вы получите 500 TMT с каждого рефералла на 2 уровне

3️⃣ Вы получите 200 TMT с каждого рефералла на 3 уровне


💸 Ваша реф ссылка, по которой должен перейти рефералл:</b> https://t.me/https://t.me/tmzarabotokbot?start={uid}"""

    await c.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)

def otmena():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('Отмена 🔙')
    return kb

class Withdraw(StatesGroup):
    summ = State()
    number = State()

@dp.callback_query_handler(text='withdraw')
async def msg(c: CallbackQuery):
    uid = c.from_user.id
    user = await check_user(str(uid))

    if user[1] < 100000:
        return await c.answer('На балансе должно быть не менее 100000A ❌', show_alert=True)
    else:
        await c.answer('🪙 Введите сумму на вывод:', show_alert=False)
        await c.message.answer('<b>🪙 Введите сумму на вывод:</b>', reply_markup=otmena())
        await Withdraw.summ.set()

@dp.message_handler(IsPrivate(), state=Withdraw.summ)
async def aye(m: Message, state: FSMContext):
    if not m.text.isdigit():
        await state.finish()
        return await m.answer(reply_markup=main_kb, text='Произошла ошибка, введите правильное число в след. раз')

    summ = int(m.text)

    uid = m.from_user.id
    user = await check_user(str(uid))

    if summ < 100000:
        await state.finish()
        return await m.answer(reply_markup=main_kb, text=f'<b>🥃 Минимальная сумма вывода 100000 !</b>')

    if user[1] < summ:
        await state.finish()
        return await m.answer(reply_markup=main_kb, text=f'<b>❌ На балансе недостаточно денег, ваш баланс:</b> <code>{round(user[1], 2)} TMT</code>')

    await m.answer(f'<b>🥝 Введите номер вашего QIWI кошелька</b> (<code>Пример: +79173819366</code>):\n\n(Если хотите вывести на BTC banker, то напишите ваш ник в телеграмм через @, с вами свяжется администратор)')

    await Withdraw.next()
    await state.update_data(s=summ)


async def log_chat(text):
    chat_id = LOG_CHAT
    print(chat_id)
    await bot.send_message(chat_id, text, disable_web_page_preview=True)

@dp.message_handler(IsPrivate(), state=Withdraw.number)
async def aye(m: Message, state: FSMContext):
    if not m.text.isdigit() and not '+' in m.text and not '@' in m.text:
        await state.finish()
        return await m.answer(reply_markup=main_kb, text='Произошла ошибка, введите правильный номер в след. раз')


    number = int(m.text)
    a = await state.get_data()

    summ = a['s']

    await state.finish()

    uid = m.from_user.id

    await update_balance(uid, -summ)

    await m.answer(f'''<b>Заявка на вывод успешно сформирована ✅
    
⚙️ Ожидайте до 48 часов

💰 Сумма:</b> <code>{float(summ)} TMT</code>
<b>💡 Реквизиты:</b> <code>{number}</code>''', reply_markup=main_kb)

    withdraw_kb = InlineKeyboardMarkup(row_width=1)
    a = InlineKeyboardButton(text='✅ Выведено', callback_data=f'ok_{uid}_{summ}')
    b = InlineKeyboardButton(text='🔄 Вернуть', callback_data=f'backup_{uid}_{summ}')
    c = InlineKeyboardButton(text='❌ Отказано', callback_data=f'no_{uid}')
    withdraw_kb.add(a, b, c)
    for i in ADMINS:
        await bot.send_message(i, f'<b>💸 Новая заявка на вывод!\n🧑‍💻 От</b> <a href="tg://user?id={uid}">Пользователя</a>\n<b>🪙 На сумму:</b> <code>{summ} TMT</code>\n⚙️ Реквизиты: {number}', reply_markup=withdraw_kb)

    #await log_chat(f'<a href="tg://user?id={uid}">Пользователь</a> создал заявку на вывод\n<b>🪙 На сумму:</b> <code>{summ} </code>')


@dp.message_handler(IsPrivate(), lambda m: m.text == '💼 Профиль', state='*')
@rate_limit(3, '💼 Профиль')
async def msg(m: Message, state: FSMContext):
    uid = m.from_user.id
    try: await state.finish()
    except: pass
    user = await check_user(str(uid))
    ref_name = 'Вас никто не пригласил'
    if user[2] != 0:
        ref_name = (await bot.get_chat(user[2])).title
    users = [i[2] for i in sql.get_all_data()]
    print(users)
    for i in sql.get_all_data():
        print(i)
    print(sql.get_all_data())
    your_refs = users.count(str(uid))
    text = f"""➖➖➖➖➖➖➖➖➖➖➖➖➖
<b>✖️ Айди:</b> <code>{uid}</code>
<b>✖️ Баланс:</b> <code>{round(user[1], 2)} TMT</code>
<b>✖️ Пригласивший:</b> <a href='tg://user?id={user[2]}'>{ref_name}</a>
<b>✖️ Дата регистрации:</b> <code>{user[5]}</code>
<b>✖️ Выводы:</b> <code>{user[4]} TMT</code>
<b>✖️ Ваши рефералы:</b> <code>{your_refs}</code>
➖➖➖➖➖➖➖➖➖➖➖➖➖"""
    return await m.reply(text, reply_markup=profile)






@dp.callback_query_handler(text_startswith='ok_')
async def msg(c: CallbackQuery):
    uid = int(c.data.split('_')[1])
    summ = float(c.data.split('_')[2])
    text = f"""💸 <a href="tg://user?id={uid}">Пользователь</a> <b>успешно вывел {summ} TMT</b>"""

    await log_chat(text)
    text = f"""<b>💰 Вам было успешно выведено {summ} TMT

Просьба оставить отзыв в нашем чате 💕</b>"""
    await bot.send_message(str(uid), text, reply_markup=about)
    await update_withdraws(str(uid), summ)
    await c.answer('Успешно выведено.')
    await c.message.delete()


@dp.callback_query_handler(text_startswith='backup_')
async def msg(c: CallbackQuery):
    global withdraws
    uid = int(c.data.split('_')[1])
    summ = float(c.data.split('_')[2])
    withdraws += summ
#	text = f"""💸 <a href="tg://user?id={uid}">Пользователь</a> <b>успешно вывел {summ} </b>"""
#	await log_chat(text)
    await update_balance(str(uid), summ)
    text = f"""<b>💰 Вам успешно были возвращены средства, вывод не удался, сумма: {summ} TMT</b>"""
    await bot.send_message(str(uid), text)
    await c.answer('Успешно возвращено.')
    await c.message.delete()

@dp.callback_query_handler(text_startswith='no_')
async def msg(c: CallbackQuery):
    await c.answer('Успешно отменено.')
    await c.message.delete()


def otmena():
    return types.ReplyKeyboardMarkup(resize_keyboard=True).add('Отмена')

class Rass(StatesGroup):
    wait = State()
    buttons = State()
    vremya = State()

@dp.callback_query_handler(text='rass')
async def adm_rass(call: types.CallbackQuery):
    if call.from_user.id in ADMINS:
        await Rass.wait.set()
        await call.message.answer(f'<b>Введи текст/фото для рассылки</b>', reply_markup=otmena())

@dp.message_handler(lambda message: message.text == 'Отмена', state='*')
async def msg(m: types.Message, state: FSMContext):
    try: await state.finish(); await m.answer('Отменено', reply_markup=main_kb)
    except: pass

@dp.message_handler(state=Rass.wait, content_types=types.ContentTypes.ANY)
async def adm_rass(msg: types.Message, state: FSMContext):
    await msg.answer('Введите кнопки\n|название|ссылка|\n\n(или + чтобы не юзать)', reply_markup=otmena())
    await state.update_data(msgs=msg)
    await Rass.next()


ayeshka = []

@dp.message_handler(state=Rass.buttons, content_types=types.ContentTypes.ANY)
async def adm_rass(msg: types.Message, state: FSMContext):
    a = await state.get_data()
    kb = types.InlineKeyboardMarkup()
    if msg.text.count('|') >= 3:
        a = msg.text.split('|')
        text = a[1]
        url = a[2]
        kb.insert(types.InlineKeyboardButton(text=text, url=url))
        ayess = 1
        if msg.text.count('\n') == 1:
            a = msg.text.split('\n')[1]
            a = a.split('|')
            text = a[1]
            url = a[2]
            kb.insert(types.InlineKeyboardButton(text=text, url=url))
        kb = kb
    await state.update_data(kb=kb)
    await msg.reply('Введите время через которое запостить рассылку, в секундах.')
    await Rass.next()


@dp.message_handler(state=Rass.vremya, content_types=types.ContentTypes.ANY)
async def adm_rass(msg: types.Message, state: FSMContext):
    a = await state.get_data()
    msgs = a['msgs']
    plus = []
    minus = []
    kb = a['kb']
    ayess = 0
    await state.finish()
    await msg.reply(f'Пост будет запощен через {msg.text} секунд')
    await asyncio.sleep(float(msg.text))

    row = sql.get_all_data()
    for i in row:
        try:
            if not i[0] in ayeshka:
                if ayess == 1:
                    await msgs.send_copy(int(i[0]), reply_markup=kb)
                else:
                    await msgs.send_copy(int(i[0]))
                plus.append(i)
        except Exception as e:
            minus.append(i)
            if not i[0] in ayeshka:
                ayeshka.append(int(i[0]))
    return await msg.reply(f'<b>Рассылка завершена!</b>\n\n✅ Успешно: {len(plus)}\n❌ НЕУспешно: {len(minus)}')


@dp.message_handler(lambda m: m.text.lower() == 'бонус 🎁')
async def bonus(m: types.Message):
    user = await check_user(str(m.from_user.id))
    if time.time() - user[6] >= 60*60*24:
        await update_balance(m.from_user.id, 250, True)
        await m.reply('Вы получили бонус 250 TMT 🎁')
        return sql.edit_data('id', str(m.from_user.id), 'last_gift', time.time())
    else:
        return await m.reply(f'Вы уже забирали свой бонус сегодня 🎁')


@dp.message_handler(lambda m: m.from_user.id in ADMINS and m.text.startswith('/info '))
async def ayehshshsg(m: types.Message):
    uid = int(m.text.split()[1])
    await m.answer(f'<a href="tg://user?id={uid}">Permalink</a>')

@dp.message_handler(lambda m: m.from_user.id in ADMINS and m.text.startswith('/balance '))
async def ayehshshsg(m: types.Message):
    uid = int(m.text.split()[1])
    summ = float(m.text.split()[2])
    await update_balance(uid, summ, False)
    await m.answer(f'<a href="tg://user?id={uid}">Пользователю</a> успешно выдано {summ} TMT')


@dp.message_handler(lambda m: m.from_user.id in ADMINS and m.text.startswith('/withdraws '))
async def ayehshshsg(m: types.Message):
    uid = int(m.text.split()[1])
    summ = float(m.text.split()[2])
    sql.edit_data('id', uid, 'withdraws', summ)
    await m.answer(f'<a href="tg://user?id={uid}">Пользователю</a> успешно выдано на выводы {summ} TMT')


@dp.message_handler(lambda m: m.from_user.id in ADMINS and m.text == '/admin')
async def ayehshshsg(m: types.Message):
    admin_kb = types.InlineKeyboardMarkup()
    admin_kb.add(types.InlineKeyboardButton(text='Рассылка 📣', callback_data='rass'))
    admin_kb.add(InlineKeyboardButton(text='Управление юзером 🧑‍💻', callback_data='panel'))
    await m.answer(f'<b>В боте: {len(sql.get_all_data())} пользователей</b>', reply_markup=admin_kb)

msgs = {}

async def get_sms(uid):
    try: t = msgs[f'{uid}']; return t
    except: msgs[f'{uid}'] = 0; return t

async def add_sms(uid):
    a = msgs[f'{uid}']
    msgs[f'{uid}'] = a + 1

'''
a = """
class Panel(StatesGroup):
    user_id = State()

@dp.callback_query_handler(text='panel')
async def aye(c: CallbackQuery, state: FSMContext):
    m = c.message
    await m.reply('Введите айди юзера:', reply_markup=otmena())
    await Panel.user_id.set()

@dp.message_handler(state=Panel.user_id)
async def aye(m: Message, state: FSMContext):
    try:
        uid = int(m.text)
        await m.reply(f'Управление <a href="tg://user?id={uid}>пользователем</a>\n\nБаланс: {round(user[1], 2)}', reply_markup=aye)
        await state.finish()
    except:
        await m.reply('error', reply_markup=main_kb)
        await state.finish()"""

a = """async def get_time(uid):
    try: a = a_id_id[f'{uid}']; return a
    except: a_id_id[f'{uid}'] = time.time(); return time.time()

async def nick_time():
    while True:
        await asyncio.sleep(3600)
        now_time = time.time()
        users = []
        for i in (await get_all_users()):
            if (now_time - (await get_time(uid))) >= 86400:
                users.append(uid)
        for i in users:
            await update_balance(uid, 1)
            await bot.send_message(i, 'Ты получил 1₽ за, то что продержал #LXREF в нике 24 часа.')"""
'''


if __name__ == '__main__':
#	loop = asyncio.get_event_loop()
#    loop.create_task(nick_time())
    dp.middleware.setup(ThrottlingMiddleware())
    executor.start_polling(dp, skip_updates=True, allowed_updates=['chat_member', 'message', 'callback_query', 'chat', 'member'])
