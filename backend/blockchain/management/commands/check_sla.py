from django.core.management.base import BaseCommand
from django.utils import timezone
from blockchain.services import get_blockchain_service
from blockchain.models import SLATracker
import time


class Command(BaseCommand):
    help = 'Check for SLA violations and escalate complaints on blockchain'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Check without making blockchain transactions',
        )
        
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of complaints to check',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        limit = options['limit']
        
        self.stdout.write(self.style.WARNING('Checking for SLA violations...'))
        
        if dry_run:
            self.stdout.write(self.style.NOTICE('DRY RUN MODE - No blockchain transactions'))
        
        try:
            current_timestamp = int(time.time())
            trackers = SLATracker.objects.filter(
                escalated=False,
                sla_deadline__lte=current_timestamp
            )[:limit]
            
            if not trackers.exists():
                self.stdout.write(self.style.SUCCESS('✓ No SLA violations found'))
                return
            
            self.stdout.write(
                self.style.WARNING(f'Found {trackers.count()} complaints past deadline')
            )
            
            for tracker in trackers:
                deadline_dt = timezone.datetime.fromtimestamp(
                    tracker.sla_deadline,
                    tz=timezone.utc
                )
                hours_overdue = (current_timestamp - tracker.sla_deadline) / 3600
                
                self.stdout.write(
                    f'  • {tracker.complaint_id} - '
                    f'Deadline: {deadline_dt.strftime("%Y-%m-%d %H:%M")} - '
                    f'Overdue: {hours_overdue:.1f}h'
                )
            
            if dry_run:
                return
            
            self.stdout.write(self.style.WARNING('Escalating on blockchain...'))
            
            service = get_blockchain_service()
            complaint_ids = [t.complaint_id for t in trackers]
            
            escalated_count = service.batch_check_and_escalate(complaint_ids)
            
            if escalated_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'🚨 Escalated {escalated_count} complaints')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No new escalations (already escalated on-chain)')
                )
            
            self.stdout.write(self.style.SUCCESS('✓ SLA check complete'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            raise
