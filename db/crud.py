from typing import Sequence, List

from sqlalchemy import TextClause, text, create_engine, ScalarResult
from sqlalchemy import func, select, update, delete, Update, Select
from sqlalchemy.exc import NoResultFound, IntegrityError, PendingRollbackError
from sqlalchemy.orm import Session

from configs.config import env
from db.models import Admin, Groups, Users

# engine = create_engine("sqlite+pysqlite:///bot_sqlite.db", echo=True)
engine = create_engine(f"mysql+pymysql://{env('DB_USER')}:{env('DB_PASSWORD')}@{env('HOST')}/"
                       f"{env('DB_NAME')}?charset=utf8mb4", echo=True)


def get_list_admins() -> list[int]:
    stmt = select(Admin)
    with Session(engine) as session:
        admins = session.scalars(stmt)
        list_admins = [admin.id for admin in admins]
        session.commit()
    return list_admins


def save_pay_user(user: str) -> bool:
    try:
        user_obj = Users(nickname=user, pay=True)
        with Session(engine) as session:
            session.add(user_obj)
            session.commit()
        return True
    except IntegrityError:
        return False


def add_object(obj) -> None:
    with Session(engine) as session:
        session.add(obj)
        session.commit()


def del_group(chat_id) -> None:
    stmt = delete(Groups).where(Groups.id == chat_id)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_links_for_user() -> str:
    stmt = select(Groups).order_by(Groups.nickname)
    with Session(engine) as session:
        all_group_str: str = '\n'.join([f"{group.nickname}\t{group.link_chat}"
                                        for group in session.scalars(stmt)])
        session.commit()
    return all_group_str


def update_user(user_nick: str, **value) -> None:
    stmt = update(Users).where(Users.nickname == user_nick).values(value)
    print(stmt)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_name_id_group() -> dict:
    stmt = select(Groups).order_by(Groups.nickname)
    with Session(engine) as session:
        dict_group = {str(group.id): group.nickname for group in session.scalars(stmt)}
        session.commit()
    return dict_group


def update_group_link(group_id: int, **param) -> bool:
    stmt = update(Groups).where(Groups.id == group_id).values(param)
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

    with Session(engine) as session:
        result = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def get_admin_by_id(admin_id: int) -> Admin | None:
    stmt = select(Admin).where(Admin.id == admin_id)
    with Session(engine) as session:
        result = session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound:
            return


def add_users_by_nickname(nick: str) -> str:
    user: Users = Users(nickname=nick, pay=True)
    try:
        with Session(engine) as session:
            session.add(user)
            session.commit()
    except (PendingRollbackError, IntegrityError):
        with Session(engine) as session:
            stmt = update(Users).where(Users.nickname == nick).values({"pay": True})
            session.execute(stmt)
            session.commit()
    return f"{nick} добавлен в оплаченные"


def update_group_status(group_id) -> None:
    stmt = update(Groups).where(Groups.id == group_id).values(news_group=True)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def add_admins_by_id(users_id: int) -> None:
    admin: Admin = Admin(id=users_id)
    with Session(engine) as session:
        session.add(admin)
        print(admin.id)
        session.commit()


def get_group(group_name) -> Groups:
    stmt = select(Groups).where(Groups.nickname == group_name)
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        return result.one()


def get_list_groups() -> Sequence[Groups]:
    stmt = select(Groups)
    with Session(engine) as session:
        result = session.scalars(stmt)
        session.commit()
        return result.all()


def unpay_users_by_nickname(nick) -> str:
    stmt = update(Users).where(Users.nickname == nick).values(pay=False)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()
    return f"{nick} удален из оплаченных и из групп"


def ban_users(nickname):
    stmt = update(Users).where(Users.nickname == nickname).values(ban=True)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def unban_user(nickname):
    stmt = update(Users).where(Users.nickname == nickname).values(ban=False)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def get_all_user() -> Sequence[Users]:
    stmt = select(Users).order_by(Users.nickname)
    with Session(engine) as session:
        result = session.scalars(stmt)
        return result.all()


def get_pay_users() -> list[Users]:
    stmt = select(Users).where(Users.pay.is_(True))
    with Session(engine) as session:
        result = session.scalars(stmt)
        return [user for user in result.all()]


def del_admins_by_id(param) -> None:
    stmt = delete(Admin).where(Admin.id == param)
    with Session(engine) as session:
        session.execute(stmt)
        session.commit()
