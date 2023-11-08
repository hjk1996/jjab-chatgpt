from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4
from bson import ObjectId


class User(BaseModel):
    username: str
    user_id: str = Field(alias="_id")
    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        json_encoders = {
            UUID: lambda v: str(v),
        }

    @classmethod
    def from_mongo(cls, data: dict):
        # MongoDB의 _id를 user_id로 변환
        if "_id" in data:
            data["user_id"] = data.pop("_id")
        return cls(**data)


class Message(BaseModel):
    content: str
    sender_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    message_id: str = Field(alias="_id")

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        json_encoders = {
            UUID: lambda v: str(v),
        }

    @classmethod
    def from_mongo(cls, data: dict):
        # MongoDB의 _id를 message_id로 변환
        if "_id" in data:
            data["message_id"] = data.pop("_id")
        return cls(**data)


system_prompt = """
I want you to act like you are a person with {personality} personality. 
I want you to respond and answer like {personality} person using the tone, manner and vocabulary {personality} man would use. 
Do not write any explanations. Only answer like {personality} person. 
You must know all of the knowledge of {personality} person. 
Only talk in korean.
"""

class ChatRoom(BaseModel):
    name: str
    room_id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.now)
    personality : str
    messages: List[Message] = []

    class Config:
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        json_encoders = {
            UUID: lambda v: str(v),
        }

    @classmethod
    def from_mongo(cls, data: dict):
        # MongoDB의 _id를 room_id로 변환
        return cls(**data)
    
    
    def messages_to_dict(self):
        return [{
            "role": "system", "content": system_prompt.format(personality=self.personality)
        }] + [{"role": message.sender_id, "content": message.content} for message in self.messages]
