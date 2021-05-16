from asyncio import sleep

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import admin_id
from load_all import dp, _, bot
from states import NewItem, Mailing
from database import Items, User

@dp.message_handler(user_id=admin_id, commands=["cancel"], state=NewItem)
async def cancel(message: types.Message, state: FSMContext):
    await message.answer("Вы прервали создание товара")
    await state.reset_state()

@dp.message_handler(commands=["add_items"])
async def add_item(message: types.Message):
    await message.answer(("Введите название товара иди нажмите /cancel"))
    await NewItem.Name.set()


@dp.message_handler(user_id = admin_id, state=NewItem.Name)
async def enter_name(message: types.Message, state:FSMContext):
    name = message.text
    item = Items()
    item.name = name
    await message.answer((f"Название: {name}\n"
                          f"Фото товара (не документ) или нажмите /cancel").format(
        name=name
    ))
    await NewItem.Photo.set()
    await state.update_data(item=item)

@dp.message_handler(user_id=admin_id,state=NewItem.Photo, content_types=types.ContentType.PHOTO)
async def add_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1].file_id
    data = await state.get_data()
    item: Items = data.get("item")
    item.photo = photo
    await message.answer_photo(
        photo=photo,
        caption=_("Название: {name}\n"
                  "Назначте цену (в копейках) или нажмите /cancel").format(
            name=item.name
        )
    )
    await NewItem.Price.set()
    await state.update_data(item=item)

@dp.message_handler(user_id=admin_id, state=NewItem.Price)
async def enter_price(messege: types.Message, state: FSMContext):
    data = await state.get_data()
    item: Items = data.get("item")
    try:
        price = int(messege.text)
    except ValueError:
        await messege.answer("Цена введене на верно, повторите")
        return
    item.price = price

    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardMarkup(
                text="Да",
                callback_data="confirm")],
            [types.InlineKeyboardMarkup(
                text="Ввести заного",
                callback_data="change"
            )]
        ]
    )
    await messege.answer(
        (f"Цена: {price:,}\n"
         f"Подтверждаете? Иначе нажмите /cancel").format(price=price),
        reply_markup=markup
    )
    await state.update_data(item=item)
    await NewItem.Confirm.set()

@dp.callback_query_handler(user_id=admin_id,
                           text_contains="change",
                           state=NewItem.Confirm)
async def change_price (call: types.CallbackQuery):
    await call.message.edit_reply_markup()
    await call.message.answer(_("Введите новую цену(в копейках)"))
    await NewItem.Price.set()

@dp.callback_query_handler(user_id=admin_id,
                           text_contains="confirm",
                           state=NewItem.Confirm)
async def confirm(call:types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup()
    data = await state.get_data()
    item: Items = data.get("item")
    await item.create()
    await call.message.answer(_("Товар создан"))
    await state.reset_state()


@dp.message_handler(user_id=admin_id, commands=["tell_everyone"])
async def mailing(message:types.Message):
    await message.answer(_("Что бы вы хотели всем сообщить?"))
    await Mailing.Text.set()

dp.message_handler(user_id=admin_id, state=Mailing.Text)
async def press_text(message: types.Message, state:FSMContext):
    text = message.text
    await state.update_data(text=text)
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardMarkup(
                text="Русский",
                callback_data="кг")],
            [types.InlineKeyboardMarkup(
                text="English",
                callback_data="en"
            )]
        ]
    )
    await message.answer(_("Выберите язык для отправки сообщения\n\n"
                           "Текст: \n"
                           "{text}").format(text=text),
                         reply_markup=markup)
    await Mailing.Language.set()

@dp.callback_query_handler(user_id=admin_id, state=Mailing.Language)
async def translate (call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data("text")
    text = data.get("text")
    await state.reset_state()
    await call.message.edit_reply_markup()
    users = await User.query.query.where(User.language == call.data).gino.all()
    for user in users:
        try:
            await bot.send_message(chat_id=user.user_id,
                                    text=text)
            await sleep(0,3)
        except Exception:
            pass

        await call.message.answer(_("Ваше сообщение было отправленно"))


