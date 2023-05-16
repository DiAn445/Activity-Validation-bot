from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import UserAdminInvalidError, ParticipantIdInvalidError
from telethon.tl import types
import re

api_id = 'your API ID'
api_hash = 'your API Hash'
phone_number = 'your phone number'

# creating Telegram client
client = TelegramClient('session_name', api_id, api_hash)

# getting info about chat
chat_username = 'link of ur telegram chat'
chat_id = None


async def remove_inactive_users(chat_id):
    participants = await client.get_participants(chat_id)
    time_threshold = 4 * 24 * 60 * 60

    for participant in participants:
        if participant.bot:
            continue

        # user activity checking
        if participant.status:
            if isinstance(participant.status, types.UserStatusOnline):
                # if user online at the moment
                continue
            elif isinstance(participant.status, types.UserStatusOffline):
                last_activity_timestamp = participant.status.was_online.timestamp()
                current_timestamp = datetime.now().timestamp()
                inactive_duration = current_timestamp - last_activity_timestamp

                if inactive_duration >= time_threshold:
                    try:
                        # delete user if wasn't online more than 4 days
                        await client.kick_participant(chat_id, participant)
                    except UserAdminInvalidError:
                        print(
                            f'Bot not allowed to delete admins. User {participant.id} is admin.')


# hook for /checkout command
@client.on(events.NewMessage(pattern='/checkout'))
async def handle_cleanup_command(event):
    try:
        global chat_id

        # Getting the ID of the current chat if it hasn't been received yet
        if chat_id is None:
            chat = await client.get_entity(chat_username)
            chat_id = chat.id

        # Checking the rights of the sender
        permissions = await client.get_permissions(chat_id, event.sender_id)
        if not permissions.is_admin:
            await event.respond('You do not have sufficient rights to execute the command.')
            return

        # Removing inactive users
        await remove_inactive_users(chat_id)

        await event.respond('Cleaning completed successfully.')
    except Exception as e:
        await event.respond(f'An error occurred while cleaning: {str(e)}')


async def is_spam(message):
    # Checking for specific keywords
    keywords = ['spam', 'discount', 'sell']
    for keyword in keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', message.text, re.IGNORECASE):
            return True
    return False


async def handle_message(message):
    if await is_spam(message):
        try:
            # Restricting user access rights in a chat
            if message.sender_id is not None:
                await client.edit_permissions(chat_id, message.sender_id, send_messages=False)
                await message.respond('You have been restricted for spam.')
            else:
                print('Restrictions cannot be applied. The sender of the message is not defined.')
        except UserAdminInvalidError:
            print('The bot is not allowed to change admin permissions.')
        except ParticipantIdInvalidError:
            print('Unable to apply restrictions to chat owner.')


# hook for newMessages
@client.on(events.NewMessage)
async def handle_new_message(event):
    await handle_message(event.message)

if __name__ == '__main__':
    with client:
        client.start(phone_number)
        client.run_until_disconnected()


