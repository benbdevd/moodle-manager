# moodle_manager
Use this script to download documents from moodle without losing your marbles by using your noodle.

moodle_manager has been designed and tested around the [UPEI moodle server](https://moodle31.upei.ca).
There is no guarantee moodle_manager will work with any other moodle servers as it makes assumptions about the HTML served.

## Usage

Simply run `python3 moodle_manager.py` to begin!

### Persistence File

moodle_manager will create a `.moodle_data.json` file to persist some data accross sessions. 

Only modify this file if you would like to manually erase your username/password from the file, or manually erase the download history.
