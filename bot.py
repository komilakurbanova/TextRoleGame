import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton

from database import *

API_TOKEN = 'TOKEN'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

menu_markup = ReplyKeyboardMarkup([[KeyboardButton(text='Инвентарь')],
                                   [KeyboardButton(text='Статы')],
                                   [KeyboardButton(text='Изменить имя')],
                                   [KeyboardButton(text='Локации')],
                                   [KeyboardButton(text='Магазин')]],
                                  one_time_keyboard=True,
                                  resize_keyboard=True,
                                  )

inv_markup = ReplyKeyboardMarkup([[KeyboardButton(text='Использовать')],
                                  [KeyboardButton(text='Снять')],
                                  [KeyboardButton(text='Назад')]],
                                 one_time_keyboard=True,
                                 resize_keyboard=True,
                                 )

store = ReplyKeyboardMarkup([[KeyboardButton(text='Купить')],
                             [KeyboardButton(text='Продать')],
                             [KeyboardButton(text='Назад')]],
                            one_time_keyboard=True,
                            resize_keyboard=True,
                            )


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply(
        f"Добро пожаловать в игру, странник! \n\nНазовись же, путник, дабы Пресветлая могла одарить тебя своим благом",
        reply_markup=menu_markup)
    add_user(message.chat.id, 'none')
    c.execute(f'UPDATE Person SET Stage = "new" WHERE UserID = {message.chat.id}')
    conn.commit()


