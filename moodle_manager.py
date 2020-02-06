from collections import defaultdict
from getpass import getpass
from bs4 import BeautifulSoup as BS
from pathlib import Path
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
PERSIST_CHOICE_PROMPTS = ['[P]assword + Username + Server URL',
                          '[U]sername + Server URL', '[N]othing']
PERSIST_ENUMS = [prompt[1] for prompt in PERSIST_CHOICE_PROMPTS]
DEFAULT_PERSIST_ENUM = PERSIST_ENUMS[1]
DEFAULT_PERSIST_PATH = './.moodle_data.json'
DEFAULT_DOWNLOAD_PATH = './moodle_course_documents/'
CEZAR_URL_FILTER = 'www.smcs.upei.ca/~ccampeanu'
MOODLE_DOCUMENT_FILTER = 'mod/resource'


# GLOBALS
session = requests.Session()
server_url = ''
download_history = dict()
download_path = DEFAULT_DOWNLOAD_PATH
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


def s_print_after(s, style, a):
    print(s, end='')
    s_print(a, style)


def load_from_persist():
    global persist_file, persist_dict, download_history
    if os.path.exists(persist_path):
        with open(persist_path, 'r') as persist_file:
            persist_dict = json.load(persist_file)
            download_history = persist_dict['download_history']


def get_login_data():
    global server_url, persist_dict
    login_data = persist_dict
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
    server_url = clean_server_url(server_url_local)
    login(username, password)


def clean_server_url(server_url):
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
    choice = ''
    while choice not in '12' or choice == '':
        choice = (input('''
MENU
1. Get all documents from current semester courses
2. Get all documents from all accessible courses

'''))
    if choice == '1':
        return get_current_course_ids()
    elif choice == '2':
        return get_all_course_ids()
    else:
        print('Please enter a menu NUMBER')


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
        print(response.url)
        print(response.status_code)
        return -1


def get_course_ids_from_soup(soup):
    elements = soup.find_all(class_='card mb-3 courses-view-course-item')
    course_ids = [element.contents[1].attrs['href'].split(
        '=')[1] for element in elements]
    return course_ids

# get_course_ids_from_soup ALTERNATIVE - zip name at this point
    # elements = temp.find_all('a')
    # course_a_tags = [a_tag for a_tag in elements if COURSE_VIEW_URLPART in a_tag.attrs['href']
    #                   and not any(map(lambda x: True if '<div ' in str(x) else False, a_tag.contents))]
    # course_ids = [course.attrs['href'].split('=')[1] for course in course_a_tags]
    # course_names = [course.contents[0] for course in course_a_tags]
    # return(list(zip(course_ids, course_names)))


def download_all_documents_from_course_set(course_ids):
    [download_all_documents_from_course(course_id) for course_id in course_ids]
    s_print_after('ALL SELECTED COURSES ', Style.GREEN, 'DONE')


def download_all_documents_from_course(course_id):
    soup = get_page_soup(COURSE_VIEW_URLPART + course_id)
    course_name = str(soup.find('h1').contents[0])
    print('Downloading ' + course_name + '...')
    links = [str(link.get('href')) for link in soup.find_all('a')]

    if not is_cezar_course(links):
        download_all_from_std_course(links, course_name)
    else:
        download_all_from_cezar_course(links, course_name)
    s_print_after('Downloading ' + course_name, Style.GREEN, ' DONE')


def is_cezar_course(links):
    cezar_links = [link for link in links if CEZAR_URL_FILTER in link]
    return len(cezar_links) > 0


def download_all_from_std_course(links, course_name):
    path = download_path + course_name + '/'
    document_links = [link for link in links if (
        server_url + MOODLE_DOCUMENT_FILTER) in link]

    for link in document_links:
        if link not in download_history.keys():
            document = get_moodle_document(link)
            s_print_after('\t' + document[1], Style.GREEN, ' DONE')
            write_document(document[0], path, document[1])
            download_history[document[2]] = document[1]
        else:
            s_print_after(
                '\t' + download_history[link], Style.YELLOW, ' PREVIOUSLY DOWNLOADED')


def download_all_from_cezar_course(links, course_name):
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

    # for link in links:
    #     link = link[link.rfind('http'):]
    #     name = link[(link.rfind('/')+1):]
    #     print(name)
    #     document = session.get(link).content
    #     write_document(document, name)
    print('CEZAR COURSE: ' + course_name + ' - NOT YET SUPPORTED')


def get_moodle_document(url):
    document = session.get(url)
    disp = document.headers['Content-disposition']
    document_name = re.findall('filename.+', disp)[0].split('"')[1]
    return (document.content, document_name, url)


def write_document(document, path, filename):
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(path + filename, 'wb') as file:
        file.write(document)


def write_to_persist():
    out_dict = persist_dict
    with open(persist_path, 'w+') as persist_file:
        if persist_choice == PERSIST_ENUMS[1]:
            out_dict['password'] = ''
        if persist_choice == PERSIST_ENUMS[2]:
            for key in PERSIST_KEYS:
                out_dict[key] = ''
        out_dict['download_history'] = download_history
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

    download_all_documents_from_course_set(course_ids)

    write_to_persist()  # update download history


# TODOS:
    # user/pass incorrect:
    # initial response doesn't return a useful code, need to catch later on

    # catch bad urls:
    # should be able to catch in initial response obv.

    # more menu options

    # profiling/pythonic code cleanup
