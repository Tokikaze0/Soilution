import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
from django.contrib.auth.models import User
from django.utils.timesince import timesince

class InboxConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.group_name = f"user_{user.id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_message(self, event):
        message = event["message"]
        sender_id = message["sender_id"]
        sender_username = message["sender"]
        content = message["content"]
        timestamp = message["timestamp"]

        await self.send(text_data=json.dumps({
            "type": "new_message",
            "message": {
                "sender_id": sender_id,
                "sender": sender_username,
                "content": content,
                "timestamp": timestamp
            }
        }))

    async def typing(self, event):
        sender_id = event['sender_id']
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender_id': sender_id
        }))

    async def receive(self, text_data):
        """
        This handles messages sent from JavaScript over WebSocket (e.g. typing events).
        """
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "typing":
            receiver_id = data.get("receiver_id")
            sender_id = self.scope["user"].id

            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    "type": "typing",
                    "sender_id": sender_id
                }
            )

