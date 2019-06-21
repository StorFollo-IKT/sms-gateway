from pprint import pprint
from django.core.management.base import BaseCommand  # , CommandError
from messaging.keyword_handler import handle


class Command(BaseCommand):
    help = 'Handle a keyword'

    def add_arguments(self, parser):
        parser.add_argument('keyword', nargs='+', type=str)

    def handle(self, *args, **options):
        print(handle(options['keyword'][0]))
