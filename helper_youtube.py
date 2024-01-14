import asyncio
import logging
import sys
import os
from os import getenv
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
import config
from pytube import YouTube
import datetime

TOKEN = getenv("BOT_TOKEN") or config.TOKEN

form_router = Router()

class Form(StatesGroup):
    url=State()
    title = State()
    menu = State()

@form_router.message(CommandStart())
async def command_start(message: Message, state: FSMContext) -> None:
    # await state.set_state(Form.url)
    await message.answer('<b>👋 Hello, I am YouTube Assistant.</b> \n <b>📥 You can download videos from YouTube.</b> \n <b>🔗 Send the link to the video.</b>', parse_mode='HTML')
    
@form_router.message(Command("help"))
async def command_help(message: Message, state: FSMContext) -> None:
    await message.answer("⁉️<b> If you have any problems.</b> \n✉️ <b>Write to me</b> <a href='https://t.me/nikit0ns'>@nikit0ns</a><b>.</b>", disable_web_page_preview=True, parse_mode="HTML")

@form_router.message(F.text.startswith('https://youtube.be/'))
@form_router.message(F.text.startswith('https://youtu.be/'))
@form_router.message(F.text.startswith('https://www.youtube.com/'))
async def command_url(message: Message, state: FSMContext) -> None:
    url = message.text
    yt = YouTube(url)
    await state.update_data(
        url = url,
        title = yt.title,
        yttitle = yt.title,
        author = yt.author,
        channel = yt.channel_url,
        resolution = yt.streams.get_highest_resolution().resolution,
        file_size = yt.streams.get_highest_resolution().filesize,
        length = yt.length,
        date_published = yt.publish_date.strftime("%Y-%m-%d"),
        views = yt.views,
        picture = yt.thumbnail_url
    )
    await state.set_state(Form.menu)
    await show_status(message, await state.get_data())

@form_router.message(Form.url)
async def command_url(message: Message, state: FSMContext) -> None:
    await message.answer(f"❗️<b>This doesn't seem like a link!</b>", parse_mode='HTML')     

@form_router.message(Form.menu, F.text.casefold() == "set custom title")
async def button_set_title(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.title)
    await message.answer('Choose the title',
                         reply_markup=ReplyKeyboardRemove())
        
@form_router.message(Form.title)
async def set_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await state.set_state(Form.menu)
    await show_status(message, await state.get_data())

@form_router.message(Form.url, F.text.startswith('https://www.youtube.com/'))
async def command_url(message: Message, state: FSMContext) -> None:
    url = message.text

@form_router.message(Form.menu, F.text.casefold() == "download")
async def button_download(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    url = data.get('url')
    title = data.get('title')
    yttitle = data.get('yttitle')
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension="mp4")
    stream.get_highest_resolution().download(f'{message.chat.id}', f'{message.chat.id}_{yt.video_id}.mp4')
    await message.answer_video(
        video=FSInputFile(f"{message.chat.id}/{message.chat.id}_{yt.video_id}.mp4"),
        caption=f"\n\n<b>{title}</b>\n<a href='{url}'>YT link</a>", 
        parse_mode='HTML',
        reply_markup=ReplyKeyboardRemove()
    )
    os.remove(f"{message.chat.id}/{message.chat.id}_{yt.video_id}.mp4")
    try:
        os.rmdir(f"{message.chat.id}")
    except OSError as e:
        print("Error: %s : %s" % (message.chat.id, e.strerror))

async def show_status(message: Message, data: Dict[str, Any]) -> None:
    url = data.get('url')
    title = data.get('title')
    yttitle = data.get('yttitle')
    author = data.get('author')
    channel = data.get('channel')
    resolution = data.get('resolution')
    file_size = data.get('file_size')
    length = data.get('length')
    date_published = data.get('date_published')
    views = data.get('views')
    picture = data.get('picture')
    await message.answer_photo(
        f'{picture}', caption=f"📹 <b>{title}</b> <a href='{url}'>→</a> \n" #Title#
        f"👤 <b>{author}</b> <a href='{channel}'>→</a> \n" #Author Of Channel# 
        f"⚙️ <b>Resolution —</b> <code>{resolution}</code> \n" ##
        f"🗂 <b>Video size —</b> <code>{round(file_size * 0.000001, 2)}MB</code> \n" #File Size#
        f"⏳ <b>Duration —</b> <code>{str(datetime.timedelta(seconds=length))}</code> \n" #Length#
        f"🗓 <b>Published on —</b> <code>{date_published}</code> \n" #Date Published#
        f"👁 <b>Views —</b> <code>{views:,}</code> \n", parse_mode='HTML',
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Download"),
                    KeyboardButton(text="Set Custom Title"),
                ]
            ],
            resize_keyboard=True,
        ),
    )

async def main():
    bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    dp.include_router(form_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
