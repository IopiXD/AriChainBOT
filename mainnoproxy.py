import requests
import json
import random
from colorama import init, Fore, Style
import time
import os
import pytz
import datetime

# Initialize colorama for colored output
init(autoreset=True)

# Constants
BASE_URL = "https://mobile.arichain.io/api/event/"
CHECKIN_URL = "https://mobile.arichain.io/api/event/checkin"
QUIZ_QUESTION_URL = BASE_URL + "quiz_q"
QUIZ_ANSWER_URL = BASE_URL + "quiz_a"
EVENTS_URL = "https://mobile.arichain.io/api/event/get_app_event_all"
SIGNIN_URL = "https://mobile.arichain.io/api/account/signin_mobile"

HEADERS = {
    "user-agent": "Dart/3.3 (dart:io)",
    "content-type": "application/x-www-form-urlencoded; charset=utf-8",
    "accept": "application/json",
    "accept-encoding": "gzip",
    "host": "mobile.arichain.io"
}
SKIP_IDS = ["3", "4", "5", "6", "18"]

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_banner():
    banner = """
    ██╗ ██████╗ ██████╗ ██╗
    ██║██╔═══██╗██╔══██╗██║
    ██║██║   ██║██████╔╝██║
    ██║██║   ██║██╔═══╝ ██║
    ██║╚██████╔╝██║     ██║
    ╚═╝ ╚═════╝ ╚═╝     ╚═╝
    Is Her :)
    AriChain Daily
    """
    print(Fore.MAGENTA + banner)

def get_wib_timestamp():
    wib_timezone = pytz.timezone("Asia/Jakarta")
    return datetime.datetime.now(wib_timezone).strftime("%Y-%m-%d %H:%M:%S")

def read_data_from_file(file_path='data.txt'):
    data_list = []
    if not os.path.exists(file_path):
        print(f"{get_wib_timestamp()} | {Fore.RED}File {file_path} not found!")
        return data_list
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split(' | ')
            if len(parts) == 4:
                email, pw, address, session_code = parts
                data_list.append({
                    "email": email,
                    "pw": pw,
                    "address": address,
                    "session_code": session_code
                })
            else:
                print(f"{get_wib_timestamp()} | {Fore.RED}Skipping invalid line: {line.strip()}")
    return data_list

