import csv
import json
import os
import shutil
import tempfile
import tweepy
import time
import pandas as pd
from app import db
from app.models import BusinessMontreal, User, Post, Message, Notification, \
                       Task
from datetime import datetime
from flask import current_app
from rq import get_current_job
from urllib.request import Request, urlopen

"""
def example(seconds):
    job = get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task completed')
"""

def example2():
    print('TEST')


BUSINESS_FIELDS = (
    'name', 'address', 'city', 'state', 'type', 'statut', 'date_statut',
    'latitude', 'longitude', 'x', 'y'
)
BUSINESS_CSV_FIELDS = {'business_id', *BUSINESS_FIELDS}
BUSINESS_MONTREAL_CSV_URL = (
    'https://donnees.montreal.ca/dataset/'
    'c1d65779-d3cb-44e8-af0a-b9f2c5f7766d/resource/'
    '28a4957d-732e-48f9-8adb-0624867d9bb0/download/businesses.csv'
)
BUSINESS_MONTREAL_CSV_PATH = 'app/static/data/business_montreal.csv'
MINIMUM_BUSINESS_ROWS = 1000
DELETE_BATCH_SIZE = 500
DOWNLOAD_TIMEOUT_SECONDS = 120


def import_data_business_montreal():
    return refresh_businesses_once()


def refresh_businesses_once(csv_path=BUSINESS_MONTREAL_CSV_PATH,
                            source_url=BUSINESS_MONTREAL_CSV_URL,
                            dry_run=False,
                            minimum_rows=MINIMUM_BUSINESS_ROWS):
    started_at = time.perf_counter()
    destination_path = os.path.abspath(csv_path)
    destination_directory = os.path.dirname(destination_path)
    os.makedirs(destination_directory, exist_ok=True)
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix='business_montreal_', suffix='.csv',
        dir=destination_directory
    )
    os.close(file_descriptor)

    try:
        download_business_csv(source_url, temporary_path)
        result = import_businesses_once(
            temporary_path,
            dry_run=dry_run,
            minimum_rows=minimum_rows
        )
        if not dry_run:
            os.replace(temporary_path, destination_path)
            temporary_path = None
        result['import_duration_seconds'] = result['duration_seconds']
        result['duration_seconds'] = round(
            time.perf_counter() - started_at, 2
        )
        result['source_url'] = source_url
        result['csv_path'] = destination_path
        return result
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)


def download_business_csv(source_url, destination_path):
    request = Request(
        source_url,
        headers={'User-Agent': 'portfolio-business-import/1.0'}
    )
    with urlopen(request, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response, \
            open(destination_path, 'wb') as destination_file:
        shutil.copyfileobj(response, destination_file)


def import_data_to_csv(link, write_file_name):
    url = urlopen("{}".format(link))
    string = url.read().decode('utf-8')
    try:
        file = open("app/static/data/{}.csv".format(write_file_name), "w")
    except Exception as e:
        print(e)
    file.write(string)
    file.close()
    

def import_csv_to_database(read_file_name):
    return import_businesses_once(
        'app/static/data/{}.csv'.format(read_file_name)
    )


def import_businesses_once(csv_path, dry_run=False,
                           minimum_rows=MINIMUM_BUSINESS_ROWS):
    started_at = time.perf_counter()

    try:
        imported_records = _read_business_csv(csv_path)
        if len(imported_records) < minimum_rows:
            raise ValueError(
                'Le CSV contient seulement {} établissements; minimum: {}.'
                .format(len(imported_records), minimum_rows)
            )

        existing_records = {
            record.id: record for record in BusinessMontreal.query.all()
        }
        minimum_safe_rows = len(existing_records) // 2
        if existing_records and len(imported_records) < minimum_safe_rows:
            raise ValueError(
                'Le CSV contient moins de la moitié des établissements '
                'actuels; suppression annulée.'
            )

        current_datetime = datetime.utcnow()
        created = 0
        updated = 0

        for business_id, values in imported_records.items():
            existing_record = existing_records.get(business_id)
            if existing_record is None:
                db.session.add(BusinessMontreal(
                    id=business_id,
                    date_last_update=current_datetime,
                    **values
                ))
                created += 1
                continue

            has_changed = any(
                getattr(existing_record, field) != values[field]
                for field in BUSINESS_FIELDS
            )
            if has_changed:
                for field in BUSINESS_FIELDS:
                    setattr(existing_record, field, values[field])
                existing_record.date_last_update = current_datetime
                updated += 1

        ids_to_delete = sorted(
            set(existing_records) - set(imported_records)
        )
        for start in range(0, len(ids_to_delete), DELETE_BATCH_SIZE):
            id_batch = ids_to_delete[start:start + DELETE_BATCH_SIZE]
            BusinessMontreal.query.filter(
                BusinessMontreal.id.in_(id_batch)
            ).delete(synchronize_session=False)

        if dry_run:
            db.session.rollback()
        else:
            db.session.commit()

        result = {
            'source_rows': len(imported_records),
            'created': created,
            'updated': updated,
            'deleted': len(ids_to_delete),
            'dry_run': dry_run,
            'duration_seconds': round(time.perf_counter() - started_at, 2)
        }
        current_app.logger.info('Business import completed: %s', result)
        return result
    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            'Business import failed for CSV %s', csv_path
        )
        raise


