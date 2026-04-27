"""
Reaction Bot — кілька акаунтів паралельно ставлять реакції на нові пости.
Сесії читаються з env vars: SESSION_1, SESSION_2, ...
"""
import asyncio
import os
import random
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import SendReactionRequest, ImportChatInviteRequest
from telethon.tl.types import ReactionEmoji

API_ID   = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

CHANNELS = [
    "football1Ukraine",
    "ualegioner",
    "https://t.me/+5veDkHfkmyg4ODk6",
    "https://t.me/+X1PYq8Fj0i0wYWNi",
    "https://t.me/+Xo_zUF2qmLIwODky",
    "https://t.me/+QdZUYYVGpB5jN2Qy",
]

# ❤ 60%, 👍 15%, 🔥 10%, решта рідкісні
REACTIONS = [
    ("❤",  60),
    ("👍", 15),
    ("🔥", 10),
    ("👏",  5),
    ("🏆",  3),
    ("🎉",  2),
    ("🥰",  1),
    ("💯",  1),
    ("⚡",  1),
    ("🤩",  1),
    ("💪",  1),
]
REACTION_EMOJIS  = [r[0] for r in REACTIONS]
REACTION_WEIGHTS = [r[1] for r in REACTIONS]

DELAY_MIN = 20
DELAY_MAX = 1800


def get_sessions():
    sessions = []
    i = 1
    while True:
        s = os.environ.get(f"SESSION_{i}")
        if not s:
            break
        sessions.append(s)
        i += 1
    return sessions


async def react(client, account, peer, msg_id, channel):
    delay = random.randint(DELAY_MIN, DELAY_MAX)
    emoji = random.choices(REACTION_EMOJIS, weights=REACTION_WEIGHTS, k=1)[0]

    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{account}] "
          f"{channel} #{msg_id} -> {emoji} через {delay}с")

    await asyncio.sleep(delay)

    try:
        await client(SendReactionRequest(
            peer=peer,
            msg_id=msg_id,
            reaction=[ReactionEmoji(emoticon=emoji)],
        ))
        print(f"  OK [{account}] {emoji} -> #{msg_id} @{channel}")
    except Exception as e:
        print(f"  ERR [{account}] #{msg_id}: {e}")


async def run_account(session_str, index):
    client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
    await client.start()

    me = await client.get_me()
    account = f"@{me.username}" if me.username else me.first_name
    print(f"[{account}] підключено")

    entities = []
    for ch in CHANNELS:
        try:
            entity = await client.get_entity(ch)
            entities.append(entity)
        except Exception:
            if "t.me/+" in ch:
                hash_ = ch.split("/+")[1]
                try:
                    result = await client(ImportChatInviteRequest(hash_))
                    entity = result.chats[0]
                    entities.append(entity)
                    print(f"  [{account}] joined: {entity.title}")
                except Exception as e2:
                    print(f"  [{account}] ERR joining {ch}: {e2}")
            else:
                try:
                    await client(JoinChannelRequest(ch))
                    entity = await client.get_entity(ch)
                    entities.append(entity)
                    print(f"  [{account}] joined: @{ch}")
                except Exception as e2:
                    print(f"  [{account}] ERR joining @{ch}: {e2}")

    entity_ids = set()
    for e in entities:
        entity_ids.add(e.id)
        entity_ids.add(-1000000000000 - e.id)

    print(f"[{account}] слухає {len(entities)} каналів")

    @client.on(events.NewMessage())
    async def handler(event):
        if not event.message.post:
            return
        if event.chat_id not in entity_ids:
            return
        name = getattr(event.chat, "username", None) or getattr(event.chat, "title", str(event.chat_id))
        asyncio.ensure_future(react(client, account, event.chat_id, event.message.id, name))

    await client.run_until_disconnected()


async def main():
    sessions = get_sessions()
    if not sessions:
        print("Немає сесій! Додай SESSION_1, SESSION_2, ... в env vars")
        return
    print(f"Запускаємо {len(sessions)} акаунт(ів)...")
    print("-" * 50)
    await asyncio.gather(*[run_account(s, i) for i, s in enumerate(sessions, 1)])


if __name__ == "__main__":
    asyncio.run(main())
