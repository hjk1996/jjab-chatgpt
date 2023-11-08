from uuid import uuid4
import json
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from pymongo import MongoClient
from openai import OpenAI

from models import ChatRoom

api_key = os.environ.get("OPENAI_API_KEY")
user = os.environ.get("DB_USER")
password = os.environ.get("DB_PASSWORD")
mongo_uri = f"mongodb://{user}:{password}@db:27017"


client = MongoClient(mongo_uri)
db = client["chat_db"]


app = Flask(__name__)
socketio = SocketIO(app)

openai = OpenAI(
    api_key=api_key,
)


@app.route("/", methods=["GET"])
def index():
    chat_rooms = db.chat_rooms.find()
    chat_rooms = [ChatRoom.from_mongo(chat_room) for chat_room in chat_rooms]
    return render_template("index.html", chat_rooms=chat_rooms)


@app.route("/chat/<room_id>", methods=["GET"])
def chat(room_id: str):
    chat_room_doc = db.chat_rooms.find_one({"_id": room_id})
    chat_room = ChatRoom.from_mongo(chat_room_doc)
    return render_template("chat_room.html", chat_room=chat_room.json(by_alias=True))


@socketio.on("join")
def on_join(data):
    room = data["room"]
    join_room(room)
    send(f"A Player has joined the room.", room=room)


@socketio.on("leave")
def on_leave(data):
    room = data["room"]
    leave_room(room)
    send(f"A Player has left the room.", room=room)


@socketio.on("message")
def handle_message(data):
    room = data["room"]
    content = data["content"]
    sender_id = data["sender_id"]
    timestamp = data["timestamp"]
    message_id = data["message_id"]
    db.chat_rooms.update_one(
        {"_id": room},
        {
            "$push": {
                "messages": {
                    "_id": message_id,
                    "content": content,
                    "sender_id": sender_id,
                    "timestamp": timestamp,
                }
            }
        },
    )
    emit(
        "message",
        {
            "content": content,
            "sender_id": sender_id,
            "timestamp": timestamp,
            "message_id": message_id,
        },
    )
    chat_room = ChatRoom.from_mongo(db.chat_rooms.find_one({"_id": room}))
    completion = openai.chat.completions.create(
        messages=chat_room.messages_to_dict(), model="gpt-3.5-turbo"
    )
    ai_content = completion.choices[0].message.content
    ai_id = "assistant"
    ai_message_id = str(uuid4())
    ai_timestamp = datetime.now().timestamp()
    db.chat_rooms.update_one(
        {"_id": room},
        {
            "$push": {
                "messages": {
                    "_id": ai_message_id,
                    "content": ai_content,
                    "sender_id": ai_id,
                    "timestamp": ai_timestamp,
                }
            }
        },
    )
    emit(
        "message",
        {
            "content": ai_content,
            "sender_id": ai_id,
            "timestamp": ai_timestamp,
            "message_id": ai_message_id,
        },
    )


@app.route("/create_room", methods=["POST"])
def create_room():
    room_name = request.form.get("room_name")
    personality = request.form.get("personality")
    if room_name:
        # 새 채팅방 생성
        new_chat_room = ChatRoom(
            _id=str(uuid4()), name=room_name, personality=personality, messages=[]
        )
        db.chat_rooms.insert_one(
            json.loads(new_chat_room.model_dump_json(by_alias=True))
        )
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
