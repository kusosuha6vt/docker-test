import os
import psycopg
from psycopg import connection
import random
from prettytable import PrettyTable
import uuid

# psycopg.extras.register_uuid()


def prompt(arg, default=False, tp=str, check=None):
    s = input(f"Введите {arg}:\n> ")
    if default and s == "":
        return None
    res = tp(s)
    if check is not None and not check(res):
        raise Exception("Поле не соответствует требованиям")
    return res


class Ship:
    ship_type = ["cruiser", "icebreaker", "ferry", "fishing boat"]

    def __init__(self):
        self.id = None
        self.name = None
        self.year = None
        self.flag = None
        self.tp = None

    def read(default=False):
        ship = Ship()
        if default:
            print(
                "Введите информацию про корабль или нажмите enter, если не хотите обновлять поле"
            )
            ship.id = prompt(
                "id", False, int, lambda x: x in range(int(1e8), int(1e9) - 1)
            )
        ship.name = prompt("имя корабля", default)
        ship.year = prompt(
            "год корабля", default, int, lambda x: x in range(1500, 3000)
        )
        ship.flag = prompt("флаг корабля", default)
        print("Введите тип корабля (индекс). Возможные типы:")
        for i, el in enumerate(Ship.ship_type):
            print(f"{i}) {el}")
        tp = prompt(
            "тип корабля", default, int, lambda x: x in range(len(Ship.ship_type))
        )
        ship.tp = None if tp is None else Ship.ship_type[tp]
        return ship

    def insert(self, conn: connection):
        self.id = random.randint(int(1e8), int(1e9) - 1)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ships(id, name, year, flag, type, dock_id) VALUES (%s, %s, %s, %s, %s, %s);",
                (self.id, self.name, self.year, self.flag, self.tp, None),
            )

    def update(self, conn: connection):
        args = []
        s = []
        if self.name is not None:
            s.append("name=%s")
            args.append(self.name)
        if self.year is not None:
            s.append("year=%s")
            args.append(self.year)
        if self.flag is not None:
            s.append("flag=%s")
            args.append(self.flag)
        if self.tp is not None:
            s.append("type=%s")
            args.append(self.tp)
        if len(args) == 0:
            return
        s = ", ".join(s)
        s += " WHERE id=%s;"
        args.append(self.id)
        with conn.cursor() as cur:
            cur.execute(f"UPDATE ships SET {s}", args)

    def get_all(conn: connection):
        with conn.cursor() as cur:
            x = PrettyTable()
            x.field_names = ["id", "Имя", "Год", "Флаг", "Тип", "id причала"]
            cur.execute("SELECT id, name, year, flag, type, dock_id FROM ships;")
            for ls in cur.fetchall():
                x.add_row(ls)
            print(x)

    def delete(conn: connection):
        id = prompt("id корабля", False, int)
        with conn.cursor() as cur, conn.transaction():
            cur.execute("SELECT dock_id FROM ships WHERE id=%s;", (id,))
            dock_id = cur.fetchall()
            if len(dock_id) != 1:
                print("Такого корабля не существует")
                return
            dock_id = dock_id[0][0]
            if dock_id is not None:
                print("Корабль пришвартован: невозможно удалить")
            cur.execute("DELETE FROM ships WHERE id = %s RETURNING id;", (id,))
            print(f"Удалено {len(cur.fetchall())}")


class Dock:
    def __init__(self):
        self.id = None
        self.name = None
        self.lat = None
        self.lon = None
        self.max_ships = None

    def get_all(conn: connection, only_available=False) -> int:
        ans = 0
        with conn.cursor() as cur:
            x = PrettyTable()
            x.field_names = [
                "id",
                "Название",
                "Широта",
                "Долгота",
                "Вместимость",
                "Кораблей",
            ]
            cond = ""
            if only_available:
                cond = " WHERE max_ships > cur_ships"
            cur.execute(
                f"SELECT id, name, latitude, longitude, max_ships, cur_ships FROM docks{cond};"
            )
            for ls in cur.fetchall():
                x.add_row(ls)
                ans += 1
            print(x)
        return ans

    def read(default=False):
        dock = Dock()
        if default:
            print(
                "Введите информацию про причал или нажмите enter, если не хотите обновлять поле"
            )
            dock.id = prompt("uuid причала", False, uuid.UUID)
        dock.name = prompt("имя причала", default)
        dock.lat = prompt("широту", default)
        dock.lon = prompt("долготу", default)
        if not default:
            dock.max_ships = prompt(
                "макс. количество кораблей", default, int, lambda x: x >= 0
            )
        return dock

    def insert(self):
        self.id = uuid.uuid4()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO docks(id, name, latitude, longitude, max_ships, cur_ships) VALUES (%s, %s, %s, %s, %s, %s);",
                (self.id, self.name, self.lat, self.lon, self.max_ships, 0),
            )

    def update(self, conn):
        s = []
        a = []
        if self.name is not None:
            a.append(self.name)
            s.append("name=%s")
        if self.lat is not None:
            a.append(self.lat)
            s.append("latitude=%s")
        if self.lon is not None:
            a.append(self.lon)
            s.append("longitude=%s")
        if len(s) == 0:
            return
        s = ", ".join(s)
        s += " WHERE id=%s"
        a.append(self.id)
        print(s)
        print(a)
        with conn.cursor() as cur:
            cur.execute(f"UPDATE docks SET {s};", a)

    def delete(conn: connection):
        print(
            "Вы хотите удалить причал. Все пришвартованные корабли автоматически отшвартуются."
        )
        id = prompt("id причала", False, uuid.UUID)
        with conn.cursor() as cur, conn.transaction():
            cur.execute("UPDATE ships SET dock_id = NULL WHERE dock_id = %s", (id,))
            cur.execute("DELETE FROM docks WHERE id = %s RETURNING id;", (id,))
            print(f"Удалено {len(cur.fetchall())}")


