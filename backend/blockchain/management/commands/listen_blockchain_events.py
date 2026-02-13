from django.core.management.base import BaseCommand
from blockchain.listeners import BlockchainEventListener


class Command(BaseCommand):
    help = 'Listen for blockchain events in real-time'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('Starting blockchain event listener...')
        )
        self.stdout.write(
            self.style.NOTICE('Press Ctrl+C to stop')
        )
        
        try:
            listener = BlockchainEventListener()
            listener.start()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.SUCCESS('\n✓ Event listener stopped')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            raise
