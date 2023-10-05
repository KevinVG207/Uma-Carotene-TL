# Carotene
## English translation patch for Uma Musume: Pretty Derby game (DMM version)

The main purpose of this repository is to host public translations for the Uma Musume: Pretty Derby game in a way that does not include the original Japanese text, for copyright reasons. As such, in order to create/edit the translations, a working installation of the game is required.

The project is a work-in-progress and the focus is currently to translate the main UI in home and training screens. The story translations are not a priority at the moment.

Translations on this repository are made by KevinVG207 or taken from [GameTora](https://gametora.com/umamusume) or [Noccu's English Patch](https://github.com/noccu/umamusu-translate). Translation help is welcome!

The *CODE* of this project is licensed under the **Creative Commons Attribution-NonCommercial 4.0 International** license. This means it may be shared and adapted without commercial use. No part of the code of this project may be distributed if a monetary transaction was required before the distribution. (No paywalling.) For more information, see ``LICENSE.md``.

## Requirements
This project assumes the use of Windows 10 (11 not tested.)

The following things need to be installed on your machine:
* Python 3
* Uma Musume: Pretty Derby - DMM version

## Usage

1. Create a virtual environment using `python -m venv venv` and activate it using `venv\Scripts\activate.bat`.
2. Install the required packages using `pip install -r requirements.txt`.
3. Run `src/_update_local.py` to update the local copy of the translations. (Indexing stories may take a few minutes the first time.)
4. Edit the local translations in the `editing` folder.
5. Update the translation files with `src/_prepare_release.py`. This will place the translations in the `translations` folder. These will be used to patch the game and is what you should be pushing to the repository.
6. Patch the game with `src/_import.py`.
7. Unpatch the game with `src/_revert.py`.
