import sqlite3
from math import sqrt

conn = sqlite3.connect('game.db')

c = conn.cursor()

'''
Удалять вовсе не обязательно. Мне так удобней тестировать
'''
c.execute("DROP TABLE IF EXISTS Person") 
c.execute("DROP TABLE IF EXISTS Inventory")
c.execute("DROP TABLE IF EXISTS Items")
c.execute("DROP TABLE IF EXISTS Locations")
c.execute("DROP TABLE IF EXISTS Distance")
c.execute("DROP TABLE IF EXISTS WhereItems")

c.execute("""CREATE TABLE Person (
    UserID text,
    Nickname text,
    Level int,
    HP int,
    CurHP int,
    Money int,
    Attack int,
    MagicAttack int,
    XP int,
    Armour int,
    MagicArmour int,
    LocationID text,
    Stage text,
    ActionAllowedTime int)""")

c.execute("""CREATE TABLE Inventory (
    UserID text,
    ItemID text,
    quantity int,
    flag int)""")

c.execute("""CREATE TABLE Items (
    ItemID text,
    ItemName text,
    Cost int,
    CostToSale int,
    ItemType text,
    HP int, 
    Mana int,
    Attack int,
    MagicAttack int,
    Armour int,
    MagicArmour int,
    ReqLevel int
    )""")

c.execute("""CREATE TABLE Locations (
    LocationID text,
    XCoord int,
    YCoord int,
    LocationType text,
    LocationName text
    )""")

c.execute("""CREATE TABLE Distance (
    LocationFromID text,
    LocationToID text,
    Dist int
    )""")

c.execute("""CREATE TABLE WhereItems (
    ItemID text,
    LocationID text,
    ItemName text
    )""")

items = [(0, 'Рубаха странника', 0, 0, 'armor', 0, 0, 0, 0, 3, 0, 1),
         (1, 'Ботинки', 0, 0, 'boots', 0, 0, 0, 0, 2, 0, 1),
         (2, 'Зелье зарождения магии', 4, 1, 'potion', 0, 20, 0, 20, 1, 5, 2),
         (3, 'Отвар спасания', 0, 0, 'potion', 15, 0, 0, 0, 0, 0, 1),

         (4, 'Стальной меч мастера Гаардрика', 20, 14.4, 'weapon', 10, 0, 30, 0, 20, 0, 1),
         (5, 'Улучшенный стальной мастера Гаардрика', 25, 1.25, 'weapon', 15, 10, 30, 10, 20, 10, 3),
         (6, 'Обсидиановый меч короля Гномов', 130, 54, 'weapon', 20, 10, 180, 17, 0, 10, 8),
         (7, 'Гархвардская кираса', 20, 15.4, 'armor', 30, 0, 0, 0, 35, 40, 1),

         (8, 'Ивовый лук', 27, 9.0, 'weapon', 35, 0, 15, 17, 0, 0, 4),
         (9, 'Слеза Древа жизни', 14, 0.0, 'potion', 70, 0, 0, 0, 0, 0, 1),
         (10, 'Доспех Ласточки', 40, 35.6, 'armor', 0, 12, 0, 5, 10, 25, 5),

         (11, 'Булава шамана степи', 35, 33.0, 'weapon', 0, 23, 15, 13, 0, 0, 10),

         (12, 'Мантия невидимка', 100, 23.0, 'armor', 0, 100, 0, 100, 0, 100, 1),

         (13, 'Яд арахнида', 5, 2.4, 'potion', -10, 0, 20, 20, 0, 0, 1),
         (14, 'Отвар Экизмара', 10, 5.2, 'potion', 0, 50, 0, 0, 0, 10, 1)]

c.executemany("INSERT INTO Items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", items)

where_items = [(0, 0, 'Рубаха странника'), (1, 0, 'Ботинки'), (2, 0, 'Зелье зарождения магии'),
               (3, 0, 'Отвар спасения'), (4, 1, 'Стальной меч мастера Гаардрика'),
               (5, 1, 'Улучшенный стальной мастера Гаардрика'), (6, 1, 'Обсидиановый меч короля Гномов'),
               (7, 1, 'Гархвардская кираса'), (8, 7, 'Ивовый лук'), (9, 7, 'Слеза Древа жизни'), (10, 7, 'Доспех Ласточки'), (11, 2, 'Булава шамана степи'),
               (12, 6, 'Мантия невидимка'), (13, 0, 'Яд арахнида'), (14, 6, 'Отвар Экизмара')]


