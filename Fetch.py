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

    for databaseName in namesDatabase:
        databaseSurname = databaseName.get("surname")
        databaseFirstName = databaseName.get("name")
        databaseID = databaseName.get("id")
        if (databaseSurname.lower() == surname and databaseFirstName.lower() == firstName) or (commentExists and (databaseSurname.lower() == commentSurname and databaseFirstName.lower() == commentFirstName)):
            print(databaseSurname)
            matchEntry = [databaseSurname, databaseID]
            matchingSurnames.append(matchEntry)
    if len(matchingSurnames) == 0:
        for databaseName in namesDatabase:
            databaseSurname = databaseName.get("surname")
            databaseID = databaseName.get("id")
            sameSurname = databaseSurname
            matchingSurnames = []
            for i in range(4):
                if surname[i] != databaseSurname.lower()[i]:
                    sameSurname = ""
                    break
            if sameSurname:
                print(databaseSurname)
                matchEntry = [databaseSurname, databaseID]
                matchingSurnames.append(matchEntry)
    print(matchingSurnames)

    if len(matchingSurnames) == 1:
        databaseSurname = matchingSurnames[0][0]
        databaseID = matchingSurnames[0][1]
        value = sheet.cell(databaseID + 1, column).value
        if value is None:
            value = 0.0
        sheet.update_cell(databaseID + 1, column, float(value) + volume)

    elif len(matchingSurnames) == 0:
        print("No match found")

    else:
        print("Multiple matches found")
        for match in matchingSurnames:
            print(match)

load_dotenv()
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