def _read_business_csv(csv_path):
    imported_records = {}

    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        missing_fields = BUSINESS_CSV_FIELDS - set(reader.fieldnames or [])
        if missing_fields:
            raise ValueError(
                'Colonnes CSV manquantes: {}'.format(
                    ', '.join(sorted(missing_fields))
                )
            )

        for line_number, row in enumerate(reader, start=2):
            business_id = int(row['business_id'])
            if business_id in imported_records:
                raise ValueError(
                    'Identifiant {} en double à la ligne {}.'
                    .format(business_id, line_number)
                )

            imported_records[business_id] = {
                'name': row['name'],
                'address': row['address'],
                'city': row['city'],
                'state': row['state'],
                'type': row['type'],
                'statut': row['statut'],
                'date_statut': datetime.strptime(
                    row['date_statut'], '%Y%m%d'
                ),
                'latitude': string_to_float(row['latitude']),
                'longitude': string_to_float(row['longitude']),
                'x': string_to_float(row['x']),
                'y': string_to_float(row['y'])
            }

    return imported_records

def compare_rows_csv_to_db(read_file_name):
    df_csv = pd.read_csv("app/static/data/{}.csv".format(read_file_name), 'r')


def export_csv_data_to_csv(source_csv, data, destination_csv):
    try:
        # Obtenir le nom des colonnes appropriées
        fieldnames = obtain_column_name_csv(source_csv)
        # Écriture des données
        with open("app/static/data/{}.csv".format(destination_csv), \
            'w') as destination_csv:
            writer = csv.DictWriter(destination_csv, fieldnames=fieldnames)
            writer.writeheader()
            # Écriture des données
            for row in data:
                writer.writerow(row)
    except Exception as e:
        print(e)


def add_todays_date_column_csv(file_name):
    try:
        # Obtenir le nom des colonnes appropriées
        existing_fieldnames = obtain_column_name_csv(file_name)
        new_fieldnames = "date_update"
        # Écriture des mises à jour des données
        with open("app/static/data/{}.csv".format(file_name), \
            'w') as destination_csv:
            # Importe l'heure actuelle
            current_datetime = datetime.now()
            formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
            writer = csv.DictWriter(destination_csv, fieldnames=
                                    existing_fieldnames + [new_fieldnames])
            # Écriture des données
            for row in file_name:
                writer.writerow({})
    except Exception as e:
        print(e)


def obtain_column_name_csv(file_name):
    try:
        # Obtenir le nom des colonnes appropriées
        with open("app/static/data/{}.csv".format(file_name), \
            'r') as source_csv:
            reader = csv.reader(source_csv)
            fieldnames = next(reader)
        return fieldnames
    except Exception as e:
        print(e)


def read_csv(file_name):
    try:
        with open("app/static/data/{}.csv".format(file_name), "r") as file:
            reader = csv.DictReader(file)
            data = []
            for row in reader:
                data.append(row)
                
            return data
    except Exception as e:
        print(e)
    file.close()


def create_tweet():
    
    
    return None


# Gère un float '' pour retourner None...
def string_to_float(string):
    try:
        return float(string)
    except ValueError:
        return None
    
    
def convert_csv_to_json(file_name):
    # Open the CSV file and read its contents into a list of dictionaries
    with open('app/static/data/{}.csv'.format(file_name), 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]

    # Write the list of dictionaries to a JSON file
    with open('app/static/data/{}.json'.format(file_name), 'w') as jsonfile:
        json.dump(data, jsonfile)
    
    
def clear_users_related_tables():
    clear_message_table()
    clear_notification_table()
    clear_post_table()
    clear_user_table()


def clear_message_table():
    db.session.query(Message).delete()
    db.session.commit()
    
    
def clear_notification_table():
    db.session.query(Notification).delete()
    db.session.commit()

    
def clear_post_table():
    db.session.query(Post).delete()
    db.session.commit()
    

def clear_user_table():
    db.session.query(User).delete()
    db.session.commit()

    
def clear_task_table():
    db.session.query(Task).delete()
    db.session.commit()
