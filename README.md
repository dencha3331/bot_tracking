# Group Moderator Bot



The "Group Moderator Bot" project is a tool for automatic group moderation in the Telegram messenger. 
The bot is developed using the aiogram3, pyrogram, and sqlalchemy libraries.

The main functionality of the bot is to restrict access to the group only for paid users. 
Before using the bot, you need to upload a list of paid users by providing their usernames or 
profile links. After that, you should add the bot to the group and make it an administrator. 
All users who are not included in the paid list will be automatically blocked when trying to 
join the group.

If the group already exists and has users, you can perform a group check by selecting the corresponding 
option in the bot's menu. As a result of the check, all users who have not been added to the paid list 
will be blocked. When performing a check in a newsgroup, the bot will gather information about the 
users and add them to the database without blocking their access.

In addition to the main functionality, the bot provides a number of additional features. For example, 
you can add or remove users from the paid list and from groups. You can also change the group's 
invitation link, generate a new link, or make the group a newsgroup, saving all new users to 
the database. The bot also allows you to download CSV files with information about users and their statuses.

For ease of use, the bot provides a help section that describes each of the provided features. 
The description includes instructions on adding and removing users, changing the invitation link,
performing checks on unpaid users, and managing bot administrators.

![ksnip_20240106-172629](https://github.com/dencha3331/bot_tracking/assets/105551459/2329c9c5-8d51-42f8-a95d-907d894bc95d)

## Install
The bot requires [Redis](https://redis.io/docs/install/install-redis/) to function properly.

```shell
git clone https://github.com/dencha3331/bot_tracking.git
cd bot_tracking
```

```shell
pip install -r requirements.txt
python3 main.py
```



## На русском


Проект "Бот модератор групп" представляет собой инструмент для автоматической модерации групп в 
мессенджере Telegram. Стек aiogram3, pyrogram и sqlalchemy.

Основной функционал бота заключается в ограничении доступа к группе только для оплаченных пользователей. 
Перед использованием бота необходимо загрузить список оплаченных пользователей, предоставив их username 
или ссылки на профили. После этого бота следует добавить в группу и сделать его администратором. 
Все пользователи, не внесенные в список оплаченных, будут автоматически заблокированы при попытке вступить 
в группу.

Если группа уже существует и в ней есть пользователи, можно провести проверку по группе, выбрав 
соответствующий пункт в меню бота. В результате проверки будут заблокированы все пользователи, 
которые не были добавлены в список оплаченных. При проведении проверки в новостной группе бот 
соберет сведения о пользователях и добавит их в базу данных, при этом не блокируя их доступ.

В дополнение к основному функционалу бота, предоставляется ряд дополнительных возможностей. 
В частности, можно добавлять или удалять пользователей из списка оплаченных и из групп. 
Также можно изменять пригласительную ссылку группы, сгенерировать новую ссылку или сделать группу 
новостной, сохраняя всех новых пользователей в базу данных. Бот также предоставляет возможность 
скачивать файлы в формате CSV с информацией о пользователях и их статусах.

Для удобства использования бота предоставляется справка, в которой описывается каждая из 
предоставляемых функциональных возможностей. Описание включает инструкции по добавлению и 
удалению пользователей, изменению пригласительной ссылки, проведению проверки на неоплаченных 
пользователей, а также управлению администраторами бота.

## Установка
Для работы бота нужен [Redis](https://redis.io/docs/install/install-redis/)

```shell
git clone https://github.com/dencha3331/bot_tracking.git
cd bot_tracking
```

```shell
pip install -r requirements.txt
python3 main.py
```
