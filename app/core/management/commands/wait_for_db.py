"""
Django command to wait for the database to be available.
"""

import time

from psycopg2 import OperationalError as psycopgeError

from django.db.utils import OperationalError
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """Django command to wait a database"""

    def handle(self, *args, **options):
        self.stdout.write('Waiting for the database...')
        db_up = False
        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except(psycopgeError, OperationalError):
                self.stdout.write('Database unavailable, Waiting 1 second...')
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database availabel!"))