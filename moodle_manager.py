from collections import defaultdict
from getpass import getpass
from bs4 import BeautifulSoup as BS
import os
import re
import json
import requests

splash = r"""
                   .-'''-.       .-'''-.
                  '   _    \    '   _    \_______     .---.
 __  __   ___   /   /` '.   \ /   /` '.   \  ___ `'.  |   |     __.....__
|  |/  `.'   `..   |     \  '.   |     \  '' |--.\  \ |   | .-''         '.
|   .-.  .-.   |   '      |  |   '      |  | |    \  '|   |/     .-''"'-.  `.
|  |  |  |  |  \    \     / /\    \     / /| |     |  |   /     /________\   \
|  |  |  |  |  |`.   ` ..' /  `.   ` ..' / | |     |  |   |                  |
|  |  |  |  |  |   '-...-'`      '-...-'`  | |     ' .|   \    .-------------'
|  |  |  |  |  |                           | |___.' /'|   |\    '-.____...---.
|__|  |__|  |__|                          /_______.'/ |   | `.             .
 __  __   ___              _..._          \_______|/  '__.....__'-...... -'
|  |/  `.'   `.          .'     '.          .--./) .-''         '.
|   .-.  .-.   '        .   .-.   .        /.''\\ /     .-''"'-.  `..-,.--.
|  |  |  |  |  |   __   |  '   '  |   __  | |  | /     /________\   |  .-. |
|  |  |  |  |  |.:--.'. |  |   |  |.:--.'. \`-' /|                  | |  | |
|  |  |  |  |  / |   \ ||  |   |  / |   \ |/("'` \    .-------------| |  | |
|  |  |  |  |  `" __ | ||  |   |  `" __ | |\ '---.\    '-.____...---| |  '-
|__|  |__|  |__|.'.''| ||  |   |  |.'.''| | /'""'.\`.             .'| |
               / /   | ||  |   |  / /   | |||     || `''-...... -'  | |
               \ \._,\ '|  |   |  \ \._,\ '\'. __//                 |_|
                `--'  `"'--'   '--'`--'  `" `'---'
"""

# CONSTANTS
LOGIN_URLPART = 'login/index.php'
MY_COURSES_URLPART = 'my/?myoverviewtab=courses'
COURSE_VIEW_URLPART = 'course/view.php?id='
PERSIST_KEYS = ['server_url', 'username', 'password', 'download_history']
PERSIST_CHOICE_PROMPTS = ['[P]assword Username Server URL',
                          '[U]sername Server URL', '[N]othing']
PERSIST_ENUMS = [prompt[1] for prompt in PERSIST_CHOICE_PROMPTS]
DEFAULT_PERSIST_ENUM = PERSIST_ENUMS[2]
DEFAULT_PERSIST_PATH = './.moodle_data.json'


# GLOBALS
session = requests.Session()
server_url = ''
persist_dict = defaultdict(lambda: '')
persist_path = DEFAULT_PERSIST_PATH
persist_choice = ''


class Style:
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BOLD = '\033[1m'
    _END = '\033[0m'


def s_print(s, style):
    print(style + s + Style._END)


def load_from_persist():
    global persist_file, persist_dict
    if os.path.exists(persist_path):
        with open(persist_path, 'r') as persist_file:
            persist_dict = json.load(persist_file)


def get_login_data():
    global server_url, persist_dict
    login_data = persist_dict
    print(persist_dict)
    return check_for_missing_data(login_data)


def check_for_missing_data(login_data):
    show_data_and_prompt(login_data, 'server_url', 'Moodle Server URL', input)
    show_data_and_prompt(login_data, 'username', 'Moodle Username', input)
    show_data_and_prompt(login_data, 'password', 'Moodle Password', getpass)
    return login_data


def show_data_and_prompt(login_data, key, name, input_func):
    message = name + ': '
    if login_data[key] == '':
        login_data[key] = input_func(message)
    else:
        if key != 'password':
            print(message + login_data[key])
        else:
            print(message + '*' * 12)


def set_persist_choice():
    global persist_choice
    choice = persist_dict['persist_choice']
    while choice not in PERSIST_ENUMS or choice == '':
        choice = get_persist_choice_from_user()
    persist_choice = choice


def get_persist_choice_from_user():
    print('What login information would you like to remember:')
    choice = input(PERSIST_CHOICE_PROMPTS[0] + ', ' + PERSIST_CHOICE_PROMPTS[1] + ', or ' +
                   PERSIST_CHOICE_PROMPTS[2] + ' (' + DEFAULT_PERSIST_ENUM + '): ')
    if choice.strip() == '':
        choice = DEFAULT_PERSIST_ENUM
    return choice.upper()


def setup_for_scraping(server_url_local, username, password):
    global server_url
    server_url = validate_server_url(server_url_local)
    login(username, password)


