import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from .models import Thread, ChatMessage


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):

        await self.send({
            "type": "websocket.accept"
        })

        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']

        # print(me, other_user)
        thread_obj = await self.get_thread(me, other_user)
        self.thread_obj = thread_obj
        # print(thread_obj)
        chat_room = f"thread_{thread_obj.id}"
        self.chat_room = chat_room

        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )

        
        # print('connected', event)

    async def websocket_receive(self, event):
        print('recive..', event)

        text = event.get('text', None)

        if text is not None:
            data = json.loads(text)
            msg = data.get('message')
            user = self.scope['user']
            username = 'anonymous'
            if user.is_authenticated:
                username = user.username


            res = {
                'message': msg,
                'username': username

            }

            await self.create_chat_message(user, msg)
            new_event = {
                "type": "chat_message",
                "text": json.dumps(res)
            }
            
            await self.channel_layer.group_send(self.chat_room, new_event)

    async def websocket_disconnect(self, event):
        print('Disconnected..', event)
        
    async def chat_message(self, event):
        await self.send({
            "type": "websocket.send",
            "text": event['text']
        })

    @database_sync_to_async
    def create_chat_message(self, me, message):
        thread_obj = self.thread_obj
        print('hi this test')
        return ChatMessage.objects.create(thread=thread_obj, user=me, message=message)


    @database_sync_to_async
    def get_thread(self, user, other_user):
        return Thread.objects.get_or_new(user, other_user)[0]



