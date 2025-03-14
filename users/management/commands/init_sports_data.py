from django.core.management.base import BaseCommand
from users.utils import create_sample_sports_data

class Command(BaseCommand):
    help = 'Initializes sample sports equipment categories and products'

    def handle(self, *args, **kwargs):
        product_count = create_sample_sports_data()
        self.stdout.write(self.style.SUCCESS(f'Successfully created sample sports data with {product_count} products'))