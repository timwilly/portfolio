# projet_photo

![Version](https://img.shields.io/badge/version-0.1.0-brightgreen)

## Table of contents
- [Description](#description)
- [Functionnality](#functionnality)
- [Installation](#installation)
- [Montreal business data](#montreal-business-data)
- [Notes](#notes)

## Description
Portfolio with various features. Although it is not done yet and need to be tested further, the features are most likely functionnal.

## Functionnality
- Create an account
- Send a message to another account
- Post a message on the feed
- Explore the feed
- View establishments in Montreal and their statues on a map
- Switch the language to English, French or Spanish

## Installation
To view the project you can click [here](https://projet-photo.onrender.com)  
  
⚠️ It is normal for the link to be slow at first due to the free plan from render.com. After navigating through the website, the request times should improve.

or

You can use a CLI with python 3.10

```bash
git clone https://github.com/timwilly/projet_photo.git
cd portfolio
source venv/bin/activate
pip install -r requirements.txt
make run
```

## Montreal business data

Starting the application with `make run` does not download or import new
business data.

To download the latest official CSV file from the City of Montreal and update
the database, run:

```bash
flask refresh-businesses-once
```

To preview the changes without modifying the database or replacing the local
CSV file:

```bash
flask refresh-businesses-once --dry-run
```

To import the CSV file already stored locally without downloading a new copy:

```bash
flask import-businesses-once app/static/data/business_montreal.csv
```

Run these commands from the `portfolio` directory with the virtual environment
activated.

## Notes

You can access a testing account with the username: 'test' and the password: 'test'
