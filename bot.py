import telebot
import time
import requests
import threading
import os

from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

token = ''
bot = telebot.TeleBot(token = token,threaded=True,num_threads=20)

utenti_registrati = {}

class Utente:
    def __init__(self, name, id_chat):
        self.name = name
        self.id = id_chat
        self.PaginaWeb = []
        self.Refresh = []
        self.ThreadAttivi = {}


    def setPaginaWeb(self, PaginaWeb):
        self.PaginaWeb.append(PaginaWeb)

    def setRefresh(self, Refresh):
        self.Refresh.append(Refresh)

    def getPaginaWeb(self,index):
        return self.PaginaWeb[index]

    def getRefresh(self, PaginaWeb):
        try:
            i = self.PaginaWeb.index(PaginaWeb)
            return self.Refresh[i]
        except Exception as e:
            bot.send_message(self.id,"Errore con la pagina web")

    def inserisci_Thread_attivo(self, nomeThread,thread_obj):
        self.ThreadAttivi[nomeThread] = thread_obj

    def getThread_attivi(self):
        return len(self.ThreadAttivi)

    def stopThread(self, nome_thread,nomefile):
        thread_obj = self.ThreadAttivi.get(nome_thread)
        self.PaginaWeb.remove(thread_obj.PaginaWeb)
        self.Refresh.remove(thread_obj.Refresh)
        thread_obj.stopit()
        self.ThreadAttivi.pop(nome_thread)
        path = os.getcwd()
        path = path + "/" + nomefile
        os.remove(path)

class Connect(Thread):
    def __init__(self,nomeThread,user,PaginaWeb):
        super(Connect, self).__init__()
        Thread.__init__(self)
        self.name = nomeThread
        Thread.setName(self,name = nomeThread)
        self.user = user
        self.PaginaWeb = PaginaWeb
        self.Refresh = None
        self._stopper = threading.Event()
        self.nomefile = None

    def run(self):
        self.Refresh = self.user.getRefresh(self.PaginaWeb)
        nomefile = str(self.user.id) + "_"
        pagina_split = self.PaginaWeb.split("/")
        for t in pagina_split:
            nomefile += t
        nomefile = nomefile + ".txt"
        self.nomefile = nomefile
        while Thread.getName(self) in self.user.ThreadAttivi:
        #while True:

            sito = requests.get(self.PaginaWeb)
            txt_conf = sito.text

            file = open(nomefile,'r')
            txt = file.read()
            file.close()

            if (txt != txt_conf):
                bot.send_message(self.user.id, "Il sito ha subito delle modifiche {} \nConnessione terminata".format(self.PaginaWeb))
                self.user.stopThread(Thread.getName(self),nomefile)
                return

            time.sleep(self.Refresh*60)

    def stopit(self):
        self._stopper.set()

    def stopped(self):
        return self._stopper.is_set()

@bot.message_handler(commands=['start'])
def start_cmd(message):
    bot.reply_to(message,"Ciao {}, sono un bot che segue le pagine web e ti avverte quando queste vengono modificate".format(message.from_user.first_name))
    bot.send_message(message.chat.id,"Questi sono i comandi che puoi inserire:\n - /start \n - /help \n - /aggiungipaginaweb \n - /riepilogo")

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message,"Questi sono i comandi che puoi inserire:\n - /start \n - /help \n - /aggiungipaginaweb \n - /riepilogo")

@bot.message_handler(commands=['aggiungipaginaweb'])
def AggiungiPaginaWeb_cmd(message):
    msg = bot.reply_to(message,"Inserisci l'URL della pagina web da seguire")
    bot.register_next_step_handler(msg, AggiungiPaginaWeb)


def AggiungiPaginaWeb(message):
    try:
        chat_id = message.chat.id
        txt_input = message.text
        temp_pagina = txt_input[0:4]
        if temp_pagina.lower() == "http":
            pagina_web = txt_input
        else:
            pagina_web = "http://" + txt_input
        name = message.from_user.first_name
        bot.send_message(chat_id,"Hai inserito: {} \nProvo a stabilire una connessione".format(pagina_web))
        try:
            html = requests.get(pagina_web)
            bot.send_message(chat_id,"Connessione stabilita")
        except Exception as e:
            msg = bot.reply_to(message,"Connessione non stabilita, reinserisci il sito web")
            bot.register_next_step_handler(msg,AggiungiPaginaWeb)
            return

        if chat_id not in utenti_registrati:
            user = Utente(name,chat_id)
            utenti_registrati[chat_id] = user
        else:
            user = utenti_registrati[chat_id]

        user.setPaginaWeb(pagina_web)
        nomefile = str(chat_id) + "_"
        pagina_split = pagina_web.split("/")
        for t in pagina_split:
            nomefile += t
        nomefile = nomefile + ".txt"
        file = open(nomefile,"w")
        file.write(html.text)
        file.close()

        msg = bot.send_message(chat_id,"Pagina inserita con successo! \nOra devi inserire ogni quanto tempo vuoi che venga effettuato il controllo. \nIl tempo minimo che puoi inserire è 5 minuti")
        bot.register_next_step_handler(msg, AggiungiRefresh_ANDConnect)
    except Exception as e:
        bot.send_message(message.chat.id,"Ops qualcosa è andato storto")

