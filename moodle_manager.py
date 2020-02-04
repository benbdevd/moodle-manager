from bs4 import BeautifulSoup as BS
from getpass import getpass
import requests
import json
import re

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

# GLOBALS
session = ''
server_url = ''

# CONSTANTS
LOGIN_URLPART = 'login/index.php'
MY_COURSES_URLPART = 'my/?myoverviewtab=courses'
COURSE_VIEW_URLPART = 'course/view.php?id='


class Style:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    _END = '\033[0m'


def s_print(s, style):
    print(style + s + Style._END)


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


def get_course_ids(get_all):
    if get_all:
        return get_all_course_ids
    else:
        return get_current_course_ids


def get_all_course_ids():
    soup = get_my_courses_soup()

    all_course_elements = soup.find_all(
        'div', class_='card mb-3 courses-view-course-item')

    return get_course_ids_from_elements(all_course_elements)


def get_current_course_ids():
    current_course_elements = []

    soup = get_my_courses_soup()
    temp = soup.find(id='pc-for-in-progress')

    current_course_elements = [
        element for element in temp.contents[1].contents if element != '\n' and element != ' ']

    return get_course_ids_from_elements(current_course_elements)


def get_my_courses_soup():
    request = session.get(server_url + MY_COURSES_URLPART)
    if(request.status_code == 200):
        return BS(request.text, 'html.parser')
    else:
        return -1


def get_course_ids_from_elements(elements):
    course_ids = []
    for element in elements:
        course_ids.append(element.contents[1].attrs['href'].split('=')[1])

    return course_ids


def get_moodle_doc(url):
    doc = session.get(url)
    disp = doc.headers['Content-disposition']
    doc_name = re.findall('filename.+', disp)[0].split('"')[1]
    return {
        'doc': doc.content,
        'name': doc_name
    }


def write_doc(doc, name):
    file = open(name, 'wb')
    file.write(doc)
    file.close


def download_std_moodle(course_id):
    website = session.get(server_url + COURSE_VIEW_URLPART + course_id)
    html = website.text
    soup = BS(html, 'html.parser')
    links = soup.findAll(class_='activityinstance')

    print('Downloading:')
    print('===========')

    for link in links:
        name = link.find(class_='instancename').text
        # if config['match'] not in name.lower() or name in config['downloaded']:
        #     continue
        print(name)
        url = link.a['href']
        doc = get_moodle_doc(url)
        write_doc(doc['doc'], doc['name'])
        # config['downloaded'].append(name)
        print('\t', doc['name'])


def download_cezar():
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
    #     name = link[(link.rfind('/')+1):]
    #     print(name)
    #     doc = session.get(link).content
    #     write_doc(doc, name)


def json_file():
    config = json.loads(open('config.json', 'r').read())

    config_file = open('config.json', 'w')
    pretty_json = json.dumps(config,
                             indent=4,
                             separators=(',', ': ')
                             )
    config_file.write(pretty_json)
    config_file.close()


def init(server_url_param, username, password):
    global session, server_url
    session = requests.Session()
    server_url = server_url_param
    login(username, password)


def validate_server_url():
    global server_url
    server_url = server_url.replace('http://', 'https://')

    if not server_url.startswith('https://'):
        server_url = 'https://' + server_url

    if not server_url.endswith('/'):
        server_url = server_url + '/'


# DRIVER
if __name__ == '__main__':
    interactive = True

    if interactive:
        s_print(splash, Style.WARNING)
        server_url = input('Moodle Server: ')
        username = input('Moodle Username: ')
        password = getpass('Moodle Password: ')

    init(server_url, username, password)
    print(get_all_course_ids())
    print(get_current_course_ids())