def print_help():
    print(
        """
    Команды:
      help       для вывода этого сообщения
      clear      для сброса базы данных
      exit       для выхода
      ship
          list     для вывода кораблей
          add      для добавления судна
          upd      для обновления информации о судне
          del      для удаления судна
      dock
          add      для добавления причала
          list     для вывода причалов
          upd      для обновления информации о причале
          del      для удаления причала
      moor
          from     для отбывающего судна
          to       для прибывающего судна
    """
    )


def clear(conn: connection):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE ships; TRUNCATE TABLE docks;")


def add_ship(conn: connection):
    ship = Ship.read()
    ship.insert(conn)
    print("Успешно")


def update_ship(conn: connection):
    ship = Ship.read(True)
    ship.update(conn)
    print("Успешно")


def parse_ship(command, conn):
    if len(command) != 1:
        print("Неверная команда")
        return
    if command[0] == "add":
        add_ship(conn)
    elif command[0] == "list":
        Ship.get_all(conn)
    elif command[0] == "upd":
        update_ship(conn)
    elif command[0] == "del":
        Ship.delete(conn)
    else:
        print("Неверная команда")


def add_dock(conn: connection):
    dock = Dock.read()
    dock.insert()
    print("Успешно")


def update_dock(conn: connection):
    dock = Dock.read(True)
    dock.update(conn)
    print("Успешно")


def moor_from(conn: connection):
    print("Вы собираетесь отшвартавать корабль")
    ship_id = prompt(
        "id корабля", False, int, lambda x: x in range(int(1e8), int(1e9) - 1)
    )
    with conn.cursor() as cur, conn.transaction():
        cur.execute("SELECT dock_id FROM ships WHERE id=%s;", (ship_id,))
        cur_dock_id = cur.fetchall()
        if len(cur_dock_id) == 0:
            print("Корабля не существует")
            return
        cur_dock_id = cur_dock_id[0][0]
        if cur_dock_id is None:
            print("Корабль уже не пришвартован")
            return
        cur.execute("UPDATE ships SET dock_id=NULL WHERE id=%s;", (ship_id,))
        cur.execute(
            "UPDATE docks SET cur_ships=(cur_ships - 1) WHERE id=%s;", (cur_dock_id,)
        )
        print("Успешно")


def moor_to(conn: connection):
    print("Вы собираетесь пришваратавать корабль")
    ship_id = prompt(
        "id корабля", False, int, lambda x: x in range(int(1e8), int(1e9) - 1)
    )
    dock_id = prompt("uuid причала", False, uuid.UUID)
    with conn.cursor() as cur, conn.transaction():
        cur.execute("SELECT dock_id FROM ships WHERE id=%s;", (ship_id,))
        cur_dock_id = cur.fetchall()
        if len(cur_dock_id) == 0:
            print("Корабля не существует")
            return
        cur_dock_id = cur_dock_id[0][0]
        if cur_dock_id is not None:
            print("Корабль уже пришвартован")
            return
        cur.execute("SELECT cur_ships, max_ships FROM docks WHERE id=%s;", (dock_id,))
        ships = cur.fetchall()
        if len(ships) != 1:
            print("Ошибка программы")
            return
        cur_ships, max_ships = ships[0]
        if cur_ships >= max_ships:
            print("Не могу пришвартовать: причал переполнен")
            return
        cur.execute("UPDATE ships SET dock_id=%s WHERE id=%s;", (dock_id, ship_id))
        cur.execute(
            "UPDATE docks SET cur_ships=(cur_ships + 1) WHERE id=%s;", (dock_id,)
        )
        print("Успешно")


def parse_dock(command, conn):
    if len(command) != 1:
        print("Неверная команда")
        return
    if command[0] == "add":
        add_dock(conn)
    elif command[0] == "list":
        s = prompt(
            "y/n, нужно ли выводить только свободные причалы",
            False,
            str,
            lambda x: x in ("y", "n"),
        )
        Dock.get_all(conn, s == "y")
    elif command[0] == "upd":
        update_dock(conn)
    elif command[0] == "del":
        Dock.delete(conn)
    else:
        print("Неверная команда")


def parse_moor(command, conn):
    if len(command) != 1:
        print("Неверная команда")
        return
    if command[0] == "from":
        moor_from(conn)
    elif command[0] == "to":
        moor_to(conn)
    else:
        print("Неверная команда")


def parse_command(command, conn):
    try:
        match command[0]:
            case "help":
                print_help()
            case "clear":
                clear(conn)
            case "ship":
                parse_ship(command[1:], conn)
            case "dock":
                parse_dock(command[1:], conn)
            case "moor":
                parse_moor(command[1:], conn)
            case _:
                print("Неверная команда")
    except Exception as e:
        print(e)
        print("Операция отменена")


def main(conn):
    print("Это приложения для обработки кораблей и причалов.")
    print_help()
    while True:
        command = input("> ").split()
        if len(command) == 0:
            continue
        if command[0] == "exit":
            return
        parse_command(command, conn)


try:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    hostname = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_NAME")
    with psycopg.connect(
        dbname=database,
        user=user,
        password=password,
        host=hostname,
        port=port,
        autocommit=True,
    ) as conn:
        main(conn)
except Exception as err:
    print("Ошибка базы данных: ", err)
