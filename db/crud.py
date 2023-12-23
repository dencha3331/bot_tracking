from typing import Sequence, List

from sqlalchemy import TextClause, text, create_engine, ScalarResult
from sqlalchemy import func, select, update, delete, Update, Select, or_
from sqlalchemy.exc import NoResultFound, IntegrityError, PendingRollbackError
from sqlalchemy.orm import Session

from configs.config import env
from db.models import Admin, Groups, Users, Setting
from logs import logger

engine = create_engine("sqlite+pysqlite:///bot_sqlite.db", echo=True)
# engine = create_engine(f"mysql+pymysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('HOST')}/"
#                        f"{env('DB_NAME')}?charset=utf8mb4", echo=True)


# __________________________________________________________
# _____________________ Users ______________________________
# __________________________________________________________
# def save_pay_user(user: str) -> bool:
#     logger.debug(f"save_pay_user in crud.py")
#     # try:
#     user_obj = Users(nickname=user, pay=True)
#     with Session(engine) as session:
#         session.add(user_obj)
#         session.commit()
#     logger.debug(f"save_pay_user in crud.py return True")
#     return True
#     # except IntegrityError:
#     #     logger.debug(f"save_pay_user in crud.py return False")
#     #     return False


def update_user_by_nickname(user_nick: str, **value) -> None:
    """Обновить данные пользователя по telegram UserName"""
    stmt = update(Users).where(Users.nickname == user_nick).values(value)
    logger.debug(f"crud.update_user({stmt})")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def update_user_by_id(user_id: int, value) -> None:
    """Обновить данные пользователя по telegram id"""
    stmt = update(Users).where(Users.id == user_id).values(value)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


# def get_user_for_nickname(user_nick: str) -> Users | None:
#     # stmt = select(Users).where(Users.nickname == user_nick or Users.tg_id == 1)
#     stmt = select(Users).where(Users.nickname == user_nick)
#     logger.debug(f"get_user_for_nickname in crud.py, stmt:\n {stmt}")
#     with Session(engine) as session:
#         result = session.scalars(stmt)
#         try:
#             return result.one()
#         except NoResultFound:
#             return
#
#
# def get_user_by_id(tg_id: int) -> Users:
#     stmt = select(Users).where(Users.tg_id == tg_id)
#     logger.debug(f"get_user_by_id in crud.py, stmt:\n {stmt}")
#     with Session(engine) as session:
#         result = session.scalars(stmt)
#         session.commit()
#         return result.one()


def get_user_by_id_or_nick(tg_id: int = 12, nick: str = '') -> Users | None:
    """Получить пользователя с бд по telegram id или UserName
    возвращает объект Users или None"""
    stmt = select(Users).where(or_(Users.nickname == nick, Users.tg_id == tg_id))
    with Session(engine) as session:
        result = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def get_all_user() -> Sequence[Users]:
    """Получить всех пользователей с бд возвращает последовательность объектов Users"""
    stmt = select(Users).order_by(Users.nickname).order_by(Users.first_name)
    logger.debug(f"get_all_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        return result.all()


def delete_user_by_id(tg_id):
    """Удаление пользователя по telegram id"""
    stmt = delete(Users).where(Users.tg_id == tg_id)
    logger.debug(f"delete_user_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


# __________________________________________________
# ______________ Groups ____________________________
# __________________________________________________
def del_group(chat_id) -> None:
    """Удалить группу в бд по telegram id группы"""
    stmt = delete(Groups).where(Groups.id == chat_id)
    logger.debug(f"del_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_list_groups() -> Sequence[Groups]:
    """Получить все группы с бд возвращает последовательность объектов Groups"""
    stmt = select(Groups).order_by(Groups.nickname)
    logger.debug(f"get_list_groups in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        return result.all()


def get_group_by_title_or_id(group_title: str = '', group_id: int = 2) -> Groups | None:
    """Получить группу с бд по telegram chat.title или chat.id возвращает объект Groups иди None"""
    stmt = select(Groups).where(or_(Groups.nickname == group_title, Groups.id == group_id))
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        try:
            return result.one()
        except NoResultFound:
            return


def get_links_for_user() -> str:
    """Получить строку со списком групп со ссылками на них по одной на строку"""
    stmt = select(Groups).order_by(Groups.nickname)
    logger.debug(f"get_links_for_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        all_group_str: str = '\n'.join([f"{group.nickname}\t{group.link_chat}"
                                        for group in session.scalars(stmt)])
        session.commit()
    return all_group_str


def get_news_or_not_group_id_name(news: bool) -> dict:
    """Получить список новостных или не новостных групп
    возвращает словарь ключ id группы значение название"""
    stmt = select(Groups).where(Groups.news_group.is_(news)).order_by(Groups.nickname)
    logger.debug(f"get_name_id_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        dict_group = {str(group.id): group.nickname for group in session.scalars(stmt)}
        session.commit()
    return dict_group


def update_group_by_id(group_id: int, param) -> None:
    """Обновить данные группы по id принимает словарь со значениями"""
    stmt = update(Groups).where(Groups.id == group_id).values(param)
    logger.debug(f"update_group_status in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


#
# def get_name_id_group() -> dict:
#     stmt = select(Groups).order_by(Groups.nickname)
#     logger.debug(f"get_name_id_group in crud.py, stmt:\n {stmt}")
#     with Session(engine) as session:
#         dict_group = {str(group.id): group.nickname for group in session.scalars(stmt)}
#         session.commit()
#     return dict_group
#
#
# def update_group_link(group_id: int, **param) -> bool:
#     stmt = update(Groups).where(Groups.id == group_id).values(param)
#     logger.debug(f"update_group_link in crud.py, stmt:\n {stmt}")
#     try:
#         with Session(engine) as session:
#             session.execute(stmt)
#             session.commit()
#         return True
#     except Exception as e:
#         print(e)
#         return False
#

# __________________________________________________
# ______________ Admin _____________________________
# __________________________________________________
def get_list_admins_ids() -> list[int]:
    """Получить список с telegram id администраторов бота"""
    stmt = select(Admin)
    logger.debug(f"get_list_admins in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        admins = session.scalars(stmt)
        list_admins = [admin.id for admin in admins]
        session.commit()
    return list_admins


def get_admin_by_id(admin_id: int) -> Admin | None:
    """Получить объект Admin по telegram id"""
    stmt = select(Admin).where(Admin.id == admin_id)
    logger.debug(f"get_admin_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def del_admins_by_id(param) -> None:
    """Удалить админа бота по telegram id"""
    stmt = delete(Admin).where(Admin.id == param)
    logger.debug(f"del_admins_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


#
# def add_admins_by_id(users_id: int) -> None:
#     admin: Admin = Admin(id=users_id)
#     with Session(engine) as session:
#         session.add(admin)
#         session.commit()
#

# _______________________________________________________
# _________________ Others ______________________________
# _______________________________________________________
def get_settings() -> Setting:
    """Получить настройки бота с бд"""
    stmt = select(Setting)
    with Session(engine) as session:
        res = session.scalars(stmt)
        session.commit()
        return res.first()


def add_object(obj) -> None:
    """Добавить объект в бд"""
    logger.debug(f"add_object in crud.py obj: {obj}")
    with Session(engine) as session:
        session.add(obj)
        session.commit()

