import requests
from dotenv import load_dotenv
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('key-file.json', scope)
client = gspread.authorize(creds)
sheet = client.open("python source").sheet1  # 'sheet1' is the first tab

records = sheet.get_all_records()

load_dotenv()
WEBHOOK_URL = os.getenv("DISCORD_API_URL")

def send_discord_message(message, level="info"):
    color_map = {
        "info": 0x3498db,    # Blue
        "warning": 0xf1c40f, # Yellow
        "error": 0xe74c3c    # Red
    }
    color = color_map.get(level.lower(), 0x3498db)

    data = {
        "embeds": [{
            "title": level.upper(),
            "description": message,
            "color": color
        }]
    }

    response = requests.post(WEBHOOK_URL, json=data)
    if response.status_code != 204:
        print("Failed to send message:", response.text)

def matchName(fullName, comment, namesDatabase, volume, paymentReason):
    fullName = fullName.lower().split()
    comment = comment.lower().split()

    surname = fullName[0]
    firstName = fullName[1]

    if len(comment) > 1:
        commentExists = True
        commentSurname = comment[0]
        commentFirstName = comment[1]
    else:
        commentExists = False
        commentSurname = ""
        commentFirstName = ""

    matchingSurnames = []

    cell = sheet.find(paymentReason)
    column = cell.col
    databaseSurname = ""
    dangerLevel = "ERROR"

    for databaseName in namesDatabase:
        databaseSurname = databaseName.get("surname")
        databaseFirstName = databaseName.get("name")
        databaseID = databaseName.get("id")
        if (databaseSurname.lower() == surname and databaseFirstName.lower() == firstName) or (commentExists and (databaseSurname.lower() == commentSurname and databaseFirstName.lower() == commentFirstName)):
            matchEntry = [databaseSurname, databaseID, databaseFirstName, comment]
            matchingSurnames.append(matchEntry)
            dangerLevel = "INFO"
    if len(matchingSurnames) == 0:
        matchRound = 2
        for databaseName in namesDatabase:
            databaseSurname = databaseName.get("surname")
            databaseFirstName = databaseName.get("name")
            databaseID = databaseName.get("id")
            sameSurname = databaseSurname
            matchingSurnames = []
            for i in range(4):
                if surname[i] != databaseSurname.lower()[i]:
                    sameSurname = ""
                    break
            if sameSurname:
                matchEntry = [databaseSurname, databaseID, databaseFirstName, comment]
                matchingSurnames.append(matchEntry)
                dangerLevel = "WARNING"

    if len(matchingSurnames) == 1:
        databaseSurname = matchingSurnames[0][0]
        databaseID = matchingSurnames[0][1]
        databaseFirstName = matchingSurnames[0][2]
        comment = matchingSurnames[0][3]
        value = sheet.cell(databaseID + 1, column).value
        if value is None:
            value = 0.0
        sheet.update_cell(databaseID + 1, column, float(value) + volume)
        send_discord_message(f"Payment matched with exactly 1 database name \nname: {databaseFirstName} {databaseSurname} \nid: {databaseID} \ncomment: {comment} \nvolume: {volume}", dangerLevel)

    elif len(matchingSurnames) == 0:
        send_discord_message(f"Payment matched with no database name \nsender name: {fullName} \ncomment: {comment} \nvolume: {volume}", "ERROR")

    else:
        send_discord_message(f"Payment matched with multiple database name \nsender name: {fullName} \ncomment: {comment} \nvolume: {volume}","ERROR")

api_key = os.getenv("BANK_API_KEY")

try:
    y = requests.get(f'https://fioapi.fio.cz/v1/rest/set-last-date/{api_key}/2025-04-28/')
    # Get the transactions since that date
    x = requests.get(f'https://fioapi.fio.cz/v1/rest/last/{api_key}/transactions.json')

    # Ensure the request succeeded
    x.raise_for_status()

    parsed_data = x.json()
    transactions = parsed_data["accountStatement"]["transactionList"]["transaction"]

    if not transactions:
        print("No transactions found.")
    else:
        for txn in transactions:
            volume = txn.get("column1", {}).get("value", "N/A")
            name = txn.get("column10", {}).get("value", "N/A")
            comment = txn.get("column16", {}).get("value", "N/A") if txn.get("column16") else "N/A"

            print(f"Volume: {volume}")
            print(f"Name: {name}")
            print(f"Comment: {comment}")
            matchName(name, comment, records, volume, "fotky")

except requests.exceptions.RequestException as e:
    print(f"Network or API error: {e}")
except (KeyError, IndexError) as e:
    print(f"Data parsing error: {e}")