def add_distance(from_id: str, to_id: str):
    c.execute(f'SELECT * from Locations WHERE LocationID = {from_id}')
    loc_from = c.fetchall()
    c.execute(f'SELECT * from Locations WHERE LocationID = {to_id}')
    loc_to = c.fetchall()
    if not len(loc_from) or not len(loc_to):
        raise sqlite3.Error
    dist = sqrt((loc_to[0][1] - loc_from[0][1]) ** 2 + (loc_to[0][2] - loc_from[0][2]) ** 2)
    c.execute("INSERT INTO Distance VALUES (?, ?, ?)", [from_id, to_id, dist])


locations = [(0, 0, 0, 'town', 'Столица'), (1, 3, 5, 'town', 'Гномий Хребет'),
             (2, -3, -6, 'town', 'Орочья Степь'), (3, 4, 5, 'dungeon', 'Паучье Гнездо'),
             (4, -4, -8, 'dungeon', 'Харшинский алтарь Безымянному богу'),
             (5, 8, -5, 'town', 'Порт'), (6, 7, -9, 'town', 'Драконья Империя'),
             (7, 5, -17, 'town', 'Эльфийское Княжество')]


c.executemany("INSERT INTO Locations VALUES (?, ?, ?, ?, ?)", locations)
c.executemany("INSERT INTO WhereItems VALUES (?, ?, ?)", where_items)

for i in range(0, len(locations)):
    for j in range(i + 1, len(locations)):
        add_distance(locations[i][0], locations[j][0])


def add_user(chat_id: int, name: str) -> None:
    """Добавить пользователя в БД
    Args:
        chat_id (int): chat_id из API telegram
        name (str): name
    Default Person:
    Level 1
    HP 100
    CurHP 100
    Money 50
    Attack 5
    MagicAttack 0
    XP 0
    Armour 0
    MagicArmour 0
    LocationID '0'

    Default Inventory:
    ItemID 0,
    quantity 1,
    flag 1
    """
    c.execute(f'DELETE from Person WHERE UserID = "{chat_id}"')
    c.execute(f'DELETE from Inventory WHERE UserID = "{chat_id}"')

    c.execute("INSERT INTO Person VALUES (?, ?, 1, 100, 100, 50, 5, 0, 0, 3, 0, 0, 'new', 0)", [chat_id, name])
    c.execute("INSERT INTO Inventory VALUES (?, 0, 1, 1)", [chat_id])
    c.execute("INSERT INTO Inventory VALUES (?, 1, 1, 0)", [chat_id])
    c.execute("INSERT INTO Inventory VALUES (?, 3, 3, 0)", [chat_id])

    conn.commit()


def get_user(chat_id: str):
    c.execute(f'SELECT * from Person WHERE UserID = {chat_id}')
    user = c.fetchall()
    if len(user):
        # print(user)
        return user
    raise sqlite3.Error


def get_inventory(chat_id: str):
    c.execute(f'SELECT * from Inventory WHERE UserID = {chat_id}')
    inv = c.fetchall()
    if len(inv):
        return inv
    raise sqlite3.Error


def get_item(item_id: str):
    c.execute(f'SELECT * from Items WHERE ItemID = {item_id}')
    item = c.fetchall()
    if len(item):
        return item
    raise sqlite3.Error


def get_location(loc_id: str):
    c.execute(f'SELECT * from Locations WHERE LocationID = {loc_id}')
    loc = c.fetchall()
    if len(loc):
        return loc
    raise sqlite3.Error


def get_distance(from_id: str, to_id: str):
    c.execute(
        f'SELECT * from Distance WHERE (LocationFromID = {from_id} AND LocationToID = {to_id}) OR (LocationFromID = {to_id} AND LocationToID = {from_id})')
    distance = c.fetchall()
    if len(distance):
        return distance[0][2]
    raise sqlite3.Error

conn.commit()

conn.close()
