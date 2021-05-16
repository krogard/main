from aiogram import types, Bot
from gino import Gino
from gino.schema import GinoSchemaVisitor
from sqlalchemy import (Column, Integer, BigInteger, String,
                        Sequence, TIMESTAMP, Boolean, JSON)

from sqlalchemy import sql

from config import db_pass, db_user, host

db = Gino()

class User(db.Model):
    __tamblename__ = "users"
    id = Column(Integer,Sequence("users_id_seq"), primary_key=True)
    user_id = Column(BigInteger)
    language = Column(String(2))
    full_name = Column(String(80))
    user_name = Column(String(50))
    referral = Column(Integer)
    query: sql.select

class Items(db.Model):
    __tablename__ = "items"
    id = Column(Integer, Sequence("users_id_seq"), primary_key=True)
    nsme = Column(String(50))
    photo = Column(String(200))
    cost = Column(Integer)
    query: sql.select

class sale_items(db.Model):
    __tablename__ = "sale_items"
    id = Column(Integer, Sequence("users_id_seq"), primary_key=True)
    buyer = Column(BigInteger)
    item_id = Column(Integer)
    amount = Column(Integer)
    quantity = Column(Integer)
    sale_time = Column(TIMESTAMP)
    delivery_address = Column(JSON)
    phone = Column(String(50))
    email = Column(String(100))
    recever = Column(String(100))
    seccessfull_buy = Column(Boolean, default=False)
    query: sql.select

class DBCommands:
    async def get_user(self, user_id):
        user = await User.query.where(User.user_id == user_id).gino.first()
        return user
    async def add_new_user(self, referral=None):
        user = types.User.get_current
        old_user = await self.get_user(user.id)
        if old_user:
            return old_user
        new_user = User()
        new_user.user_id = user.id
        new_user.username = user.username
        new_user.full_name = user.full_name
        if referral:
            new_user.referral = int(referral)
        await new_user.create()
        return new_user

    async def set_language(self, language):
        user_id = self.get_user().id
        user = await self.get_user(user_id)
        await user.update(language=language).apply()

    async def count_users(self):
        all = await db.func.count(User.id).gino.scaler()
        return all

    async def check_referral(self):
        bot = Bot.get_current()
        user_id = types.User.get_current().id
        user = await self.get_user(user_id)
        referrals = await User.query.where(User.referral == user.id).gino.all()
        return ", ".join(
            [
                f"{num+1}. " + (await bot.get_chat(referral.user_id)).get_mention(as_html=True)
                for num, referral in enumerate(referrals)
            ]
        )
    async def show_items(self):
        items = await Items.query.gino.all()
        return items

async def create_db():

    await db.set_bind(f"postgresql://{db_user}:{db_pass}@{host}/gino")
    db.gino = GinoSchemaVisitor
    await db.gino.drop_all()
    await db.gino.create_all()





