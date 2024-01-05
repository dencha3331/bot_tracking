from typing import Sequence
from sqlalchemy import create_engine, Select, Update, ScalarResult, Delete
from sqlalchemy import select, update, delete, or_
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from db.models import Admin, Groups, Users, Setting
from logs import logger
# from configs.config import env

engine = create_engine("sqlite+pysqlite:///bot_sqlite.db", echo=True)
# engine = create_engine(f"mysql+pymysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('HOST')}/"
#                        f"{env('DB_NAME')}?charset=utf8mb4", echo=True)


# __________________________________________________________
# _____________________ Users ______________________________
# __________________________________________________________

def update_user_by_nickname(user_nick: str, **value) -> None:
    """Обновить данные пользователя по telegram UserName"""
    stmt: Update = update(Users).where(Users.nickname == user_nick).values(value)
    logger.debug(f"crud.update_user({stmt})")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def update_ban_user(user_id: int, value) -> None:
    """Обновить данные пользователя по telegram id"""
    stmt: Update = update(Users).where(Users.id == user_id).values(value)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def update_user_by_id(user_id: int, **value) -> None:
    """Обновить данные пользователя по telegram id"""
    stmt: Update = update(Users).where(Users.tg_id == user_id).values(value)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_user_by_id_or_nick(tg_id: int = 12, nick: str = '') -> Users | None:
    """Получить пользователя с бд по telegram id или UserName
    возвращает объект Users или None"""
    stmt: Select = select(Users).where(or_(Users.nickname == nick, Users.tg_id == tg_id))
    with Session(engine) as session:
        result: ScalarResult = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def get_all_user() -> Sequence[Users]:
    """Получить всех пользователей с бд возвращает последовательность объектов Users"""
    stmt: Select = select(Users).order_by(Users.nickname).order_by(Users.first_name)
    logger.debug(f"get_all_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result: ScalarResult = session.scalars(stmt)
        return result.all()


def delete_user_by_id(tg_id) -> None:
    """Удаление пользователя по telegram id"""
    stmt: Delete = delete(Users).where(Users.tg_id == tg_id)
    logger.debug(f"delete_user_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


# __________________________________________________
# ______________ Groups ____________________________
# __________________________________________________
def del_group(chat_id) -> None:
    """Удалить группу в бд по telegram id группы"""
    stmt: Delete = delete(Groups).where(Groups.id == chat_id)
    logger.debug(f"del_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_list_groups() -> list[Groups]:
    """Получить все группы с бд возвращает последовательность объектов Groups"""
    stmt: Select = select(Groups).order_by(Groups.nickname)
    logger.debug(f"get_list_groups in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result: ScalarResult = session.scalars(stmt)
        session.commit()
        res = [group for group in result.all()]
        return res


def get_group_by_title_or_id(group_title: str = '', group_id: int = 2) -> Groups | None:
    """Получить группу с бд по telegram chat.title или chat.id возвращает объект Groups иди None"""
    stmt: Select = select(Groups).where(or_(Groups.nickname == group_title, Groups.id == group_id))
    with Session(engine) as session:
        result: ScalarResult = session.scalars(stmt)
        session.commit()
        try:
            return result.one()
        except NoResultFound:
            return


def get_links_for_user() -> str:
    """Получить строку со списком групп со ссылками на них по одной на строку"""
    stmt: Select = select(Groups).order_by(Groups.nickname)
    logger.debug(f"get_links_for_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        all_group_str: str = '\n'.join([f"{group.nickname}\t{group.link_chat}"
                                        for group in session.scalars(stmt)])
        session.commit()
    return all_group_str


def get_news_or_not_group_id_name(news: bool) -> dict[str, str]:
    """Получить список новостных или не новостных групп
    возвращает словарь ключ id группы значение название"""
    stmt: Select = select(Groups).where(Groups.news_group.is_(news)).order_by(Groups.nickname)
    logger.debug(f"get_name_id_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        dict_group: dict[str, str] = {str(group.id): group.nickname for group in session.scalars(stmt)}
        session.commit()
    return dict_group


def update_group_by_id(group_id: int, param) -> None:
    """Обновить данные группы по id принимает словарь со значениями"""
    stmt = update(Groups).where(Groups.id == group_id).values(param)
    logger.debug(f"update_group_status in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


# __________________________________________________
# ______________ Admin _____________________________
# __________________________________________________
def get_list_admins_ids() -> list[int]:
    """Получить список с telegram id администраторов бота"""
    stmt: Select = select(Admin)
    logger.debug(f"get_list_admins in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        admins: ScalarResult = session.scalars(stmt)
        list_admins: list[int] = [admin.id for admin in admins]
        session.commit()
    return list_admins


def get_admin_by_id(admin_id: int) -> Admin | None:
    """Получить объект Admin по telegram id"""
    stmt: Select = select(Admin).where(Admin.id == admin_id)
    logger.debug(f"get_admin_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result: ScalarResult = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def del_admins_by_id(param) -> None:
    """Удалить админа бота по telegram id"""
    stmt: Delete = delete(Admin).where(Admin.id == param)
    logger.debug(f"del_admins_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


# _______________________________________________________
# _________________ Others ______________________________
# _______________________________________________________
def get_settings() -> Setting:
    """Получить настройки бота с бд"""
    stmt: Select = select(Setting)
    with Session(engine) as session:
        res: ScalarResult = session.scalars(stmt)
        session.commit()
        return res.first()


def add_object(obj) -> None:
    """Добавить объект в бд"""
    logger.debug(f"add_object in crud.py obj: {obj}")
    with Session(engine) as session:
        session.add(obj)
        session.commit()