def validate_server_url(server_url):
    server_url = server_url.replace('http://', 'https://')
    if not server_url.startswith('https://'):
        server_url = 'https://' + server_url
    if not server_url.endswith('/'):
        server_url = server_url + '/'
    return server_url


def login(username, password):
    payload = {
        'logintoken': get_session_id(),
        'username': username,
        'password': password
    }
    session.post(server_url + LOGIN_URLPART, data=payload)


def get_session_id():
    soup = BS(session.get(server_url + LOGIN_URLPART).text, 'html.parser')
    return soup.find('input', attrs={'name': 'logintoken'})['value']


def main_menu():
    choice = int(input('''
MENU
1. Get all documents from current semester courses
2. Get all documents from all accessible courses

'''))
    if choice == 1:
        return get_current_course_ids()
    elif choice == 2:
        return get_all_course_ids()


def get_all_course_ids():
    soup = get_page_soup(MY_COURSES_URLPART)
    return get_course_ids_from_soup(soup)


def get_current_course_ids():
    soup = get_page_soup(MY_COURSES_URLPART)
    temp = soup.find(id='pc-for-in-progress')
    return get_course_ids_from_soup(temp)


def get_page_soup(urlpart):
    response = session.get(server_url + urlpart)
    if(response.status_code == 200):
        return BS(response.text, 'html.parser')
    else:
        return -1


def get_course_ids_from_soup(soup):
    elements = soup.find_all(class_='card mb-3 courses-view-course-item')
    course_ids = [element.contents[1].attrs['href'].split(
        '=')[1] for element in elements]
    return course_ids


def download_all_documents_from_course_set(course_ids):
    for id in course_ids:
        if is_a_cezar_course(id):
            download_all_from_cezar_course(id)
        else:
            download_all_from_std_course(id)


def is_a_cezar_course(course_id):
    soup = get_page_soup(COURSE_VIEW_URLPART + course_id)
    CEZAR_URL = 'www.smcs.upei.ca/~ccampeanu'
    links = [str(link.get('href')) for link in soup.find_all('a')]
    cezar_links = [link for link in links if CEZAR_URL in link]
    return len(cezar_links) > 0


def download_all_from_std_course(course_id):
    soup = get_page_soup(COURSE_VIEW_URLPART + course_id)
    links = soup.find_all(class_='activityinstance')

    print('Downloading:')
    print('===========')

    for link in links:
        name = link.find(class_='instancename').text
        # if config['match'] not in name.lower() or name in config['downloaded']:
        #     continue
        print(name)
        url = link.a['href']
        document = get_moodle_document(url)
        write_document(document['document'], document['name'])
        # config['downloaded'].append(name)
        print('\t', document['name'])


def download_all_from_cezar_course(course_id):
    # semester = config['semester'].split('-')
    # year = semester[0]
    # season = semester[1]
    # course = config['course']
    # website = requests.get(
    #     'http://www.smcs.upei.ca/~ccampeanu/Teach/'
    #     + season
    #     + '/'
    #     + year
    #     + '/'
    #     + course
    #     + '/LN/'
    # )
    # html = website.text
    # links = re.findall('"(http://.*4.pdf?)"', html)

    print('Downloading:')
    print('===========')

    # for link in links:
    #     link = link[link.rfind('http'):]
    #     name = link[(link.rfind('/')+1):]
    #     print(name)
    #     document = session.get(link).content
    #     write_document(document, name)


def get_moodle_document(url):
    document = session.get(url)
    disp = document.headers['Content-disposition']
    document_name = re.findall('filename.+', disp)[0].split('"')[1]
    return {
        'document': document.content,
        'name': document_name
    }


def write_document(document, path):
    with open(path, 'wb') as file:
        file.write(document)


def write_to_persist():
    out_dict = persist_dict
    with open(persist_path, 'w+') as persist_file:
        if persist_choice == PERSIST_ENUMS[1]:
            out_dict['password'] = ''
        if persist_choice == PERSIST_ENUMS[2]:
            out_dict = {'download_history': persist_dict['download_history']}
            for key in PERSIST_KEYS:
                out_dict[key] = ''
        out_dict['persist_choice'] = persist_choice
        if persist_choice in PERSIST_ENUMS and persist_choice != '':
            json.dump(out_dict, persist_file)


# DRIVER
if __name__ == '__main__':
    s_print(splash, Style.YELLOW)

    load_from_persist()

    login_data = get_login_data()

    set_persist_choice()

    setup_for_scraping(
        login_data['server_url'], login_data['username'], login_data['password'])

    write_to_persist()  # save requested data upon login

    course_ids = main_menu()

    out = list(zip(course_ids, map(is_a_cezar_course, course_ids)))

    print('Selected courses:' + str(out))

    write_to_persist()  # update download history


# TODO: Notify user if login unsuccessful and why:
    # user/pass incorrect:
    # initial response doesn't return a useful code, need to catch later on
    # bad url
    # should be able to catch in initial response obv.
