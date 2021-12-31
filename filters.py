from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from loader import chats

class IsGroupJoin(BoundFilter):
    key = "is_group_join"

    def __init__(self, is_group_join: bool):
        self.is_group_join = is_group_join

    async def check(self, update: types.ChatMemberUpdated):
        print(update)
        print()
        print(chats)
        if update.new_chat_member.status in ("member", "creator"):
            if str(update.chat.id) in chats:
                print('true')
                return True
        elif update.old_chat_member.status in ("member", "administrator", 'admin', "creator"):
            if str(update.chat.id) in chats:
                print('true')
                return True

