import telebot
from telebot import types
import requests
import datetime
import re
from pythonping import ping
import logging

token='5315004947:AAGes0qxhT4BOV_aX0mKpbavj84duB8mXUo'
bot=telebot.TeleBot(token)
cookies = {'bkapisessionid': 'sGAdN16x3b'}
prmssn=[281881098,258106109,446680241,424049654,546590932,663743746]
response=requests.get('https://crm.businesskassa.ru/frs/10.55.9.99', cookies=cookies)


def testIP(object):      
    L=object.split(' ', 1)
    if re.match(r"^(10\.55\.)(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$", L[0])!=None:
    	urlFR='https://api.businesskassa.ru/v1/frs/'+L[0]
    	return True, urlFR, L[0]
    elif re.match(r"^(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9][0-9]|[0-9])$", L[0])!=None:
    	urlFR='https://api.businesskassa.ru/v1/frs/10.55.'+L[0]
    	return True, urlFR, '10.55.'+L[0]
    else:
    	return False

@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, 'IP указывается в формате X.X или X.X.X.X, регистр букв не важен\n\nГараж - выдаст количество свободных касс всех типов\nIP - выдаст расположение и серийный номер кассы\n\nIP ping - пинг IP кассы\n\nIP clear - удалит расположение кассы\n\nIP и через пробел расположение в формате X.X.X.X - изменяет расположение кассы\n\nIP и через пробел любой текст - меняет местоположение на этот текст\n\nIP on - включает фискализацию\n\nIP off - выключает фискализацию\n\nИНН дд.мм.гггг - устанавливает для ИНН дату окончания аренды')

