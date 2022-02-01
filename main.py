import json
import smtplib
import datetime as dt
import time
import requests

# -------------------------------- E-MAIL CONFIG --------------------------------
MY_EMAIL = "my@mail.de"
MY_PASSWORD = "mypass"
MY_SMTP = "my.smtp.com"
MY_PORT = 123

send = []

# -------------------------------- GET USER DATA --------------------------------
with open("data.json", "r") as f:
    user = json.load(f)


def check_pos(data_input):
    """Erfragt die aktuelle ISS Position per 'request' und vergleicht diese mit der Nutzerposition.
    Bei einem Unterschied +-5 wird Schritt 2 eingeleitet."""
    data = data_input
    print(f"Schritt 1: Prüfe LAT/LNG - '{data['name']}'")

    my_lat = float(data["my_lat"])
    my_lng = float(data["my_lng"])

    response = requests.get(url="http://api.open-notify.org/iss-now.json")
    response.raise_for_status()
    resp_data = response.json()

    iss_lat = float(resp_data["iss_position"]["latitude"])
    iss_lng = float(resp_data["iss_position"]["longitude"])

    data["iss_lat"] = iss_lat
    data["iss_lng"] = iss_lng

    if my_lat - 5 <= iss_lat <= my_lat + 5 and my_lng - 5 <= iss_lng <= my_lng + 5:
        check_night(data)
    else:
        print("-- ISS nicht in der Nähe")


def check_night(data_input):
    """Erfragt die aktuelle Uhrzeit sowie die Nachtstunden (Sonnenuntergang - Sonnenaufgang) an der Position des Users.
    Handelt es sich um eine Nachtstunde, wird Schritt 3 eingeleitet."""
    data = data_input
    print(f"Schritt 2: Prüfe NIGHTTIME - '{data['name']}'")

    parameters = {
        "lat": data["my_lat"],
        "lng": data["my_lng"],
        "formatted": 0,
    }

    response = requests.get("https://api.sunrise-sunset.org/json", params=parameters)
    response.raise_for_status()
    resp_data = response.json()
    sunrise = int(resp_data["results"]["sunrise"].split("T")[1].split(":")[0])
    sunset = int(resp_data["results"]["sunset"].split("T")[1].split(":")[0])

    today = dt.datetime.now()
    hour = today.hour

    if hour > sunset or hour < sunrise:
        prep_mail(data)
    else:
        print("-- Nicht dunkel genug")


def prep_mail(data_input):
    """Bereitet den E-Mailversand vor: Liest die Textvorlage aus, überschreibt die benötigten Werte und leitet den
    Versandprozess ein."""
    data = data_input
    print(f"Schritt 3: Vorbereitung E-MAIL - '{data['name']}'")

    name = data['name']
    iss_lat = str(data['iss_lat'])
    iss_lng = str(data['iss_lng'])
    my_lat = str(data['my_lat'])
    my_lng = str(data['my_lng'])

    with open("./mail.txt", "r") as m:
        mail_text = m.read()
        mail_text = mail_text.replace("[NAME]", name)
        mail_text = mail_text.replace("[ISS_LAT]", iss_lat)
        mail_text = mail_text.replace("[ISS_LNG]", iss_lng)
        mail_text = mail_text.replace("[LAT]", my_lat)
        mail_text = mail_text.replace("[LNG]", my_lng)

    send_mail(data, mail_text)


def send_mail(data_input, mail_text):
    """Versendet eine E-Mail mit der eingespeisten Textvorlage. Leitet dann den Log-Prozess ein."""
    data = data_input

    print(f"Schritt 4: Senden E-MAIL - '{data['name']}'")
    e_mail = data["email"]
    with smtplib.SMTP(MY_SMTP, port=MY_PORT) as con:
        con.starttls()
        con.login(user=MY_EMAIL, password=MY_PASSWORD)
        con.sendmail(from_addr=MY_EMAIL, to_addrs=e_mail,
                     msg=f"Subject: ISS zu sehen!\n\n{mail_text}")
    print(f"ERFOLGREICH: E-Mail an '{data['name']}' gesendet.")
    log_file(data)


def log_file(data_input):
    """Erstellt einen Log-Eintrag im Textfile, sobald eine E-Mail erfolgreich verschickt wurde.
    Fügt den Namen der Liste 'send' hinzu"""
    global send
    data = data_input
    datum = dt.datetime.now()
    datum_format = f"{datum.day}.{datum.month}.{datum.year} um {datum.time()}"
    with open("log.txt", "a") as log:
        log.write(f"E-Mail an: {data['name']} am {datum_format} gesendet.\n")

    send.append(data["name"])


def countdown(s):
    """Countdown. Return 'True' sobald abgelaufen."""
    print(f"Countdown gestartet: {s} sec.")
    seconds = s
    while seconds > 0:
        dt.timedelta(seconds=seconds)
        time.sleep(1)
        seconds -= 1
    return True


# -------------------------------- CHECKS --------------------------------
while countdown(60):
    for i in user:
        if user[i]["name"] not in send:
            check_pos(user[i])