def AggiungiRefresh_ANDConnect(message):
    try:
        chat_id = message.chat.id
        refresh = message.text
        if not refresh.isdigit():
            msg = bot.reply_to(message, "Ops, non hai inserito un numero... Prova ora")
            bot.register_next_step_handler(msg, AggiungiRefresh_ANDConnect)
            return
        user = utenti_registrati[chat_id]
        refresh = int(refresh)
        if refresh < 5:
            user.setRefresh(5)
            bot.send_message(chat_id,"Ci hai provato a mettere {} minuti ma io ho messo 5 ;D".format(refresh))
        else:
                user.setRefresh(refresh)
                bot.send_message(chat_id,"Hai inserito {} minuti".format(refresh))
        bot.send_message(chat_id,"Bene... sembra che tutto sia andato a buon fine. Provo a connettermi al sito")
        nome_thread = "Thread" + "_" + str(message.chat.id) + "_" + str(user.getThread_attivi()+1)
        thread_connnessione = Connect(nome_thread,user,user.getPaginaWeb(len(user.PaginaWeb)-1))
        user.inserisci_Thread_attivo(nome_thread,thread_connnessione)
        thread_connnessione.start()
        bot.send_message(user.id,"Connesso! Ti avvertirò quando il sito verrà modificato")
    except Exception as e:
        bot.send_message(message.chat.id, "Ops qualcosa è andato storto")

def pagine_markup(id_chat):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    if utenti_registrati != {} and id_chat in utenti_registrati:
        user = utenti_registrati[id_chat]
        if user.PaginaWeb != []:
            for t in user.PaginaWeb:
                markup.add(InlineKeyboardButton(t, callback_data=t))
        else:
            markup.add(InlineKeyboardButton("Non stai seguendo nessuna pagina", callback_data="Vuoto"))
    else:
        markup.add(InlineKeyboardButton("Non stai seguendo nessuna pagina", callback_data="Vuoto"))
    return markup

@bot.callback_query_handler(func=lambda call:True)
def pagine_query(call):
    if utenti_registrati != {} and call.from_user.id in utenti_registrati:
        user = utenti_registrati[call.from_user.id]
        if user.PaginaWeb != []:
            for t in user.PaginaWeb:
                if call.data == t:
                    bot.answer_callback_query(call.id, "Sto per disconnetermi da {}".format(t))
                    bot.send_message(call.from_user.id,"Sto per disconnetermi da {}".format(t))

                    indice = user.PaginaWeb.index(t)
                    keys_thread = list(user.ThreadAttivi.keys())
                    thread_attivo = keys_thread[indice]
                    nomefile = str(user.id) + "_"
                    pagina_split = t.split("/")
                    for z in pagina_split:
                        nomefile += z
                    nomefile = nomefile + ".txt"
                    user.stopThread(thread_attivo,nomefile)
                    bot.send_message(call.from_user.id,"Disconesso")
        elif call.data == "Vuoto":
            bot.send_message(call.from_user.id,"Premi /aggiungipaginaweb per iniziare")
    elif call.data == "Vuoto":
        bot.send_message(call.from_user.id,"Premi /aggiungipaginaweb per iniziare")


@bot.message_handler(commands=['riepilogo'])
def riepilogo_cmd(message):
    bot.send_message(message.chat.id, "Pagine che sto controllando", reply_markup=pagine_markup(message.chat.id))

@bot.message_handler(func=lambda message: True)
def Faiqualcosa(message):
    bot.reply_to(message,"Scusami ma non capisco, inserisci un comando per iniziare")

#bot.enable_save_next_step_handlers(delay=2)

#bot.load_next_step_handlers()

def Salvadati():
    while True:
        file = open("private.txt","w")
        stringa = ""
        for t in utenti_registrati:
            user = utenti_registrati[t]
            stringa += str(user.id) + ","
            for i in user.PaginaWeb:
                stringa += i + ";"
            for j in user.Refresh:
                stringa += str(j) + "_"
            file.write(stringa)
        file.close()
        time.sleep(3600*4)

t1 = threading.Thread(target=Salvadati)
t1.start()

while True:
    try:
        bot.polling()
    except Exception:
        time.sleep(15)
