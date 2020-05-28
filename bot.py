import requests
import json
import time
import datetime 
from threading import Thread
import sys, signal
import requests.packages.urllib3

#errors
requests.packages.urllib3.disable_warnings()

##init
BOT_KEY					= "BOTKEY" #edit this
URL_UPDATES				= "https://api.telegram.org/bot"+BOT_KEY+"/getUpdates"
USER 					= "AKSIS_USERNAME" #edit this
PASS 					= "AKSIS_PASSWORD" #edit this
session 				= requests.session()
old_dat 				= ""
new_dat 				= ""
NOT_KONTROL_TIME 			= 2	# Aksis chech interval (1 request in 2 sec)
TELEGRAM_KONTROL_TIME 			= 0.3	# Telegram check interval (1 request in 0.3 sec)
CHAT_ID 				= "CHAT_ID" #edit this
YIL 					= "2019" #edit this, 
DONEM 					= "1" #edit this,  Guz=1 Bahar=2 
kill_sinyali 				= 0 
##

#Func Part
def mesaj_at(mesaj):
	SEND_MSG_URL 	= "https://api.telegram.org/bot"+BOT_KEY+"/sendMessage?chat_id="+CHAT_ID+"&parse_mode=Markdown&text=```"+mesaj+"```"
	requests.get(SEND_MSG_URL)

def oturum_cookie_al():
	burp0_url 		= "http://aksis.istanbulc.edu.tr:80/Account/LogOn"
	burp0_cookies 	= {"_ga": "GA1.3.288573048.1575306714"}
	burp0_headers 	= {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/x-www-form-urlencoded", "Connection": "close", "Referer": "http://aksis.istanbulc.edu.tr/Account/LogOn?ReturnUrl=%2f&AspxAutoDetectCookieSupport=1", "Upgrade-Insecure-Requests": "1"}
	burp0_data		= {"UserName": USER, "Password": PASS}
	session.post(burp0_url, headers=burp0_headers, cookies=burp0_cookies, data=burp0_data)
 	session.get("http://obs.istanbulc.edu.tr")

def notlari_getir(user,password):
	global YIL
	global DONEM
	burp0_url 		= "http://obs.istanbulc.edu.tr/OgrenimBilgileri/SinavSonuclariVeNotlar/GetOgrenciSinavSonuc"
	burp0_headers 	= {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0", "Accept": "*/*", "Accept-Language": "en-US,en;q=0.5", "Accept-Encoding": "gzip, deflate", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "Origin": "http://obs.istanbulc.edu.tr", "Connection": "close", "Referer": "http://obs.istanbulc.edu.tr/OgrenimBilgileri/SinavSonuclariVeNotlar/Index"}
	burp0_data 		= {"sort": '', "group": "DersAdi-asc", "filter": '', "yil": str(YIL), "donem": str(DONEM)}
	ret1 			= session.post(burp0_url, headers=burp0_headers,   data=burp0_data)
	if "/Account/LogOn" in ret1.text:
		oturum_cookie_al()
		return notlari_getir(user,password)
	return ret1
 
def mesaj_kontrol():
	tmp = requests.get(URL_UPDATES).json()
	if(not tmp["result"] == []):
		tmp_id 		= tmp["result"][0]["update_id"]
		requests.get(URL_UPDATES+"?offset="+str(tmp_id+1))
		return tmp["result"][0]["message"]["text"]
	else:
		return ""

def tum_notlari_gonder(new_dat):
	not_msg				=""
	not_msg 			= not_msg + "Notlar\n" 
	ders_sayisi			= len(new_dat["Data"])
	for i in range(0,ders_sayisi):
		not_msg			=  not_msg + "-----------------------------------\n"
		not_msg			=  not_msg + new_dat["Data"][i]["Key"]+"\n"
		girdi_sayisi 	= len(new_dat["Data"][i]["Items"])
		for x in range(0,girdi_sayisi):
			not_msg 	= not_msg + new_dat["Data"][i]["Items"][x]["Notu"]+"\n"
	not_msg 			= not_msg + "-----------------------------------\n"
	not_msg 			= not_msg + str(datetime.datetime.now()) 
	mesaj_at(not_msg)

def telegram_kontrol(old_dat):
	global YIL
	global DONEM
	global kill_sinyali
	while True:
		if kill_sinyali:
			break
		time.sleep(TELEGRAM_KONTROL_TIME)
		mesaj = mesaj_kontrol()
		if(mesaj == ""):
			continue
		if("/yil" in mesaj and len(mesaj)!=4):
			if len(mesaj.split(' '))==3:
				YIL 	= str(mesaj.split(' ')[1])
				DONEM 	= str(mesaj.split(' ')[2])
				old_dat = notlari_getir(USER,PASS).json()
				mesaj_at(" Yil "+YIL+" ve Donem "+DONEM+" olarak degisitirildi!")
			continue
		if(mesaj == "/not"):
			tum_notlari_gonder(old_dat)
			continue
		if(mesaj == "/yil"):
			mesaj_at(" Yil "+YIL+" ve Donem "+DONEM+" olarak set edilmis.")
			continue
		if(mesaj == "/guncel_not"):
			tum_notlari_gonder(notlari_getir(USER,PASS).json())
			continue
		if(mesaj == "/start"):
			mesaj_at("Naber ;)\n\nMevcut Fonk;\n1. /not : Suanki Notlar\n2. /guncel_not : Aksisden guncel notlari getir.\n3. /yil 2020 1 : Yili ve donemi degistir.\n4. /yil : Gecerli yil ve donemi dondurmektedir.\n")
			continue
		if(mesaj == "/kapat"):
			mesaj_at(" Kapatiliyor")
			kill_threads()
			sys.exit(0)
		mesaj_at("Sen_Hayirdir?")

def aksis_kontrol(old_dat):
	global kill_sinyali
	while True:
		if kill_sinyali:
			break
		try:
			time.sleep(NOT_KONTROL_TIME)
			new_dat 	=  notlari_getir(USER,PASS).json()
			if(new_dat 	!= old_dat):
				tum_notlari_gonder(new_dat)
				old_dat 	= new_dat
		except:
			print "Aksisden notlar getirilirken hata olustu."

def kill_threads():
	global kill_sinyali
	kill_sinyali = 1


 

def main():
	mesaj_at(" Aksis bot basliyor ...")
	oturum_cookie_al() #Gerekli cookie yi 1 kez al
	old_dat 	= notlari_getir(USER,PASS).json()
	try:
		telegram_kontrol_thread = Thread(target = telegram_kontrol, args = (old_dat,)).start()
		aksis_kontrol_thread 	= Thread(target = aksis_kontrol, 	args = (old_dat,)).start()
	except (KeyboardInterrupt, SystemExit):
		kill_threads()
		sys.exit(1)
 

##
main()
