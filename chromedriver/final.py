from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
import os
import asyncio
import logging
from aiogram.dispatcher.filters import Text
from aiogram import Bot, types, Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import InputFile
from sqlalchemy import create_engine, insert
from sqlalchemy import MetaData, Table, String, Integer, Column, BigInteger
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import exists
from sqlalchemy.dialects.postgresql import FLOAT
from sqlalchemy import and_


"""create db"""
try:
    connection = psycopg2.connect(user="postgres", password="")
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    sql_create_database = cursor.execute('create database Bot')
    cursor.close()
    connection.close()
except Exception:
    pass
finally:
    engine = create_engine("postgresql+psycopg2://postgres:@localhost/bot", echo=True)
    engine.connect()
    metadata = MetaData(engine)
    Base = declarative_base()
    Session = sessionmaker(bind=engine)
    session = Session()


    class Botinfo(Base):
        __tablename__ = 'botinfo'
        ID = Column(String(100), primary_key=True)
        ИНН = Column(BigInteger)
        Наименование = Column(String(100), nullable=False)
        Год = Column(Integer)
        Коэффициент_автономии = Column(FLOAT)
        Коэффициент_обеспеченности_собственными_оборотными_средствами = Column(FLOAT)
        Коэффициент_покрытия_инвестиций = Column(FLOAT)
        Коэффициент_текущей_ликвидности = Column(FLOAT)
        Коэффициент_быстрой_ликвидности = Column(FLOAT)
        Коэффициент_абсолютной_ликвидности = Column(FLOAT)
        Рентабельность_продаж = Column(FLOAT)
        Норма_чистой_прибыли = Column(FLOAT)

    Base.metadata.create_all(engine)

# """create mongodb"""
# client = MongoClient("mongodb+srv://mongouser:toZq5tM9LYiQnGwW@cluster0.muhaypz.mongodb.net/?retryWrites=true&w=majority")
# mongo = client['Project']
# mongo.create_collection('test_sbd')


"""info"""
ck = ["1.1 Коэффициент автономии",
      "1.2 Коэффициент обеспеченности собственными оборотными средствами",
      "1.3 Коэффициент покрытия инвестиций",
      "2.1 Коэффициент текущей ликвидности",
      "2.2 Коэффициент быстрой ликвидности",
      "2.3 Коэффициент абсолютной ликвидности",
      "3.1 Рентабельность продаж",
      "3.2 Норма чистой прибыли"]
cv = []
o = {}
inn_num = 0
received_data = {}
x_path_years = {
    "2015": "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[1]/td[2]/select/option[4]",
    "2016": "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[1]/td[2]/select/option[5]",
    "2017": "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[1]/td[2]/select/option[6]",
    "2018": "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[1]/td[2]/select/option[7]"}


"""Bot"""
storage = MemoryStorage()
bot = Bot(token="")
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


"""Selenium parser"""
s = Service("from selenium.webdriver.chrome.service import Service")
driver = webdriver.Chrome(service=s)
url = "https://www.gks.ru/accounting_report"
driver.get(url)
# with open('Logo.png', 'wb') as file:
#     img = driver.find_element(By.XPATH,
#                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[7]/td[2]/span[1]/a/img[1]")
#     file.write(img.screenshot_as_png)
# # pathimg = r"C:\Users\alkod\PycharmProjects\selen\chromedriver\Logo.png"
# time.sleep(2)


class Form(StatesGroup):
    """Класс состояний FSM"""
    inn = State()
    year = State()
    capcha = State()


async def on_startup(_):
    print('ON')


@dp.message_handler(commands=['start'])
async def command_start(message: types.Message):
    """Стартовое состояние бота"""
    await bot.send_message(message.from_user.id, 'Добрый день! \nВведите ИНН:')
    driver.refresh()
    await Form.inn.set()
    # s = Service("from selenium.webdriver.chrome.service import Service")
    # driver = webdriver.Chrome(service=s)
    # url = "https://www.gks.ru/accounting_report"
    # driver.get(url)


@dp.message_handler(commands=['cancel'], state="*")
@dp.message_handler(Text(equals='cancel', ignore_case=True), state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    """Выход из любого состояния"""
    await state.finish()
    os.remove("C:/Users/alkod/PycharmProjects/selen/chromedriver/Logo.png")
    driver.close()
    driver.quit()
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: all([not message.text.isdigit(), len(message.text) != 10]), state=Form.inn)
async def inn_invalid(message: types.Message):
    """Обработка ошибки ввода ИНН"""
    return await message.reply("ИНН должен состоять из десяти цифр")


@dp.message_handler(state=Form.inn)
async def process_inn(message: types.Message, state: FSMContext):
    """Ввод ИНН"""
    await state.update_data(inn=message.text)
    received_data["inn"] = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("2015", "2016").add("2017", "2018")
    await bot.send_message(message.from_user.id, "Введите год отчетности:", reply_markup=markup)
    await state.set_state(Form.year.state)


@dp.message_handler(lambda message: message.text not in ['2015', '2016', '2017', '2018'], state=Form.year)
async def year_invalid(message: types.Message):
    """Обработка ошибки ввода даты отчетности"""
    return await message.reply("Введите год используя встроенную клавиатуру")