@bot.message_handler(content_types=['text'])
def send_text(message):
    
    #Включение логгирования
    dtn = datetime.datetime.now()
    botlogfile = open('BKbot.log', 'a')
    print(dtn.strftime("%d-%m-%Y %H:%M"), 'Пользователь ' + message.from_user.first_name, message.from_user.id, 'написал следующее: ' + message.text, file=botlogfile)
    botlogfile.close()
    
    #Авторизация пользователя
    print(response.status_code)
    if message.chat.id not in prmssn:
        print(message.chat.id)
        bot.send_message(message.chat.id, "Доступ закрыт")
    elif response.status_code==401:
        bot.send_message(message.chat.id, "Просрочены куки")
        print(response.status_code)
    elif response.status_code>=500:
        bot.send_message(message.chat.id, "Ошибка сервера")
        
    #Основной блок
    else:
        #Запрос IP и SN
        if testIP(message.text) and message.text.replace('.','',-1).isdigit():
            res = requests.get(testIP(message.text)[1], cookies=cookies)
            if res.status_code==200:
                try:
                    bot.send_message(message.chat.id, f"Расположение: {res.json()['placement']}, SN: {res.json()['sn']}")
                except:
                    bot.send_message(message.chat.id, f"Расположение: , SN: {res.json()['sn']}")
            else:
                bot.send_message(message.chat.id, "Кассы с таким IP не зарегистрировано")

        #Запрос количества свободных касс всех видов
        elif message.text.lower()=='гараж':
            url='https://api.businesskassa.ru/v1/frs/avaiable'
            req = requests.get(url, cookies=cookies)
            Q=len(req.json())
            FA36=0
            FA15=0
            FS36=0
            FS15=0
            for i in range(0,Q):
                if "terminalfa" in req.json()[i]["type"] and "996144" in req.json()[i]['fs']["sn"]:
                    FA36+=1
                elif "terminalfa" in req.json()[i]["type"] and "996044" in req.json()[i]['fs']["sn"]:
                    FA15+=1
                elif "pkfs" in req.json()[i]["type"] and "996144" in req.json()[i]['fs']["sn"]:
                    FS36+=1
                elif "pkfs" in req.json()[i]["type"] and "996044" in req.json()[i]['fs']["sn"]:
                    FS15+=1
                else:
                    print("Нет доступных касс")
            bot.send_message(message.chat.id, f"ФА36: {FA36} шт\nФА15: {FA15} шт\nФС36: {FS36} шт\nФС15: {FS15} шт")
        #Отключение фискализации
        elif testIP(message.text) and 'off' in message.text.lower():
            req=requests.get(testIP(message.text)[1], cookies=cookies)
            global IP
            IP=testIP(message.text)[2]
            global inn
            inn=req.json()['reg']['inn']
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton("пере-\nрегистрация")
            btn2 = types.KeyboardButton("пере-\nпрошивка")
            btn3 = types.KeyboardButton("закрытие ФН")
            btn4 = types.KeyboardButton("изменение местоположения")
            btn5 = types.KeyboardButton("технические работы")
            btn6 = types.KeyboardButton("должник")
            markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
            bot.send_message(message.chat.id, text="Укажите причину", reply_markup=markup)
        elif message.text.lower() == "пере-\nрегистрация":
            try:                
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+IP+'/deactivate'
                data={"reason": "перерегистрация"}
                req=requests.patch(url, cookies=cookies, json=data)
                bot.send_message(message.chat.id, f"Фискализация {IP} выключена по причине: перерегистрация", reply_markup=types.ReplyKeyboardRemove())
            except:            
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует",reply_markup=types.ReplyKeyboardRemove() )
        elif message.text.lower() == "пере-\nпрошивка":
            try:                
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+IP+'/deactivate'
                data={"reason": "перепрошивка"}
                req=requests.patch(url, cookies=cookies, json=data)
                bot.send_message(message.chat.id, f"Фискализация {IP} выключена по причине: перепрошивка", reply_markup=types.ReplyKeyboardRemove())
            except:            
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует", reply_markup=types.ReplyKeyboardRemove()) 
        elif message.text.lower() == "закрытие ФН":
            try:               
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+IP+'/deactivate'
                data={"reason": "закрытие ФН"}
                req=requests.patch(url, cookies=cookies, json=data)
                bot.send_message(message.chat.id, f"Фискализация {IP} выключена по причине: закрытие ФН", reply_markup=types.ReplyKeyboardRemove())
            except:            
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует", reply_markup=types.ReplyKeyboardRemove())
        elif message.text.lower() == "изменение местоположения":
            try:
                
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+IP+'/deactivate'
                data={"reason": "изменение местоположения"}
                req=requests.patch(url, cookies=cookies, json=data)
                bot.send_message(message.chat.id, f"Фискализация {IP} выключена по причине: изменение местоположения", reply_markup=types.ReplyKeyboardRemove())
            except:            
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует", reply_markup=types.ReplyKeyboardRemove())
        elif message.text.lower() == "технические работы":
            try:
                
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+IP+'/deactivate'
                data={"reason": "технические работы"}
                req=requests.patch(url, cookies=cookies, json=data)
                bot.send_message(message.chat.id, f"Фискализация {IP} выключена по причине: технические работы", reply_markup=types.ReplyKeyboardRemove())
            except:            
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует", reply_markup=types.ReplyKeyboardRemove())
        elif message.text.lower() == "должник":
            try:                
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+IP+'/deactivate'
                data={"reason": "должник"}
                req=requests.patch(url, cookies=cookies, json=data)
                bot.send_message(message.chat.id, f"Фискализация {IP} выключена по причине: должник", reply_markup=types.ReplyKeyboardRemove())
            except:            
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует",reply_markup=types.ReplyKeyboardRemove() )


        #Включение фискализации
        elif testIP(message.text) and 'on' in message.text.lower():
            req=requests.get(testIP(message.text)[1], cookies=cookies)
            try:
                inn=req.json()['reg']['inn']
                url='https://api.businesskassa.ru/v1/orgs/'+inn+'/fcircuit/frs/'+testIP(message.text)[2]+'/activate'
                req=requests.patch(url, cookies=cookies)
                bot.send_message(message.chat.id, f"Фискализация {testIP(message.text)[2]} включена")
            except:
                bot.send_message(message.chat.id, f"Ошибка! Контур фискализации {IP} отсутсвует")
                
        #Очищение расположения кассы
        elif testIP(message.text) and "clear" in message.text.lower():
            req=requests.get(testIP(message.text.lower())[1], cookies=cookies)
            y=req.json()['placement']
            data={'placement':''}
            req=requests.patch(testIP(message.text.lower())[1], cookies=cookies, json=data)
            bot.send_message(message.chat.id, f"Расположение {testIP(message.text.lower())[2]} изменено c {y} на пустое")
            
        #Пинг кассы
        elif testIP(message.text) and "ping" in message.text.lower():
            y=ping(testIP(message.text.lower())[2])           
            bot.send_message(message.chat.id, y)

        #Изменение местоположения кассы
        elif testIP(message.text) and len(message.text.split(' '))>=2:
            Spl=message.text.split(' ', 1)
            req=requests.get(testIP(message.text)[1], cookies=cookies)
            y=req.json()['placement']
            data={'placement':Spl[1]}
            req=requests.patch(testIP(message.text)[1], cookies=cookies, json=data)
            bot.send_message(message.chat.id, f"Расположение {testIP(message.text)[2]} изменено c {y} на {Spl[1]}")     
        # Установить срок аренды по ИНН
        elif message.text.lower().count('.')==2 and len(message.text.lower())>=21:
            inn = message.text.split(' ')[0]
            try:
                new_date = datetime.datetime.strptime(message.text.split(' ')[1], "%d.%m.%Y").strftime("%Y-%m-%d")
                url =  'https://api.businesskassa.ru/v1/orgs/' + inn
                req = requests.get(url, cookies=cookies)
                if req.status_code==200:
                    try:
                        old_date = req.json()['t_rent_to']
                        old_date = datetime.datetime.strptime(old_date, "%Y-%m-%dT00:00:00.000Z").strftime("%Y-%m-%d")
                    except:
                        old_date = 'None'
                    json = {'t_rent_to': new_date}
                    req = requests.patch(url, cookies=cookies, json=json)
                    if req.status_code==200:
                        bot.send_message(message.chat.id, f'срок аренды у ИНН {inn} изменен с {old_date} на {new_date}')
                    else:
                        bot.send_message(message.chat.id, f'что-то пошло не так, напишите Лене')
                    status = {"pipelines":[]}
                    req=requests.patch(url, cookies=cookies, json=status)
                    if req.status_code !=200:
                        bot.send_message(message.chat.id, f'не удалось изменить статус на -действий не требуется-')
                else:
                    bot.send_message(message.chat.id, f'организация с таким ИНН не найдена, проверьте длину/правильность ИНН')
            except:
                bot.send_message(message.chat.id, f'ошибка в формате даты, правильный формат - dd.mm.yyyy')
        else:
            print(message.text)
            bot.send_message(message.chat.id, 'Запрос неверный, введите /help для получения списка доступных команд', reply_markup=types.ReplyKeyboardRemove())
            
#Обход ошибок:)
while True:
    try:
        bot.polling()
    except:
        print("Неизвестная ошибка")
        continue
#bot.polling()

