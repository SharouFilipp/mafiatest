import sqlite3
import random
from typing import Literal, Callable
from functools import wraps

def with_db_connection(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        con = sqlite3.connect("db.db")
        cur = con.cursor()
        try:
            result = func(cur, *args, **kwargs)
            con.commit()
        except Exception as e:
            con.rollback()
            print(f"ОШИБКА: {e}")
        finally:
            con.close()
        return result
    return wrapper  

@with_db_connection
def create_tables(cur):
    # Подключаемся к базе данных (если файла нет, он будет создан)
    #con = sqlite3.connect("db.db")
    # Создаем курсор для выполнения SQL-запросов
    #cur = con.cursor()
    # Выполняем SQL-запрос для создания таблицы "players", если она не существует
    cur.execute("""
    CREATE TABLE IF NOT EXISTS players(
        player_id INTEGER,         
        username TEXT,              
        role TEXT,                  
        mafia_vote INTEGER,         
        citizen_vote INTEGER,       
        voted INTEGER,              
        dead INTEGER                
    )""")
    # Сохраняем изменения в базе данных
    #con.commit()
    # Закрываем соединение с базой данных
    #con.close()
@with_db_connection
def insert_player(cur,player_id: int, username: str) -> None:
    # SQL-запрос для добавления нового игрока в таблицу
    sql = "INSERT INTO players (player_id, username, mafia_vote, citizen_vote, voted, dead) \
        VALUES (?, ?, ?, ?, ?, ?)"
    # Выполняем запрос, вставляем игрока с начальными значениями для голосов, голосования и состояния (жив/мертв)
    cur.execute(sql, (player_id, username, 0, 0, 0, 0))

def players_amount() -> int:
    # Подключаемся к базе данных
    con = sqlite3.connect("db.db")
    # Создаем курсор для выполнения SQL-запросов
    cur = con.cursor()
    # SQL-запрос для получения всех строк из таблицы игроков
    sql = "SELECT * FROM players"
    # Выполняем запрос
    cur.execute(sql)
    # Получаем все строки результата
    res = cur.fetchall()
    # Закрываем соединение с базой данных
    con.close()
    # Возвращаем количество игроков (длина списка результатов)
    return len(res)
 
def get_mafia_usernames() -> str:
    # Подключаемся к базе данных
    con = sqlite3.connect("db.db")
    # Создаем курсор для выполнения SQL-запросов
    cur = con.cursor()
    # SQL-запрос для получения имен пользователей, у которых роль "мафия"
    sql = "SELECT username FROM players WHERE role = 'mafia'"
    # Выполняем запрос
    cur.execute(sql)
    # Получаем все строки результата
    data = cur.fetchall()
    # Инициализируем строку для имен мафии
    names = ""
    # Перебираем полученные строки
    for row in data:  # Пример данных: [("asdasdas",), ("sdasadsad",), ]
        name = row[0]  # Извлекаем имя из кортежа
        names += name + "\n"  # Добавляем имя в итоговую строку с новой строки
    # Закрываем соединение с базой данных
    con.close()
    # Возвращаем строку с именами мафии
    return names
 
def get_players_roles() -> list:
    # Подключаемся к базе данных
    con = sqlite3.connect("db.db")
    # Создаем курсор для выполнения SQL-запросов
    cur = con.cursor()
    # SQL-запрос для получения ID игроков и их ролей
    sql = "SELECT player_id, role FROM players"
    # Выполняем запрос
    cur.execute(sql)
    # Получаем все строки результата
    data = cur.fetchall()
    # Закрываем соединение с базой данных
    con.close()
    # Возвращаем список с данными (ID игрока и его роль)
    return data

def get_all_alive()-> list[str]:
    con =  sqlite3.connect("db.db")
    cur = con.cursor()
    sql = "SELECT username FROM players WHERE dead=0"
    cur.execute(sql)
    data = cur.fetchall()
    data = [row[0] for row in data]
    con.close()
    return data

def set_roles(players:int) ->None:
    game_roles = ["citizen"] * players
    mafias = int(players * 0.3)
    for i in range(mafias):
        game_roles[i] = "mafia"
    random.shuffle(game_roles)
    con =  sqlite3.connect("db.db")
    cur = con.cursor()
    sql = "SELECT player_id FROM players"
    cur.execute(sql)
    players_id = cur.fetchall()
    for role, player_id in zip(game_roles, players_id):
        sql = "UPDATE players SET role=? WHERE player_id=?"
        cur.execute(sql, (role, player_id[0]))
    con.commit()
    con.close()    

def vote(type: Literal['mafia_vote', 'citizen_vote'], username: str, player_id: int) -> bool:
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT username FROM players WHERE player_id=? AND dead=0 AND voted=0", (player_id,))
    can_vote = cur.fetchone()
    if can_vote:
        cur.execute(f"UPDATE players SET {type} = {type} + 1 WHERE username=?",(username,))
        con.execute(f"UPDATE players SET voted=1 WHERE player_id=?",(player_id,))
        con.commit()
        con.close()
        return True
    con.close()
    return False

def mafia_kill() -> str:
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT MAX(mafia_vote) FROM players")
    max_votes= cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE dead=0 AND role='mafia' ")
    mafia_alive = cur.fetchone()[0]
    username_killed = "никого"
    if max_votes == mafia_alive:
        cur.execute("SELECT username FROM players WHERE mafia_vote=?", (max_votes,))
        username_killed = cur.fetchone()[0]
        cur.execute("UPDATE players SET dead=1 WHERE username=?",(username_killed,))
        con.commit()
    con.close()
    return username_killed    


def citizen_kill() -> str:
    con = sqlite3.connect("db.db")
    cur = con.cursor()
    cur.execute("SELECT MAX(citizen_vote) FROM players")
    max_votes= cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE citizen_vote=?",(max_votes,))
    max_count = cur.fetchone()[0]
    username_killed = "никого"
    if max_count == 1:
        cur.execute("SELECT username FROM players WHERE citizen_vote=?", (max_votes,))
        username_killed = cur.fetchone()[0]
        cur.execute("UPDATE players SET dead=1 WHERE username=?",(username_killed,))
        con.commit()
    con.close()
    return username_killed   


@with_db_connection
def check_winner(cur) -> str | None:
    cur.execute("SELECT COUNT(*) FROM players WHERE role='mafia' and dead=0 ")
    mafia_alive = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM players WHERE role!='mafia' and dead=0")
    citizen_alive = cur.fetchone()[0]
    if mafia_alive >= citizen_alive:
        return "Мафия"
    elif mafia_alive == 0:
        return "Горожане"
    return None


@with_db_connection
def clear(cur, dead: bool=False) -> None:
    sql = "UPDATE players SET citizen_vote=0, mafia_vote=0, voted=0"
    if dead:
        sql += ", dead=0"
    cur.execute(sql)


if __name__ == "__main__":
    create_tables()  # Создание таблицы (можно раскомментировать, чтобы создать таблицу)
    #insert_player(1, "Филипп")  # Добавление игрока с ID 1 и именем "Артём"
    #insert_player(124121, "fhdhd")
    #insert_player(3, "f")
    #insert_player(4, "d")
    #insert_player(5, "s")
    #insert_player(6, "a")
    #print(get_all_alive())
    #set_roles(players_amount())
    #print(players_amount())  # Вывод количества игроков
    #print(get_mafia_usernames())  # Вывод имен игроков, являющихся мафией
    #print(get_players_roles())  # Вывод ролей всех игроков
    #mafia_kill()
    #print(vote("mafia_vote", "Филипп", 2))
    #print(citizen_kill())
    #print(check_winner())
    print(clear())
    