def login_account(email, pw, max_retries=5):
    data = {
        "blockchain": "testnet",
        "email": email,
        "pw": pw,
        "device": "app",
        "lang": "id",
        "is_mobile": "Y"
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.post(SIGNIN_URL, headers=HEADERS, data=data, timeout=20)
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get("status") == "success":
                    session_code = result["result"]["session_code"]
                    address = result["result"]["address"]
                    print(f"{get_wib_timestamp()} | {Fore.GREEN}[SUCCESS] {email} -> Session Code: {session_code}, Address: {address}")
                    with open("data.txt", "a") as out_file:
                        out_file.write(f"{email} | {pw} | {address} | {session_code}\n")
                    return True
                else:
                    print(f"{get_wib_timestamp()} | {Fore.RED}[FAILED] {email} -> API response failed: {result}")
                    return False
            else:
                retries += 1
                wait_time = 2 ** retries
                print(f"{get_wib_timestamp()} | {Fore.YELLOW}[RETRY] {email} -> HTTP {response.status_code}, retry {retries}/{max_retries} in {wait_time}s")
                time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            retries += 1
            wait_time = 2 ** retries
            print(f"{get_wib_timestamp()} | {Fore.RED}[ERROR] {email} -> Request error: {e}, retry {retries}/{max_retries} in {wait_time}s")
            time.sleep(wait_time)
    print(f"{get_wib_timestamp()} | {Fore.RED}[ERROR] {email} -> Max retries exceeded.")
    return False

def fetch_daily_status(data, retries=7, backoff_factor=1.5):
    payload = {
        "blockchain": "testnet",
        "address": data['address'],
        "lang": "id",
        "device": "app",
        "is_mobile": "Y",
        "session_code": data['session_code']
    }
    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(CHECKIN_URL, headers=HEADERS, data=payload, timeout=15)
            if response.status_code == 200:
                response_data = response.json()
                status = response_data.get("status", "")
                if status == "success":
                    print(f"{get_wib_timestamp()} | {Fore.GREEN}Daily check-in success.")
                    return True
                elif status == "fail":
                    print(f"{get_wib_timestamp()} | {Fore.RED}Address {data['address']} - Error: {response_data.get('msg', 'Unknown error')}")
                    return False
            else:
                print(f"{get_wib_timestamp()} | {Fore.RED}Error: Unable to fetch data for address {data['address']} (HTTP {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"{get_wib_timestamp()} | {Fore.YELLOW}Request failed for address {data['address']}: {e}")
        attempt += 1
        if attempt < retries:
            wait_time = backoff_factor ** attempt
            print(f"{get_wib_timestamp()} | {Fore.YELLOW}Retrying ({attempt}/{retries})... Waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)
    print(f"{get_wib_timestamp()} | {Fore.RED}Failed to fetch data for address {data['address']} after {retries} attempts.")
    return False

def get_quiz_data(data, retries=7, backoff_factor=1.5):
    payload = {
        "blockchain": "testnet",
        "address": data['address'],
        "lang": "id",
        "device": "app",
        "is_mobile": "Y",
        "session_code": data['session_code']
    }
    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(QUIZ_QUESTION_URL, data=payload, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                data_res = response.json()
                quiz_idx = data_res["result"]["quiz_idx"]
                quiz_title = data_res["result"]["quiz_title"]
                quiz_q = data_res["result"]["quiz_q"]
                print(f"{get_wib_timestamp()} | {Fore.GREEN}Quiz Title: {quiz_title}")
                for q in quiz_q:
                    print(f"{get_wib_timestamp()} | {Fore.YELLOW}{q['q_idx']}: {q['question']}")
                return quiz_idx, quiz_title, quiz_q
            else:
                print(f"{get_wib_timestamp()} | {Fore.RED}Failed to fetch quiz data (HTTP {response.status_code})")
        except requests.RequestException as e:
            print(f"{get_wib_timestamp()} | {Fore.RED}Error fetching quiz data: {e}")
        attempt += 1
        if attempt < retries:
            wait_time = backoff_factor ** attempt
            print(f"{get_wib_timestamp()} | {Fore.YELLOW}Retrying quiz data ({attempt}/{retries})... Waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)
    print(f"{get_wib_timestamp()} | {Fore.RED}Failed to fetch quiz data after {retries} attempts.")
    return None, None, None

def submit_quiz_answer(quiz_idx, answer_idx, data, retries=7, backoff_factor=1.5):
    payload = {
        "blockchain": "testnet",
        "address": data['address'],
        "quiz_idx": quiz_idx,
        "answer_idx": answer_idx,
        "lang": "id",
        "device": "app",
        "is_mobile": "Y",
        "session_code": data['session_code']
    }
    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(QUIZ_ANSWER_URL, data=payload, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                data_res = response.json()
                result = data_res.get("result", {})
                if "msg" in result:
                    msg = result["msg"]
                    if msg == "Already taken quiz.":
                        print(f"{get_wib_timestamp()} | {Fore.CYAN}{msg}. Skipping...")
                        return True
                    print(f"{get_wib_timestamp()} | {Fore.GREEN}Response: {msg}")
                if "is_answer" in result:
                    print(f"{get_wib_timestamp()} | {Fore.GREEN}Is Answer Correct: {result['is_answer']}")
                else:
                    print(f"{get_wib_timestamp()} | {Fore.RED}Unexpected response. Response: {result}")
                return True
            else:
                print(f"{get_wib_timestamp()} | {Fore.RED}Failed to submit the answer (HTTP {response.status_code})")
        except requests.RequestException as e:
            print(f"{get_wib_timestamp()} | {Fore.RED}Error submitting answer: {e}")
        attempt += 1
        if attempt < retries:
            wait_time = backoff_factor ** attempt
            print(f"{get_wib_timestamp()} | {Fore.YELLOW}Retrying submit answer ({attempt}/{retries})... Waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)
    print(f"{get_wib_timestamp()} | {Fore.RED}Failed to submit the answer after {retries} attempts.")
    return False

def check_events(data, retries=7, backoff_factor=2):
    payload = f"blockchain=testnet&lang=id&device=app&is_mobile=Y&session_code={data['session_code']}"
    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(EVENTS_URL, headers=HEADERS, data=payload, timeout=15)
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"{get_wib_timestamp()} | {Fore.RED}Failed to fetch events (HTTP {response.status_code})")
        except Exception as e:
            print(f"{get_wib_timestamp()} | {Fore.RED}Error fetching events: {e}")
        attempt += 1
        if attempt < retries:
            wait_time = backoff_factor ** attempt
            print(f"{get_wib_timestamp()} | {Fore.YELLOW}Retrying event fetch ({attempt}/{retries})... Waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)
    print(f"{get_wib_timestamp()} | {Fore.RED}Failed to fetch events after {retries} attempts.")
    return None

def process_event(data, event_id, retries=7, backoff_factor=2):
    url = "https://arichain.io/api/event/set_app_event"
    payload = f"blockchain=testnet&email={data['email']}&address={data['address']}&event_id={event_id}&lang=id&device=app&is_mobile=Y&session_code={data['session_code']}"
    attempt = 0
    while attempt < retries:
        try:
            response = requests.post(url, headers=HEADERS, data=payload, timeout=15)
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"{get_wib_timestamp()} | {Fore.GREEN}Processed: {result}")
                return True
            else:
                print(f"{get_wib_timestamp()} | {Fore.RED}Failed to process (HTTP {response.status_code})")
        except Exception as e:
            print(f"{get_wib_timestamp()} | {Fore.RED}Error processing: {e}")
        attempt += 1
        if attempt < retries:
            wait_time = backoff_factor ** attempt
            print(f"{get_wib_timestamp()} | {Fore.YELLOW}Retrying ({attempt}/{retries})... Waiting for {wait_time:.2f} seconds")
            time.sleep(wait_time)
    print(f"{get_wib_timestamp()} | {Fore.RED}Failed to process after {retries} attempts.")
    return False

def process_account(data, quiz_idx, answer_idx, skip_completed=True):
    print(f"{get_wib_timestamp()} | {Fore.BLUE}Processing account: {data['email']}")

    data_events = check_events(data)
    if not data_events or data_events.get("status") != "success":
        print(f"{get_wib_timestamp()} | {Fore.RED}Failed to fetch events.")
        return

    result = data_events.get("result", {})
    general = result.get("general", [])
    collabs = result.get("collabs", [])
    daily = result.get("daily", {}).get("result", [])
    all_events = general + collabs + daily

    daily_checkin_status = None
    quiz_status = None
    for event in all_events:
        event_id = event.get("id")
        status = event.get("status")
        if event_id == "7":
            daily_checkin_status = status
        elif event_id == "10":
            quiz_status = status

    if daily_checkin_status == "DONE":
        print(f"{get_wib_timestamp()} | {Fore.CYAN}[SKIP] Title: Daily Check-in | Status: {daily_checkin_status}")
    else:
        print(f"{get_wib_timestamp()} | {Fore.YELLOW}[READY] Title: Daily Check-in")
        fetch_daily_status(data)

    if quiz_idx and answer_idx and quiz_status != "CORRECT":
        print(f"{get_wib_timestamp()} | {Fore.YELLOW}[READY] Title: Daily Quiz")
        submit_quiz_answer(quiz_idx, answer_idx, data)
    else:
        print(f"{get_wib_timestamp()} | {Fore.CYAN}[SKIP] Title: Daily Quiz | Status: {quiz_status or 'Not available'}")

    for event in all_events:
        event_id = event.get("id")
        status = event.get("status3") or event.get("status2") or event.get("status")
        if event_id in ["7", "10"]:
            continue
        if event_id in SKIP_IDS:
            print(f"{get_wib_timestamp()} | {Fore.CYAN}[SKIP] Title: {event.get('title')} (Excluded ID)")
            continue
        if skip_completed and status != "READY":
            print(f"{get_wib_timestamp()} | {Fore.CYAN}[SKIP] Title: {event.get('title')} | Status: {status}")
            continue
        print(f"{get_wib_timestamp()} | {Fore.YELLOW}[READY] Title: {event.get('title')}")
        process_event(data, event_id)

def get_session_codes():
    clear_terminal()
    display_banner()

    akun_list = []
    with open("akun.txt", "r") as file:
        for i, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) != 2:
                print(f"{get_wib_timestamp()} | {Fore.RED}[SKIP] Line {i} invalid format: {line}")
                continue
            email, pw = parts[0].strip(), parts[1].strip()
            akun_list.append((email, pw))

    for email, pw in akun_list:
        login_account(email, pw)
    print(f"{get_wib_timestamp()} | {Fore.BLUE}[INFO] Semua akun selesai diproses.")

def process_main():
    clear_terminal()
    display_banner()

    data_list = read_data_from_file()
    if not data_list:
        print(f"{get_wib_timestamp()} | {Fore.RED}No data found in data.txt. Exiting.")
        return

    print(f"{get_wib_timestamp()} | {Fore.BLUE}Fetching quiz data...")
    first_data = data_list[0]
    quiz_idx, quiz_title, quiz_q = get_quiz_data(first_data)
    answer_idx = None
    if quiz_idx:
        answer_idx = input(f"{get_wib_timestamp()} | {Fore.MAGENTA}Masukkan id Quiz (e.g., 388): {Style.RESET_ALL}").strip()

    for data in data_list:
        process_account(data, quiz_idx, answer_idx)

def main():
    while True:
        clear_terminal()
        display_banner()
        print(f"{get_wib_timestamp()} | {Fore.BLUE}Choose an option:")
        print(f"{get_wib_timestamp()} | {Fore.YELLOW}1. Get Session Codes")
        print(f"{get_wib_timestamp()} | {Fore.YELLOW}2. Process Accounts Daily + Quizz + Clear task")
        print(f"{get_wib_timestamp()} | {Fore.YELLOW}3. Exit")
        choice = input(f"{get_wib_timestamp()} | {Fore.MAGENTA}Enter your choice (1-3): {Style.RESET_ALL}").strip()

        if choice == "1":
            get_session_codes()
        elif choice == "2":
            process_main()
        elif choice == "3":
            print(f"{get_wib_timestamp()} | {Fore.BLUE}Exiting program.")
            break
        else:
            print(f"{get_wib_timestamp()} | {Fore.RED}Invalid choice. Please select 1, 2, or 3.")
        input(f"{get_wib_timestamp()} | {Fore.MAGENTA}Press Enter to continue...{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
