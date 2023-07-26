import requests
from aiogram import Bot, Dispatcher,types, executor
from aiogram.dispatcher.filters.state import State,StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TokenAPI,ChinaSiteURL,ShortChinaSiteURL,urlCalc,LinkCalc

from urllib.parse import urlparse, parse_qs,quote
import json
from datetime import datetime

bot = Bot(token=TokenAPI)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class ChinaSite(StatesGroup):
    price_state = State()


# Описание переменных калькулятора
calculate = "1" #idcalc
owner = "1"     #физ лицо
age = ["0-3","3-5","5-7","7-0"]
engine = {'Бензиновый':"1",'Дизельный':"2",'Гибридный':"3",'Электрический':"4",}
power_unit =2 #KW
currency = ['USD','EUR','CNY','RUB']
currencyindex = 2
car_price = 0
headers = {
  'Cookie': 'PHPSESSID=a1flblfl5n8aaf15snnb7aemmr; last_used=Customs'
}
files=[

]

      
@dp.message_handler(state=None)
async def GetAutoInfo(message: types.Message, state: FSMContext):
   
    text = message.text
    if text.startswith(ShortChinaSiteURL):
        current_state = await state.get_state()
        await message.reply(f'Введи цену в {currency[currencyindex]}')
        await ChinaSite.price_state.set()
        async with state.proxy() as data:
            data["URL"] = text   
            data["message_id"] = message.message_id   
    else:       
        await message.reply(text='Я не знаю, что мне с этим делать. Работаю только с сайтом guazi.com')

# Сюда приходит ответ с ценой
@dp.message_handler(state=ChinaSite.price_state)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("URL")
    URLmessage_id = data.get("message_id")
    car_price = message.text    
    parsed_url = urlparse(text)
    test = parse_qs(parsed_url.query)
    clue_id = test['clueId']
    data ={"versionId" : "0.0.0.0", 
            "sourceFrom" : "wap", 
            "deviceId" : "b502f548-40b5-4c88-b419-d6be32fbcbaf", 
            "osv" : "Windows+10", 
            "clueId" : clue_id[0], 
            "platfromSource" : "wap"       
            }
    response = requests.get(ChinaSiteURL, params=data)
    
    json_data = response.json()
    # with open('3.json',encoding='utf-8') as file:
    #     json_data = json.load(file)

    datebuild=car_weight=electricengineinfo=fuelengineinfo =motor_type=''
    data = json_data['data']['list']
    for records in data: 
        if records['id']==1:
            for children in records['children']: 
                if children['id']==4:
                    datebuild = children['content']
        elif records['id']==2:
            motor_power=motor_volume=''
            if records['title']=='发动机':
                motor_type = 'Бензиновый'
                
            for children in records['children']: 
                if children['id']==3:
                    motor_volume = children['content']
                elif children['id']==10:
                    motor_power =children['content']
            fuelengineinfo = TemplateText ="Двигатель {}\nМощность(kW) {}\nОбъем(L) {}".format(motor_type,motor_power,motor_volume)
        elif records['id']==3:
            motor_power=''
            if records['title']=='电动机':
                if motor_type == 'Бензиновый':
                    motor_type = 'Гибридный'
                else:
                    motor_type = 'Электрический'
            for children in records['children']: 
                if children['id']==2:
                    motor_power = children['content']
            electricengineinfo = TemplateText ="Двигатель {}\nМощность(kW) {}".format(motor_type,motor_power)
                
                    
        elif records['id']==5:
            
            for children in records['children']: 
                if children['id']==14:
                    car_weight =children['content']
    
    date_str = datebuild
    date = datetime.strptime(date_str, '%Y.%m')
    current_date  = datetime.now()
    year = current_date .year-date.year
    if year <= 3:
        ageindex = 0
    elif year > 3:
        ageindex = 1
    elif year > 5:
        ageindex = 2
    elif year > 7:
        ageindex = 3
    else:
        ageindex = 0
        
        # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
        # markup.row('🏎 до 3️⃣','🚗 до 5️⃣','🛻 до 7️⃣','🛺 свыше 7️⃣')
        
        # await message.reply(text='Выберите возраст машины',reply_markup=markup)
        
        
         
    payload = {"calculate": calculate,
                "owner": owner,
                "age": age[ageindex],
                "engine": engine[motor_type],
                "power": motor_power,
                "power_unit": power_unit,
                "value": float(motor_volume)*1000,
                "price": car_price,
                "currency": currency[currencyindex]}
    response = requests.request("POST", urlCalc, headers=headers, data=payload, files=files)
    json_data = response.json()
    strpayload = quote(str(payload).replace("'",'"'))
    TemplateText ="Выпуск {}\n{}\n{}\nПлатеж: {}\nИтого: {}\nСсылка на расчет:\n{}".format(datebuild,fuelengineinfo,electricengineinfo,json_data['total'],json_data['total2'],LinkCalc+strpayload)
    
    await state.finish()
    await bot.send_message(message.from_user.id, TemplateText, reply_to_message_id=URLmessage_id)
    
    

if __name__=='__main__':
    executor.start_polling(dp)