#!/usr/bin/env python


from __future__ import annotations
from types import TracebackType
from typing import Iterator, cast
from pyrogram.client import Client
import pyrogram.types as pt
from dataclasses import dataclass, field, InitVar
from datetime import datetime


@dataclass
class TgChat:
    """
    Базовая информация о чате
    """
    id: int = field(init=False)     # ID чата
    name: str = field(init=False)   # Название чата

    dialog: InitVar[pt.Dialog]      # Аргументом конструктора передаётся сущность Dialog из pyrogram

    @staticmethod
    def __get_chat_name(chat: pt.Chat) -> str:
        """
        Извлекате удобочитаемое название чата.
        """
        if chat.title:
            return chat.title
        full_name = " ".join(
            part for part in (chat.first_name, chat.last_name) if part
        )
        return full_name or chat.username or str(chat.id)

    def __post_init__(self, dialog: pt.Dialog):
        self.id = dialog.chat.id
        self.name = TgChat.__get_chat_name(dialog.chat)

    def __str__(self):
        return f"{self.name}: {self.id}"


@dataclass
class TgMessage:
    """
    Сообщение чата с метаданными
    """
    id: int
    date: datetime
    author: str
    content: str

    def __str__(self):
        return f"[{self.date}] {self.author}: {self.content}"


class TgReader:
    """
    Класс предоставляет упрощённый API для доступа к чатам Telegram.
    """
    def __init__(self, api_id: int, api_hash: str):
        self.__client = Client(
            "telegram_account",
            api_id = api_id,
            api_hash = api_hash
        )
    
    def __enter__(self) -> 'TgReader':
        self.__client.start() # type: ignore[misc]
        return self
    
    def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None
    ):
        self.__client.stop() # type: ignore[misc]

    def get_chats(self) -> list[TgChat]:
        """
        Получить список доступных чатов.
        """
        dialogs = cast(
            Iterator[pt.Dialog],
            self.__client.get_dialogs(),
        )
        return [TgChat(dialog) for dialog in dialogs]
    
    @staticmethod
    def get_message_author(message: pt.Message) -> str:
        """
        Получить удобочитаемое имя автора сообщения.
        """
        if message.from_user:
            user = message.from_user

            full_name = " ".join(
                part for part in (user.first_name, user.last_name) if part
            )

            return full_name or user.username or str(user.id)
        elif message.sender_chat:
            chat = message.sender_chat
            return chat.title or chat.username or str(chat.id)
        else:
            return "<Unknown>"
    
    @staticmethod
    def get_message_content(message: pt.Message) -> str:
        """
        Получить в читаемом виде содержимое сообщения.
        """
        if message.text:
            return message.text
        elif message.caption:
            return message.caption
        elif message.media:
            return f"<медиа: {message.media.value}>"
        elif message.service:
            return f"<служебное событие: {message.service.value}>"
        else:
            return "<служебное событие>"

    
    def get_messages(self, chat_id: int, limit: int) -> list[TgMessage]:
        """
        Получить `limit` последних сообщений из чата `chat_id`.
        """
        history = cast(
            Iterator[pt.Message],
            self.__client.get_chat_history(chat_id, limit)
        )
        return [
            TgMessage(
                msg.id,
                msg.date,
                TgReader.get_message_author(msg),
                TgReader.get_message_content(msg)
            ) for msg in history
        ]


if __name__ == "__main__":
    import os

    # Читаем API_KEY
    from dotenv import load_dotenv
    load_dotenv()

    def create_TgReader() -> TgReader:
        return TgReader(
            api_id=int(os.environ["TG_API_ID"]),
            api_hash=os.environ["TG_API_HASH"]
        )

    # Парсер аргументов скрипта
    from argparse import ArgumentParser
    arg_parser = ArgumentParser(
        description="Справка по командам"
    )
    subparsers = arg_parser.add_subparsers(
        dest="command",
        required=True,
        help="Действие"
    )
    list_parser = subparsers.add_parser(
        "list",
        help="Показать список доступных чатов"
    )
    show_parser = subparsers.add_parser(
        "show",
        help="Показать сообщения из чата"
    )
    show_parser.add_argument(
        "chat_id",
        help="ID чата"
    )
    show_parser.add_argument(
        "count",
        type=int,
        nargs="?",
        default=20,
        help="Количество последних сообщений"
    )
    args = arg_parser.parse_args()

    if args.command == "list":
        # Запрашиваем список чатов
        tg = create_TgReader()
        with tg:
            chats = tg.get_chats()
        for chat in chats:
            print(chat)
    elif args.command == "show":
        # Запрашиваем сообщения из чата
        tg = create_TgReader()
        with tg:
            messages = tg.get_messages(
                args.chat_id,
                args.count
            )
        for msg in messages:
            print(msg)
    else:
        # Пользователь не указал действие
        # Выводим справку
        arg_parser.print_help()