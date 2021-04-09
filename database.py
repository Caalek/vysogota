import os
from pymongo import MongoClient
from dotenv import load_dotenv
load_dotenv()

db = MongoClient(os.environ.get('MONGODB_URI'))['vysogota']

def check_exists(uid):
    exists = db.users.find_one({'_id': uid})
    if exists is not None:
        return True
    else:
        return False

def create_user(uid):
    user = {
            '_id': uid,
            'guilds': []
        }
    db.users.insert_one(user)

def user_assigned_to_guild(uid, guild_id):
    users_guilds = db.users.find_one({'_id': uid})['guilds']
    for i in users_guilds:
        if i['guild_id'] == guild_id:
            return True
    else:
        return False

def assign_to_guild(uid, guild_id):
    guild = {
        'guild_id': guild_id,
        'points': 0,
        }
    db.users.update_one({'_id': uid}, {'$push': {'guilds': guild}})

def add_points(uid, guild_id, amount):
    user = db.users.find_one({'_id': uid})
    user_guilds = user['guilds']
    for i in user_guilds:
        if i['guild_id'] == guild_id:
            index = user_guilds.index(i)
            break
            
    db.users.update_one({'_id': uid}, {'$inc': {f'guilds.{index}.points': amount}})