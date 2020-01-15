import socket, sys, threading, tkinter as tk, time, queue
from tkinter import BOTH, END, LEFT
from threading import Thread
import time


user = None
activechat = None
users = []
conversations = []

# w klasie User przechowywany jest nick uzytkownika i jego wiadomosci
class User:
    def __init__(self, name=None):
        self.messages = []
        self.nick = name
    def addmessage(self, message):
        self.messages.append(message)
        print(self.messages)

class Message:
    def __init__(self, ffrom, to, message):
        self.ffrom = ffrom
        self.to = to
        self.message = message

    #wysyła do serwera wiadomość w formie #od:do:wiadomosc$
    def send(self):
        self.msg = "#" + str(self.ffrom) + ":" +str(self.to) + ":" + str(self.message) + "$"
        #print(self.msg)
        sock.send(self.msg.encode('utf-8'))



def connectClick(event, hostguess, portguess, windowhp):
    global PORT
    global HOST
    PORT = int(portguess.get())
    HOST = hostguess.get()
    windowhp.destroy()
#pierwsze okienko z hostem i portem
windowhp = tk.Tk()
windowhp.title = ("Host i Port")
windowhp.minsize(300,200)
hosttext = tk.Label(windowhp, text="Host:")
hostguess = tk.Entry(windowhp)
porttext = tk.Label(windowhp, text="Port:")
portguess = tk.Entry(windowhp)
connectButton = tk.Button(text = "Polacz")
connectButton.bind("<Button-1>", lambda event: connectClick(event,hostguess, portguess, windowhp))
hosttext.pack()
hostguess.pack()
porttext.pack()
portguess.pack()
connectButton.pack()
windowhp.mainloop()



sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))


def loginClick(event, usernameguess,window):
	message = '*' + usernameguess.get() +'$'
	global user
	global conversations
	user = User(usernameguess.get())
	sock.send(message.encode('utf-8'))
	print("zalogowano jako" + message[1:-1])
	window.destroy()


#drugie okienko z logowaniem
window = tk.Tk()
window.title = ("Logowanie")
usernametext = tk.Label(window, text="Login:")
usernameguess = tk.Entry(window)
loginButton = tk.Button(text = "Zaloguj")
loginButton.bind("<Button-1>", lambda event: loginClick(event,usernameguess,window))
usernametext.pack()
usernameguess.pack()
loginButton.pack()
window.mainloop()



def exitClick(event):
	exit(0)
def sendMessageClick(event, textField, chat):
	x = textField.get()
	msg = Message(user.nick,activechat, x)
	msg.send()
	#print(msg)
	chat.configure(state = "normal")
	chat.insert('end', user.nick + ": " + x + "\n")
	chat.configure(state = "disabled")
	for c in conversations:
		if activechat == c.nick:
			addto = c
			break
	m = user.nick+":"+activechat+":"+x
	addto.messages.append(m)
	textField.delete(0, "end") #clears textField
def updatelist():
	usersPanel.delete(0,END)
	global conversations
	for c in conversations:
		print(c.nick)
		usersPanel.insert(tk.END, c.nick)
		usersPanel.select_set(0)

def CurSelet(event): #po zaznaczeniu na liscie uzytkownikow
	value=str((usersPanel.get(usersPanel.curselection())))
	for c in conversations:
		if value == c.nick:
			global activechat
			activechat = value
			chat.configure(state = "normal")
			chat.delete('1.0', tk.END)
			chat.configure(state = "disabled")
			for m in c.messages:
				print(m)
				f,t,ms = m.split(":")
				chat.configure(state = "normal")
				chat.insert('end', f + ": " + ms +"\n")
				chat.configure(state = "disabled")
			break
	print(value, activechat)

#glowne okienko
root = tk.Tk()
root.title("Messenger")
root.minsize(600,400)
root.bind("<Return>", lambda event: sendMessageClick(event,textField, chat) ) #enter

mainFrame = tk.Frame(root)
mainFrame.grid(row=0, column=0, sticky=tk.N + tk.S + tk.W + tk.E)

root.rowconfigure(0, weight=1)
root.columnconfigure(0, weight=1)


#ChatField
chat = tk.Text(mainFrame)
chat.configure(state = "disabled")
chat.grid(column=0, row=0, sticky=tk.N + tk.S + tk.W + tk.E)

#TextFieldToSend
textField = tk.Entry(mainFrame)
textField.grid(column=0, row=1, sticky=tk.N + tk.S + tk.W + tk.E)

#SendMessageButton
buttonSend = tk.Button(mainFrame)
buttonSend["text"] = "Wyslij"
buttonSend.grid(column=0, row=2, sticky=tk.N + tk.S + tk.W + tk.E)
buttonSend.bind("<Button-1>", lambda event: sendMessageClick(event,textField, chat))


#usersPanel
usersPanel= tk.Listbox(mainFrame)
usersPanel.insert(1, "KONTAKTY")
usersPanel.grid(column=2, row=0, sticky=tk.N + tk.S + tk.W + tk.E)
#global conversations
for c in conversations:
	usersPanel.insert(tk.END, c.nick)
usersPanel.select_set(0)
target = usersPanel.get(usersPanel.curselection())
usersPanel.bind('<<ListboxSelect>>',CurSelet)

#ExitButton
buttonExit = tk.Button(mainFrame)
buttonExit["text"] = "Zamknij"
buttonExit["background"] = "gray"
buttonExit.grid(column=2, row=2, sticky=tk.N + tk.S + tk.W + tk.E)
buttonExit.bind("<Button-1>", exitClick)




def receive():
    while True:
        #msg = ""
        sock.settimeout(0.5)
        try:
            msg = sock.recv(1024)
            msg = msg.decode("utf-8", 'ignore')
        except socket.timeout as e:
            msg = ''
        sock.settimeout(None)
        #msg = sock.recv(1024)
        #msg = msg.decode('utf-8', 'ignore')
        if len(msg) > 0:
            global conversations
            print('Otrzymano wiadomosc: ', msg)
            if msg[0]=='#': #zwykla wiadomosc
                msgtemp = msg.split('$')[0]
                msgtemp = msgtemp[1:]
                f,t,m = msgtemp.split(':') #from, to, message
                print(f,t,m)
                if t == user.nick: #sprawdzenie czy wiadomosc jest skierowana do zalogowanego uzytkownika
	                for c in conversations:
	                    if f == c.nick:
	                        c.messages.append(f+':'+t+':'+m) #dodanie wiadomosci do listy wiadomosci okreslonego kontaktu
	                if f == activechat: #wyswietlenie wiadomosci jesli jest ona skierowana do aktualnie wyswietlanego kontaktu 
	                    chat.configure(state = "normal")
	                    chat.insert('end', f+': '+m+ "\n")
	                    chat.configure(state = "disabled")
            if msg[0]=='*': #wiadomosc z nowym kontaktem
                msgtemp = msg.split('$')[0]
                #msgtemp = msg[1:-2]
                msgtemp=msgtemp[1:]
                print("dolaczyl " + msgtemp +"\n")
                newcontact = User(msgtemp)
                conversations.append(newcontact)
                usersPanel.insert(tk.END, newcontact.nick)



receive_thread = Thread(target=receive)
receive_thread.start()
root.mainloop()
