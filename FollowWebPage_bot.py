import telepot
import time
import requests
from urllib.request import urlopen
from threading import Thread

class Connect (Thread):
    def __init__(self,nomefile):
        Thread.__init__(self)
        self.nomeFile = nomefile

    def run(self):
        while (PaginaWeb["TempoRefresh"] != []):
            sito = requests.get(PaginaWeb["URL"])
            nomefileconf = str(PaginaWeb["id_chat"]) + "_conf.html"
            InserimentoInFile(nomefileconf,sito.text)

            file = open(self.nomeFile)
            txt = file.read()

            file_conf = open(nomefileconf)
            txt_conf = file_conf.read()

            if txt_conf != txt:
                bot.sendMessage(PaginaWeb["id_chat"],"Il sito ha subito delle modifiche")
                bot.sendMessage(PaginaWeb["id_chat"],"Connessione terminata, se vuoi continuare a seguire questa pagina rieffettua la registrazione del sito, /help")
                PaginaWeb["URL"] = []
                PaginaWeb["TempoRefresh"] = []
                return
            else:
                continue
            file.close()
            file_conf.close()
            time.sleep(int(PaginaWeb["TempoRefresh"])*60)

# Connessione al bot
token = ''
bot = telepot.Bot(token)
global cronologia
cronologia = []
PaginaWeb = {"id_chat":[], "URL":[], "TempoRefresh" :[]}
def stampaHelpStart():
    return 'Questi sono i comandi che puoi inserire:\n - /start \n - /help \n - /aggiungipaginaweb \n - /setrefresh \n - /connect \n - /stop'


# Funzione per far rispondere al bot
def on_chat_message(msg):
    tipo_contenuto, chat, id_chat = telepot.glance(msg)
    if tipo_contenuto == 'text':
        nome = msg["from"]["first_name"]
        txt = msg["text"]
        global cronologia
        cronologia.append(txt)
        if '/start' in txt:
            bot.sendMessage(id_chat,'Ciao {}, sono un bot che segue le pagine web e ti avverte quando queste vengono modificate'.format(nome))
            bot.sendMessage(id_chat,stampaHelpStart())

        elif '/help' in txt:
            bot.sendMessage(id_chat,stampaHelpStart())

        elif '/aggiungipaginaweb' in txt:
            bot.sendMessage(id_chat,"Inserisci l'URL della pagina web da seguire, non inserire http:// oppure https://")
        elif cronologia[len(cronologia)-2] == '/aggiungipaginaweb':
            AggiungiPaginaWeb(id_chat,cronologia[len(cronologia)-1])
            cronologia[:] = []
            bot.sendMessage(id_chat,"Pagina aggiunta con successo, ora clicca /setrefresh")

        elif '/setrefresh' in txt:
            bot.sendMessage(id_chat,"Inserisci il Refresh della pagina web da seguire (minimo 10 minuti)")
        elif cronologia[len(cronologia)-2] == '/setrefresh':
            if int(txt) < 10:
                SetRefresh(id_chat,10)
            else:
                SetRefresh(id_chat,txt)
            cronologia[:] = []
            bot.sendMessage(id_chat, "Tempo di ricarica aggiunto con successo, ora clicca /connect")

        elif '/connect' in txt:
            bot.sendMessage(id_chat,"Connessione...")
            nomefile = (str(id_chat)+ "_html.html")
            try:
                html = requests.get(PaginaWeb["URL"])
            except Exception as e:
                bot.sendMessage(id_chat,"Errore di connessione")
                return
            InserimentoInFile(nomefile,html.text)
            bot.sendMessage(id_chat, "Connesso, ti avvertirò quando la pagina verrà modificata")
            thread_connessione = Connect(nomefile)
            thread_connessione.start()

        elif 'stop' in txt:
            PaginaWeb["URL"] = []
            PaginaWeb["TempoRefresh"] = []
            bot.sendMessage(PaginaWeb["id_chat"],"Connessio terminata")


        else:
            bot.sendMessage(id_chat,'Controlla perchè non trovo questo comando')



def AggiungiPaginaWeb(id_chat, URL):
    if id_chat == PaginaWeb["id_chat"]:
        PaginaWeb["URL"] = "http://" + URL
        return
    else:
        PaginaWeb["id_chat"] = id_chat;
        PaginaWeb["URL"] = "http://" + URL
        return

def SetRefresh(id_chat,Refresh):
    if id_chat == PaginaWeb["id_chat"]:
        PaginaWeb["TempoRefresh"] = Refresh
        return
    else:
        bot.sendMessage(id_chat,"Errore")

def InserimentoInFile(nomeFile,testo):
    file = open(nomeFile,"w")
    file.write(testo)
    file.close()

# Funzione che prende in input i messaggi inviati al bot e come parametro gli viene passata la funzione
bot.message_loop(on_chat_message)

print ('Online')

while 1:
    time.sleep(1)