@dp.message_handler()
async def commands(message: types.Message):
    user = get_user(message.chat.id)[0]
    if user[12] == 'wait' and user[13] > datetime.now().timestamp():
        await message.answer('Сейчас тебе запрещено действовать')
        return
    if user[12] == 'new':
        c.execute(f'UPDATE Person SET Nickname = "{message.text}", Stage = "game" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(
            f'Богиня изменила твое имя в книге смертных на "{message.text}"! Возрадуйся и наслаждайся игрой',
            reply_markup=menu_markup)
        return
    if message.text == "Назад":
        c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer('Ты передумал? Что ж, может и к лучшему',
                             reply_markup=menu_markup)
        return

    if user[12] == 'putting_on':
        c.execute(f'SELECT * from Items WHERE ItemName = "{message.text}"')
        item = c.fetchall()
        if not len(item):
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer('Такого предмета попросту не существует!', reply_markup=menu_markup)
            return
        item_id = item[0][0]
        item_category = item[0][4]
        req_level = item[0][11]
        if req_level > user[2]:
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer(f'Ты пока не достоит этого предмета. Развей себя до {req_level} ступени',
                                 reply_markup=menu_markup)
            return
        inv = get_inventory(message.chat.id)
        qnty_in_inv = 0
        qnty_on = 0
        for i in inv:
            item_from_inv = get_item(i[1])[0]
            if item_from_inv[0] == item_id:
                qnty_in_inv = i[2]
                qnty_on = i[3]
            print()
            print(i)
            print(item_from_inv)
            print(item_category)
            print(item_id)
            if i[3] > 0 and item_from_inv[4] == item_category:
                if item_category != 'potion':
                    c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
                    conn.commit()
                    await message.answer(f'На тебе уже {item_from_inv[1]}. Не гневай богов жадностью',
                                         reply_markup=menu_markup)
                    return
        if qnty_in_inv:
            c.execute(
                f"UPDATE Inventory SET quantity = '{qnty_in_inv}', flag = '{qnty_on + 1}' WHERE UserID = {message.chat.id} AND ItemID = {item_id}")
        else:
            c.execute("INSERT INTO Inventory VALUES (?, ?, 0, ?)", [message.chat.id, item_id, qnty_on])
        c.execute(
            f'UPDATE Person SET HP = {max(0, user[3] + item[0][5])}, Attack = {user[6] + item[0][7]}, MagicAttack = {user[7] + item[0][8]}, Armour = {user[9] + item[0][9]}, MagicArmour = {user[10] + item[0][10]}, Stage = "game" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(f'Просьба выполнена, используется {message.text}', reply_markup=menu_markup)
        return

    if user[12] == 'putting_off':
        c.execute(f'SELECT * from Items WHERE ItemName = "{message.text}"')
        item = c.fetchall()
        if not len(item):
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer('Такого предмета попросту не существует!', reply_markup=menu_markup)
            return
        item_id = item[0][0]
        inv = get_inventory(message.chat.id)
        for i in inv:
            if i[1] == item_id and i[3]:
                c.execute(
                    f"UPDATE Inventory SET quantity = '{i[2]}', flag = '{i[3] - 1}' WHERE UserID = {message.chat.id} AND ItemID = {item_id}")
                c.execute(
                    f'UPDATE Person SET HP = {max(0, user[3] - item[0][5])}, Attack = {user[6] - item[0][7]}, MagicAttack = {user[7] - item[0][8]}, Armour = {user[9] - item[0][9]}, MagicArmour = {user[10] - item[0][10]}, Stage = "game" WHERE UserID = {message.chat.id}')
                conn.commit()
                await message.answer(f'{message.text} отныне в инвентаре', reply_markup=menu_markup)
                return
        c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(f'А ведь у тебя такого и не было! Ты ходил в иллюзии?', reply_markup=menu_markup)
        return

    if user[12] == "changing_location":
        c.execute(f'SELECT * from Locations WHERE LocationName = "{message.text}"')
        loc = c.fetchall()
        if not len(loc):
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer(
                'Это мираж. Попытка войти в него завершится смертью. Благословление Пресветлой не пустит тебя туда',
                reply_markup=menu_markup)
            return
        wait = get_distance(user[11], loc[0][0])
        await message.answer(f'Хорошо, {user[1]}, иди с миром. {round(wait)} секунд ты будешь в пути',
                             reply_markup=ReplyKeyboardRemove())
        c.execute(
            f'UPDATE Person SET ActionAllowedTime = {datetime.now().timestamp() + wait}, Stage = "wait" WHERE UserID = {message.chat.id}')
        conn.commit()
        await asyncio.sleep(wait)
        c.execute(f'UPDATE Person SET LocationID = {loc[0][0]}, Stage = "game" WHERE UserID = {message.chat.id}')
        if loc[0][3] == 'town':
            c.execute(f'UPDATE Person SET CurHP = {user[3]} WHERE UserID = {message.chat.id}')
        await message.answer(f'Ты прибыл в {loc[0][4]}!', reply_markup=menu_markup)
        return

    if user[12] == 'buying':
        c.execute(f'SELECT * from WhereItems WHERE ItemName = "{message.text}"')
        item_to_buy = c.fetchall()
        if not len(item_to_buy):
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer('Хм, ты не успел и все уже раскупили', reply_markup=menu_markup)
            return
        item = get_item(item_to_buy[0][0])[0]
        if item[2] > user[5]:
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer('У тебя недостаточно монет для покупки!', reply_markup=menu_markup)
            return
        c.execute(f'SELECT * from Inventory WHERE ItemID = "{item[0]}"')
        item_in_inv = c.fetchall()
        if not len(item_in_inv):
            c.execute("INSERT INTO Inventory VALUES (?, ?, 1, 0)", [user[0], item[0]])
        else:
            c.execute(f'UPDATE Inventory SET quantity = "{item_in_inv[0][2] + 1}" WHERE  ItemID = "{item[0]}"')
        c.execute(f'UPDATE Person SET Money = {user[5] - item[2]}, Stage = "game" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(f'- {item[2]} монет\nТеперь {message.text} в инвентаре', reply_markup=menu_markup)
        return

    if user[12] == 'selling':
        c.execute(f'SELECT * from WhereItems WHERE ItemName = "{message.text}"')
        item_to_sell = c.fetchall()
        if not len(item_to_sell):
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer('Торговец закрыл свою лавку', reply_markup=menu_markup)
            return
        item = get_item(item_to_sell[0][0])[0]
        c.execute(f'SELECT * from Inventory WHERE ItemID = "{item[0]}"')
        item_in_inv = c.fetchall()
        if not len(item_in_inv):
            c.execute(f'UPDATE Person SET Stage = "game" WHERE UserID = {message.chat.id}')
            conn.commit()
            await message.answer('Торговец закрыл свою лавку', reply_markup=menu_markup)
            return
        c.execute(f'UPDATE Person SET Money = {user[5] + item[3]}, Stage = "game" WHERE UserID = {message.chat.id}')
        c.execute(f'UPDATE Inventory SET quantity = "{item_in_inv[0][2] - 1}" WHERE  ItemID = "{item[0]}"')
        conn.commit()
        await message.answer(f'+ {item[3]} монет\n{message.text} продан', reply_markup=menu_markup)
        return


    if message.text == "Статы":
        await message.answer(f'''
            Level: {user[2]}
XP {user[8]}
HP {user[4]}/{user[3]}
Money: {user[5]}
        
Attack {user[6]}
MagicAttack {user[7]}
Armour {user[9]}
MagicArmour {user[10]}''')
        return

    if message.text == "Изменить имя":
        c.execute(f'UPDATE Person SET Stage = "new" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.reply("И как ты хочешь именоваться отныне?")
        return

    if message.text == "Инвентарь":
        inventory = get_inventory(message.chat.id)
        on = 'На вас: \n'
        off = 'Инвентарь: \n'
        for i in inventory:
            item = get_item(i[1])[0]
            if i[3] == 1:
                on += item[1] + '\n'
            elif i[3] > 0:
                on += item[1] + f' x{i[3]}\n'
            qnty = i[2] - i[3]
            if qnty == 1:
                off += item[1] + '\n'
            elif qnty > 0:
                off += item[1] + f' x{qnty}\n'
        await message.answer(on + '\n' + off, reply_markup=inv_markup)
        return

    if message.text == "Снять":
        inventory = get_inventory(message.chat.id)
        to_put_off = ReplyKeyboardMarkup()
        for i in inventory:
            item = get_item(i[1])[0]
            if i[3] > 0:
                to_put_off.add(KeyboardButton(text=item[1]))
        to_put_off.add(KeyboardButton(text='Назад'))
        c.execute(f'UPDATE Person SET Stage = "putting_off" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer('Выбери, что хочешь снять', reply_markup=to_put_off)
        return

    if message.text == "Использовать":
        inventory = get_inventory(message.chat.id)
        to_put_on = ReplyKeyboardMarkup()
        for i in inventory:
            item = get_item(i[1])[0]
            if i[2] - i[3] > 0:
                to_put_on.add(KeyboardButton(text=item[1]))
        to_put_on.add(KeyboardButton(text='Назад'))
        c.execute(f'UPDATE Person SET Stage = "putting_on" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer('Выбери, что хочешь использовать', reply_markup=to_put_on)
        return

    if message.text == "Локации":
        user_location_id = user[11]
        s = 'Доступные: \n\n'
        c.execute(f'SELECT * from Distance WHERE LocationFromID = {user_location_id} AND Dist <= 10')
        to_go_from_here = c.fetchall()
        c.execute(f'SELECT * from Distance WHERE LocationToID = {user_location_id} AND Dist <= 10')
        to_come_here_from = c.fetchall()
        locations = ReplyKeyboardMarkup()
        for n in to_come_here_from:
            tmp = get_location(n[0])[0]
            s += tmp[4]
            locations.add(KeyboardButton(text=tmp[4]))
            if tmp[3] == 'town':
                s += ' – мирное\n'
            else:
                s += '   подземелье\n'
        for n in to_go_from_here:
            tmp = get_location(n[1])[0]
            s += tmp[4]
            locations.add(KeyboardButton(text=tmp[4]))
            if tmp[3] == 'town':
                s += ' – мирное\n'
            else:
                s += ' – подземелье\n'
        locations.add(KeyboardButton(text='Назад'))
        c.execute(f'UPDATE Person SET Stage = "changing_location" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(s, reply_markup=locations)
        return


    if message.text == "Магазин":
        await message.answer('Ты хочешь купить что-то у торговца? Или, может быть, тебе есть, что ему предложить?',
                             reply_markup=store)
        return


    if message.text == "Купить":
        cur_loc = get_location(user[11])[0]
        if cur_loc[3] == 'dungeon':
            await message.answer('На вражеской территории нечего купить. Жаль, что жизнь не дают за деньги...',
                                 reply_markup=menu_markup)
            return
        c.execute(f'SELECT * from WhereItems WHERE LocationID = {cur_loc[0]}')
        items = c.fetchall()
        if not len(items):
            await message.answer('Здесь нечего купить, путник', reply_markup=menu_markup)
            return
        s = f'{cur_loc[4]}\nНаличие у торговцев:\n\n'
        to_buy = ReplyKeyboardMarkup()
        for where_i in items:
            i = get_item(where_i[0])[0]
            s += i[1] + f' за {i[2]} монет\n'
            to_buy.add(KeyboardButton(text=i[1]))
        to_buy.add(KeyboardButton(text='Назад'))
        c.execute(f'UPDATE Person SET Stage = "buying" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(s, reply_markup=to_buy)
        return

    if message.text == "Продать":
        cur_loc = get_location(user[11])[0]
        inventory = get_inventory(message.chat.id)
        s = f'{cur_loc[4]}\nМожно продать:\n\n'
        to_sell = ReplyKeyboardMarkup()
        cnt = 0
        for i in inventory:
            item = get_item(i[1])[0]
            c.execute(f'SELECT * from WhereItems WHERE ItemID = {item[0]} AND LocationID = {user[11]}')
            sell_here = c.fetchall()
            if len(sell_here):
                if i[2] - i[3] > 0:
                    cnt += 1
                    to_sell.add(KeyboardButton(text=item[1]))
                    s += item[1] + f' за {item[3]} монет\n'
        if not cnt:
            await message.answer(f'Здесь нечего продать, {user[1]}', reply_markup=menu_markup)
            return
        to_sell.add(KeyboardButton(text='Назад'))
        c.execute(f'UPDATE Person SET Stage = "selling" WHERE UserID = {message.chat.id}')
        conn.commit()
        await message.answer(s, reply_markup=to_sell)
        return


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
conn.commit()
conn.close()
