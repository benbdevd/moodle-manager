from bs4 import BeautifulSoup as BS
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
    session = requests.Session()
    payload = {
        'logintoken': get_session_id(session),
        'username': username,
        'password': password
    }
    session.post('https://moodle31.upei.ca/login/index.php', data=payload)
    return session


def get_session_id(session):
    soup = BS(session.get(
        'https://moodle31.upei.ca/login/index.php').text, 'html.parser')
    return soup.find('input', attrs={'name': 'logintoken'})['value']


def get_current_courses(session):
    current_courses = []
    r = session.get(baseurl + 'my/?myoverviewtab=courses')

    if(r.status_code == 200):
        soup = BS(r.text, 'html.parser')
        current_courses = soup.find(id='pc-for-in-progress')

    return current_courses


def get_all_courses(session):
    all_courses = []
    r = session.get(baseurl + 'my/?myoverviewtab=courses')

    if(r.status_code == 200):
        soup = BS(r.text, 'html.parser')
        all_courses = soup.find_all(
            'div', class_='card mb-3 courses-view-course-item')

    return all_courses


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


def download_std_moodle():
    website = session.get('https://moodle31.upei.ca/course/view.php?id='
                          + str(config['course_id']))
    html = website.text
    soup = BS(html, 'html.parser')
    links = soup.findAll(class_='activityinstance')

    print('Downloading:')
    print('===========')

    for link in links:
        name = link.find(class_='instancename').text
        if config['match'] not in name.lower() or name in config['downloaded']:
            continue
        print(name)
        url = link.a['href']
        doc = get_moodle_doc(url)
        write_doc(doc['doc'], doc['name'])
        config['downloaded'].append(name)
        print('\t', doc['name'])


def download_cezar():
    semester = config['semester'].split('-')
    year = semester[0]
    season = semester[1]
    course = config['course']
    website = requests.get(
        'http://www.smcs.upei.ca/~ccampeanu/Teach/'
        + season
        + '/'
        + year
        + '/'
        + course
        + '/LN/'
    )
    html = website.text
    links = re.findall('"(http://.*4.pdf?)"', html)

    print('Downloading:')
    print('===========')

    for link in links:
        name = link[(link.rfind('/')+1):]
        print(name)
        doc = session.get(link).content
        write_doc(doc, name)


session = login()
print(get_current_courses(session))

if __name__ == '__main__':
    config = json.loads(open('config.json', 'r').read())
    session = login()

    if config['course_type'] == 'std':
        download_std_moodle()
    elif config['course_type'] == 'cezar':
        download_cezar()

    config_file = open('config.json', 'w')
    pretty_json = json.dumps(config,
                             indent=4,
                             separators=(',', ': ')
                             )
    config_file.write(pretty_json)
    config_file.close()
