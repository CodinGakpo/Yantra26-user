#!/usr/bin/env python3
"""
Script to clean up duplicate blockchain transactions and fix database issues.

This solves the "UNIQUE constraint failed: blockchain_blockchaintransaction.tx_hash" error
by removing duplicate or failed transactions from the database.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_hub.settings.local')
django.setup()

from blockchain.models import BlockchainTransaction, EvidenceHash, SLATracker
from django.db.models import Count

# ANSI colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text):
    print(f"\n{BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")


def print_error(text):
    print(f"{RED}✗ {text}{RESET}")


def check_duplicates():
    """Check for duplicate transaction hashes"""
    print_header("Checking for Duplicate Transactions")
    
    # Find duplicate tx_hashes
    duplicates = (BlockchainTransaction.objects
                 .values('tx_hash')
                 .annotate(count=Count('id'))
                 .filter(count__gt=1))
    
    if duplicates:
        print_warning(f"Found {len(duplicates)} duplicate transaction hashes:")
        for dup in duplicates:
            print(f"  - {dup['tx_hash']}: {dup['count']} occurrences")
        return list(duplicates)
    else:
        print_success("No duplicate transaction hashes found")
        return []


def check_failed_transactions():
    """Check for failed transactions"""
    print_header("Checking for Failed Transactions")
    
    failed = BlockchainTransaction.objects.filter(status='FAILED')
    pending = BlockchainTransaction.objects.filter(status='PENDING')
    
    print(f"Failed transactions: {failed.count()}")
    print(f"Pending transactions: {pending.count()}")
    
    return failed, pending


def remove_duplicates(duplicates, dry_run=True):
    """Remove duplicate transactions, keeping only the most recent one"""
    if not duplicates:
        print_success("No duplicates to remove")
        return
    
    print_header("Removing Duplicate Transactions")
    
    if dry_run:
        print_warning("DRY RUN MODE - No changes will be made")
        print("Run with --fix flag to actually remove duplicates\n")
    
    removed_count = 0
    
    for dup in duplicates:
        tx_hash = dup['tx_hash']
        
        # Get all transactions with this hash
        transactions = BlockchainTransaction.objects.filter(tx_hash=tx_hash).order_by('-timestamp')
        
        if transactions.count() > 1:
            # Keep the most recent one (first in the ordered list)
            to_keep = transactions[0]
            to_remove = transactions[1:]
            
            print(f"\nTransaction hash: {tx_hash}")
            print(f"  Keeping:  ID={to_keep.id}, Status={to_keep.status}, Time={to_keep.timestamp}")
            
            for tx in to_remove:
                print(f"  Removing: ID={tx.id}, Status={tx.status}, Time={tx.timestamp}")
                
                if not dry_run:
                    tx.delete()
                    removed_count += 1
    
    if not dry_run:
        print_success(f"\n✅ Removed {removed_count} duplicate transactions")
    else:
        print_warning(f"\n Would remove {len(duplicates)} duplicate transaction groups")


def clean_failed_transactions(dry_run=True):
    """Remove failed and old pending transactions"""
    print_header("Cleaning Failed Transactions")
    
    if dry_run:
        print_warning("DRY RUN MODE - No changes will be made")
        print("Run with --fix flag to actually remove failed transactions\n")
    
    failed = BlockchainTransaction.objects.filter(status='FAILED')
    
    print(f"Found {failed.count()} failed transactions")
    
    if not dry_run:
        count = failed.count()
        failed.delete()
        print_success(f"✅ Removed {count} failed transactions")
    else:
        print_warning(f"Would remove {failed.count()} failed transactions")


def display_statistics():
    """Display database statistics"""
    print_header("Database Statistics")
    
    total_tx = BlockchainTransaction.objects.count()
    confirmed_tx = BlockchainTransaction.objects.filter(status='CONFIRMED').count()
    pending_tx = BlockchainTransaction.objects.filter(status='PENDING').count()
    failed_tx = BlockchainTransaction.objects.filter(status='FAILED').count()
    
    total_evidence = EvidenceHash.objects.count()
    verified_evidence = EvidenceHash.objects.filter(verified=True).count()
    
    total_sla = SLATracker.objects.count()
    escalated_sla = SLATracker.objects.filter(escalated=True).count()
    
    print(f"📊 Blockchain Transactions:")
    print(f"   Total:     {total_tx}")
    print(f"   Confirmed: {confirmed_tx}")
    print(f"   Pending:   {pending_tx}")
    print(f"   Failed:    {failed_tx}")
    
    print(f"\n📁 Evidence Hashes:")
    print(f"   Total:    {total_evidence}")
    print(f"   Verified: {verified_evidence}")
    
    print(f"\n⏰ SLA Trackers:")
    print(f"   Total:     {total_sla}")
    print(f"   Escalated: {escalated_sla}")
    
    print()


def reset_pending_transactions(dry_run=True):
    """Reset old pending transactions to allow retry"""
    print_header("Resetting Pending Transactions")
    
    from django.utils import timezone
    from datetime import timedelta
    
    # Find pending transactions older than 5 minutes
    cutoff_time = timezone.now() - timedelta(minutes=5)
    old_pending = BlockchainTransaction.objects.filter(
        status='PENDING',
        timestamp__lt=cutoff_time
    )
    
    print(f"Found {old_pending.count()} old pending transactions")
    
    if not dry_run:
        count = old_pending.count()
        # Delete them so they can be retried
        old_pending.delete()
        print_success(f"✅ Reset {count} old pending transactions")
    else:
        print_warning(f"Would reset {old_pending.count()} old pending transactions")


def main():
    """Main function to clean blockchain database"""
    print_header("🔧 Blockchain Database Cleanup Tool")
    
    # Parse command line arguments
    dry_run = True
    if '--fix' in sys.argv:
        dry_run = False
        print_warning("⚠️  FIX MODE - Changes will be permanent!")
    else:
        print_warning("Running in DRY RUN mode. Use --fix to apply changes.")
    
    # Display current statistics
    display_statistics()
    
    # Check for issues
    duplicates = check_duplicates()
    failed, pending = check_failed_transactions()
    
    # Perform cleanup
    if duplicates:
        remove_duplicates(duplicates, dry_run=dry_run)
    
    if failed.count() > 0:
        clean_failed_transactions(dry_run=dry_run)
    
    if pending.count() > 0:
        reset_pending_transactions(dry_run=dry_run)
    
    # Display final statistics
    if not dry_run:
        print("\n" + "="*60)
        display_statistics()
    
    print_success("✅ Cleanup complete!")
    
    if dry_run:
        print_warning("\n💡 Run with --fix flag to actually apply the changes:")
        print(f"   python {Path(__file__).name} --fix")


if __name__ == '__main__':
    main()
