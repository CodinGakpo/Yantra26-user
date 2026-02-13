from django.core.management.base import BaseCommand
from blockchain.listeners import sync_events_from_blockchain


class Command(BaseCommand):
    help = 'Sync blockchain events to database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--from-block',
            type=int,
            help='Starting block number',
        )
        
        parser.add_argument(
            '--to-block',
            type=int,
            help='Ending block number',
        )
    
    def handle(self, *args, **options):
        from_block = options.get('from_block')
        to_block = options.get('to_block')
        
        self.stdout.write(self.style.WARNING('Syncing blockchain events...'))
        
        if from_block:
            self.stdout.write(f'  From block: {from_block}')
        if to_block:
            self.stdout.write(f'  To block: {to_block}')
        
        try:
            result = sync_events_from_blockchain(from_block, to_block)
            
            if 'error' in result:
                self.stdout.write(
                    self.style.ERROR(f'Error: {result["error"]}')
                )
                return
            
            self.stdout.write(self.style.SUCCESS('✓ Sync complete:'))
            self.stdout.write(f'  • Complaint events: {result.get("complaint_events", 0)}')
            self.stdout.write(f'  • Evidence events: {result.get("evidence_events", 0)}')
            self.stdout.write(f'  • Escalation events: {result.get("escalation_events", 0)}')
            self.stdout.write(f'  • SLA events: {result.get("sla_events", 0)}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            raise
