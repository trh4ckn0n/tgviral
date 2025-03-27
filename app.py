from telethon import TelegramClient, events
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
import asyncio
import random
from config import api_id, api_hash, bot_token

# Initialisation du client Telethon
client = TelegramClient("bot_session", api_id, api_hash).start(bot_token=bot_token)

# Liste pour éviter de spammer les mêmes groupes
groupes_deja_visites = set()

async def recuperer_membres_du_groupe(chat):
    """ Récupère les membres du groupe et tente de voir où ils sont aussi. """
    try:
        participants = await client(GetParticipantsRequest(chat, ChannelParticipantsSearch(''), 0, 100, hash=0))
        return [p.id for p in participants.users]
    except Exception as e:
        print(f"Impossible de récupérer les membres de {chat.title}: {e}")
        return []

async def trouver_groupes_en_commun(user_id):
    """ Vérifie les groupes communs d'un utilisateur """
    try:
        user_dialogs = await client.get_dialogs()
        return [d.entity for d in user_dialogs if hasattr(d.entity, 'participants_count') and user_id in d.entity.participants]
    except Exception as e:
        print(f"Erreur lors de la recherche des groupes communs: {e}")
        return []

async def inviter_bot(group):
    """ Envoie une demande d'ajout du bot à un groupe """
    if group.id in groupes_deja_visites:
        return
    
    try:
        await client(InviteToChannelRequest(group, [await client.get_me()]))
        groupes_deja_visites.add(group.id)
        print(f"Ajouté avec succès à {group.title}")
    except Exception as e:
        print(f"Erreur d'invitation dans {group.title}: {e}")

@client.on(events.ChatAction)
async def action_handler(event):
    """ Déclenché lorsqu'un membre rejoint ou ajoute le bot """
    if event.user_added or event.user_joined:
        chat = event.chat
        if chat.id in groupes_deja_visites:
            return
        
        print(f"Bot ajouté à {chat.title}, récupération des membres...")
        user_ids = await recuperer_membres_du_groupe(chat)

        for user_id in user_ids:
            groupes_communs = await trouver_groupes_en_commun(user_id)
            for group in groupes_communs:
                await inviter_bot(group)
                await asyncio.sleep(random.randint(5, 10))  # Pour éviter le spam

client.run_until_disconnected()