@dp.message_handler(state=Form.year)
async def process_year(message: types.Message, state: FSMContext):
    """Введение года отчетности"""
    async with state.proxy() as data:
        data['year'] = message.text
    received_data["year"] = message.text
    await state.set_state(Form.capcha.state)
    with open('Logo.png', 'wb') as file:
        img = driver.find_element(By.XPATH,
                                  "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[7]/td[2]/span[1]/a/img[1]")
        file.write(img.screenshot_as_png)
    await bot.send_message(chat_id=message.from_user.id, text="Введите капчу", reply_markup=types.ReplyKeyboardRemove())
    photo = InputFile("C:/Users/alkod/PycharmProjects/selen/chromedriver/Logo.png")
    await bot.send_photo(chat_id=message.from_user.id, photo=photo)
    await process_timer(message)


@dp.message_handler(state=Form.capcha)
async def process_capch(message: types.Message, state: FSMContext):
    """Отправка капчи и заполнение"""
    if message.text is not None:
        await state.update_data(capch=message.text)
        received_data["capch"] = message.text
        # global received_data
        # received_data = state.get_data()
        # print(await state.get_data())
    # else:
    #     await state.finish()
        try:
            # pathimg = r"C:\Users\alkod\PycharmProjects\selen\chromedriver\Logo.png"
            time.sleep(2)
            driver.find_element(By.XPATH, x_path_years[received_data["year"]]).click()
            time.sleep(5)
            inn = driver.find_element(By.XPATH,
                                      "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[2]/td[2]/input")
            inn.send_keys(received_data["inn"])

            time.sleep(10)
            capch = driver.find_element(By.XPATH,
                                        "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/table/tbody/tr[7]/td[2]/input")
            capch.send_keys(received_data["capch"])
            time.sleep(6)

            driver.find_element(By.XPATH,
                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/form/div[1]/div/div/span").click()
            time.sleep(20)

            f_1_1 = (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[56]/td[2]").text)) / \
                    (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[42]/td[2]").text))
            f_1_2 = ((float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[56]/td[2]").text)) - \
                     (float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[26]/td[2]").text))) / \
                    (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[40]/td[2]").text))
            f_1_3 = ((float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[56]/td[2]").text)) + \
                     (float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[66]/td[2]").text))) / \
                    (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[80]/td[2]").text))
            p_2_1 = (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[40]/td[2]").text)) / \
                    (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[78]/td[2]").text))
            p_2_2 = ((float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[32]/td[2]").text)) + \
                     (float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[34]/td[2]").text)) + \
                     (float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[36]/td[2]").text))) / \
                    (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[78]/td[2]").text))
            p_2_3 = (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[34]/td[2]").text) + \
                     float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[36]/td[2]").text)) / \
                    (float(driver.find_element(By.XPATH,
                                               "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[78]/td[2]").text))
            eff_3_1 = float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[92]/td[2]").text) / \
                      float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[82]/td[2]").text)
            eff_3_2 = float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[116]/td[2]").text) / \
                      float(driver.find_element(By.XPATH,
                                                "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[82]/td[2]").text)
            cv = [f_1_1, f_1_2, f_1_3, p_2_1, p_2_2, p_2_3, eff_3_1, eff_3_2]
            for i, j, in zip(ck, cv):
                await bot.send_message(chat_id=message.from_user.id, text=f"{i}:{j}")
                await asyncio.sleep(1)
            name = driver.find_element(By.XPATH, "/html/body/div/div/div[3]/div/div[2]/div/div/div/div/div/div[2]/div/div/div/table/tbody/tr[1]/td[2]").text
            # inn = received_data['inn']
            year = int(received_data["year"])
            id_ = name+"_"+str(year)
            flag_1 = not (session.query(exists().where(Botinfo.ID == id_)).scalar())
            inn = int(received_data['inn'])
            if flag_1:
                q = Botinfo(ID=id_,
                            ИНН=inn,
                            Наименование=name,
                            Год=year,
                            Коэффициент_автономии=cv[0],
                            Коэффициент_обеспеченности_собственными_оборотными_средствами=cv[1],
                            Коэффициент_покрытия_инвестиций=cv[2],
                            Коэффициент_текущей_ликвидности=cv[3],
                            Коэффициент_быстрой_ликвидности=cv[4],
                            Коэффициент_абсолютной_ликвидности=cv[5],
                            Рентабельность_продаж=cv[6],
                            Норма_чистой_прибыли=cv[7])
                session.add(q)
                session.commit()
            else:
                pass
        except Exception as ex:
            print(ex)
        finally:
            os.remove("C:/Users/alkod/PycharmProjects/selen/chromedriver/Logo.png")
            # driver.close()
            # driver.quit()
    await state.finish()


async def process_timer(message: types.Message):
    """Таймер  для бота"""
    timer = await bot.send_message(chat_id=message.from_user.id, text=f"Осталось времени:{30}")
    for i in range(29, -1, -1):
        await asyncio.sleep(1)
        await timer.edit_text(f"Осталось времени:{i}")


executor.start_polling(dp, skip_updates=True, on_startup=on_startup)




