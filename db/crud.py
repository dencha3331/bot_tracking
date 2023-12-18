from typing import Sequence, List

from sqlalchemy import TextClause, text, create_engine, ScalarResult
from sqlalchemy import func, select, update, delete, Update, Select
from sqlalchemy.exc import NoResultFound, IntegrityError, PendingRollbackError
from sqlalchemy.orm import Session

from configs.config import env
from db.models import Admin, Groups, Users, Setting
from logs import logger

# engine = create_engine("sqlite+pysqlite:///bot_sqlite.db", echo=True)
engine = create_engine(f"mysql+pymysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('HOST')}/"
                       f"{env('DB_NAME')}?charset=utf8mb4", echo=True)


def get_list_admins() -> list[int]:
    stmt = select(Admin)
    logger.debug(f"get_list_admins in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        admins = session.scalars(stmt)
        list_admins = [admin.id for admin in admins]
        session.commit()
    return list_admins


def save_pay_user(user: str) -> bool:
    logger.debug(f"save_pay_user in crud.py")
    # try:
    user_obj = Users(nickname=user, pay=True)
    with Session(engine) as session:
        session.add(user_obj)
        session.commit()
    logger.debug(f"save_pay_user in crud.py return True")
    return True
    # except IntegrityError:
    #     logger.debug(f"save_pay_user in crud.py return False")
    #     return False


def add_object(obj) -> None:
    logger.debug(f"add_object in crud.py obj: {obj}")
    with Session(engine) as session:
        session.add(obj)
        session.commit()


def del_group(chat_id) -> None:
    stmt = delete(Groups).where(Groups.id == chat_id)
    logger.debug(f"del_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_links_for_user() -> str:
    stmt = select(Groups).order_by(Groups.nickname)
    logger.debug(f"get_links_for_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        all_group_str: str = '\n'.join([f"{group.nickname}\t{group.link_chat}"
                                        for group in session.scalars(stmt)])
        session.commit()
    return all_group_str


def update_user_by_nickname(user_nick: str, **value) -> None:
    stmt = update(Users).where(Users.nickname == user_nick).values(value)
    logger.debug(f"crud.update_user({stmt})")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_name_id_group() -> dict:
    stmt = select(Groups).order_by(Groups.nickname)
    logger.debug(f"get_name_id_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        dict_group = {str(group.id): group.nickname for group in session.scalars(stmt)}
        session.commit()
    return dict_group


def news_or_not_group_id_name(news: bool) -> dict:
    if news:
        stmt = select(Groups).where(Groups.news_group).order_by(Groups.nickname)
    else:
        stmt = select(Groups).where(Groups.news_group.is_(False)).order_by(Groups.nickname)
    logger.debug(f"get_name_id_group in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        dict_group = {str(group.id): group.nickname for group in session.scalars(stmt)}
        session.commit()
    return dict_group

def update_group_link(group_id: int, **param) -> bool:
    stmt = update(Groups).where(Groups.id == group_id).values(param)
    logger.debug(f"update_group_link in crud.py, stmt:\n {stmt}")
    try:
        with Session(engine) as session:
            session.execute(stmt)
            session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def get_user_for_nickname(user_nick: str) -> Users | None:
    stmt = select(Users).where(Users.nickname == user_nick)
    logger.debug(f"get_user_for_nickname in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def get_admin_by_id(admin_id: int) -> Admin | None:
    stmt = select(Admin).where(Admin.id == admin_id)
    logger.debug(f"get_admin_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def add_users_by_nickname(nick: str) -> str:
    user: Users = Users(nickname=nick, pay=True)
    try:
        logger.debug(f"add_users_by_nickname in crud.py try: user: {user}")
        with Session(engine) as session:
            session.add(user)
            session.commit()
    except (PendingRollbackError, IntegrityError):
        with Session(engine) as session:
            stmt = update(Users).where(Users.nickname == nick).values({"pay": True})
            logger.debug(f"except (PendingRollbackError, IntegrityError): "
                         f"add_users_by_nickname in crud.py, stmt:\n {stmt}")
            session.execute(stmt)
            session.commit()
    logger.debug(f"end dd_users_by_nickname in crud.py: {nick} добавлен в оплаченные")
    return f"{nick} добавлен в оплаченные"


def update_group_status(group_id: int, param) -> None:
    stmt = update(Groups).where(Groups.id == group_id).values(param)
    logger.debug(f"update_group_status in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def add_admins_by_id(users_id: int) -> None:
    admin: Admin = Admin(id=users_id)
    with Session(engine) as session:
        session.add(admin)
        session.commit()


def get_list_groups() -> Sequence[Groups]:
    stmt = select(Groups)
    logger.debug(f"get_list_groups in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        return result.all()


def unpay_users_by_nickname(nick) -> str:
    stmt = update(Users).where(Users.nickname == nick).values(pay=False)
    logger.debug(f"unpay_users_by_nickname in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()
    return f"{nick} удален из оплаченных и из групп"


def ban_users(nickname):
    stmt = update(Users).where(Users.nickname == nickname).values(ban=True, pay=False)
    logger.debug(f"ban_users in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def unban_user(nickname):
    stmt = update(Users).where(Users.nickname == nickname).values(ban=False, pay=True)
    logger.debug(f"unban_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_all_user() -> Sequence[Users]:
    stmt = select(Users).order_by(Users.nickname)
    logger.debug(f"get_all_user in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        return result.all()


def get_pay_users() -> list[Users]:
    stmt = select(Users).where(Users.pay.is_(True))
    logger.debug(f"get_pay_users in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        return [user for user in result.all()]


def del_admins_by_id(param) -> None:
    stmt = delete(Admin).where(Admin.id == param)
    logger.debug(f"del_admins_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def insert_user(**values):
    user = Users(**values)
    add_object(user)


def some():
    # user = Users(nickname="den", pay=True)
    # add_object(user)
    # user2 = Users(tg_id=123)
    # add_object(user2)
    user3 = Users(nickname="den", pay=True, tg_id=123)
    try:
        add_object(user3)
    except IntegrityError:
        stmt = delete(Users).where(Users.tg_id == 123)
        with Session(engine) as session:
            session.execute(stmt)
            session.commit()
        update_user_by_nickname("den", tg_id=123)


def delete_user_by_id(tg_id):
    stmt = delete(Users).where(Users.tg_id == tg_id)
    logger.debug(f"delete_user_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def delete_user_by_nicname(user_nick):
    stmt = delete(Users).where(Users.nickname == user_nick)
    logger.debug(f"delete_user_by_nicname in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_user_by_id(tg_id: int) -> Users:
    stmt = select(Users).where(Users.tg_id == tg_id)
    logger.debug(f"get_user_by_id in crud.py, stmt:\n {stmt}")
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        return result.one()


def update_user_by_id(user_id: int, value):
    stmt = update(Users).where(Users.id == user_id).values(value)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_group_by_title(group_title: str) -> Groups | None:
    stmt = select(Groups).where(Groups.nickname == group_title)
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        try:
            return result.one()
        except NoResultFound:
            return


def get_settings():
    stmt = select(Setting)
    with Session(engine) as session:
        res = session.scalars(stmt)
        session.commit()
        return res.one()
