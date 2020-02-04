import requests
import re
from bs4 import BeautifulSoup
import json

def get_sesh_id(session):
    soup = BeautifulSoup(session.get('https://moodle31.upei.ca/login/index.php').text,"html.parser")
    return soup.find('input', attrs={'name':'logintoken'})['value']



def login():
    session = requests.Session()
    payload = {
        'logintoken': get_sesh_id(session),
        'username': config["username"],
        'password': config["password"]
    }
    session.post('https://moodle31.upei.ca/login/index.php', data=payload)
    return session

def get_moodle_doc(url):
    doc= session.get(url)
    disp = doc.headers['Content-disposition']
    doc_name = re.findall("filename.+", disp)[0].split("\"")[1]
    return {
        'doc': doc.content,
        'name': doc_name
    }

def write_doc(doc, name):
    file = open(name, 'wb')
    file.write(doc)
    file.close

    

def print_downloaded():
    print('Downloaded:')
    print('===========')
    for name in config["downloaded"]:
        print(name)
    print('================================================================================')
    
def download_stnd_moodle():
    website = session.get("https://moodle31.upei.ca/course/view.php?id=" 
                           + str(config["course_id"]))
    html = website.text
    soup = BeautifulSoup(html, "html.parser")
    links = soup.findAll(class_='activityinstance')

    print_downloaded()
    print('Downloading:')
    print('===========')

    for link in links:
        name = link.find(class_ = "instancename").text
        if config["match"] not in name.lower() or name in config["downloaded"]:
            continue
        print(name)
        url = link.a["href"]
        doc = get_moodle_doc(url)
        write_doc(doc['doc'], doc['name'])
        config["downloaded"].append(name)
        print('\t', doc['name'])

    

def download_cezar():
    semester = config["semester"].split('-')
    year = semester[0]
    season = semester[1]
    course = config["course"]
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
        name = link[(link.rfind('/')+1 ):]
        print(name)
        doc = session.get(link).content
        write_doc(doc, name)

if __name__== "__main__":
    config = json.loads(open('config.json', 'r').read())
    session = login()

    if config["course_type"] == "stnd_moodle": download_stnd_moodle()
    elif config["course_type"] == "cezar": download_cezar()

    config_file = open('config.json', 'w')
    pretty_json = json.dumps(config,
        indent=4, 
        separators=(',', ': ')
        )
    config_file.write(pretty_json)
    config_file.close()
