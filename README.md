# Moodle Downloader
Use this to download notes from moodle.

## Usage
Rename config-template.json to config.json.
Fill in the required data in the file.

- match
    - What to match to link names. This is not case sensitive
- course_id
    - The number at the end of the url for a moodle course
- username and password
    - Your login credentials
- course_type
    - either std or cezar at the moment
- semester
    - the semester in which the course takes place in the form <year>-<first letter of season>
    - ex 2019-F
- course
    - the course code in the form <subeject><course number>
    - ex CS3610
- downloaded
    - and array of all previously downloaded documents.
    - cezars type courses do not track downloads because the documens might be updated without notice

Example config.json
```
{
     "match": "lecture",
     "downloaded": [],
     "course_id": "1234",
     "username": "jsmith",
     "password": "mygreatpassword"
}
```