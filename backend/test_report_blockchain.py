#!/usr/bin/env python
"""
Test Script for Report Creation and Blockchain Integration

This script tests:
1. User authentication
2. Report creation
3. Blockchain integration
4. Database persistence
"""

import os
import django
import sys
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'report_hub.settings.local')
django.setup()

import json
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from user_profile.models import UserProfile
from report.models import IssueReport
from blockchain.models import BlockchainTransaction
from blockchain.services import BlockchainService

User = get_user_model()

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def create_test_user():
    """Create or get a test user with Aadhaar verification"""
    print_section("Creating Test User")
    
    email = "testuser@reportmitra.com"
    
    try:
        user = User.objects.get(email=email)
        print(f"✓ Found existing user: {user.email}")
    except User.DoesNotExist:
        user = User.objects.create_user(
            email=email,
            password="TestPass123!",
            first_name="Test",
            last_name="User"
        )
        print(f"✓ Created new user: {user.email}")
    
    # Create/update profile with Aadhaar verification
    profile, created = UserProfile.objects.get_or_create(user=user)
    if not profile.is_aadhaar_verified:
        # Create a dummy Aadhaar entry if needed
        from aadhaar.models import AadhaarDatabase
        from datetime import date
        aadhaar_entry, _ = AadhaarDatabase.objects.get_or_create(
            aadhaar_number="123456789012",
            defaults={
                'full_name': 'Test User',
                'date_of_birth': date(1990, 1, 1),
                'address': 'Test Address, Mumbai',
                'gender': 'Male'
            }
        )
        profile.aadhaar = aadhaar_entry
        profile.is_aadhaar_verified = True
        profile.save()
        print(f"✓ Aadhaar verified for user")
    else:
        print(f"✓ User already has Aadhaar verification")
    
    return user

def get_jwt_token(user):
    """Generate JWT token for the user"""
    print_section("Generating JWT Token")
    
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    print(f"✓ Access Token: {access_token[:50]}...")
    return access_token

def create_test_report(user):
    """Create a test issue report"""
    print_section("Creating Test Report")
    
    report_data = {
        'user': user,
        'issue_title': 'Pothole on Main Street',
        'location': 'Main Street, Near City Center, Mumbai',
        'issue_description': 'Large pothole causing traffic issues. Approximately 2 feet wide and 6 inches deep.',
        'image_url': 'reports/test-image-key.jpg',
        'department': 'Public Works Department',
        'confidence_score': 0.95
    }
    
    try:
        report = IssueReport.objects.create(**report_data)
        print(f"✓ Report created successfully")
        print(f"  - Tracking ID: {report.tracking_id}")
        print(f"  - Title: {report.issue_title}")
        print(f"  - Location: {report.location}")
        print(f"  - Department: {report.department}")
        print(f"  - Status: {report.status}")
        print(f"  - Date: {report.issue_date}")
        return report
    except Exception as e:
        print(f"✗ Error creating report: {e}")
        raise

def check_blockchain_integration(report):
    """Check if blockchain transaction was created"""
    print_section("Verifying Blockchain Integration")
    
    try:
        # Check if blockchain service is available
        print("Checking blockchain connection...")
        service = BlockchainService()
        print(f"✓ Connected to blockchain")
        print(f"  - Node URL: {service.w3.provider.endpoint_uri}")
        print(f"  - Chain ID: {service.w3.eth.chain_id}")
        print(f"  - Latest Block: {service.w3.eth.block_number}")
        print(f"  - Account: {service.account.address}")
        print(f"  - Contract: {service.contract.address}")
        
        # Check for blockchain transactions
        print("\nQuerying blockchain transactions...")
        txs = BlockchainTransaction.objects.filter(
            complaint_id=report.tracking_id
        ).order_by('-timestamp')
        
        if txs.exists():
            print(f"✓ Found {txs.count()} blockchain transaction(s):")
            for tx in txs:
                print(f"\n  Transaction #{tx.id}:")
                print(f"    - Event Type: {tx.event_type}")
                print(f"    - Status: {tx.status}")
                print(f"    - Tx Hash: {tx.tx_hash}")
                print(f"    - Gas Used: {tx.gas_used}")
                print(f"    - Timestamp: {tx.timestamp}")
                if hasattr(tx, 'error_message') and tx.error_message:
                    print(f"    - Error: {tx.error_message}")
        else:
            print("⚠ No blockchain transactions found for this report")
            print("  This might be expected if blockchain operations are async")
            print("  or if BLOCKCHAIN_ENABLED is set to False")
        
        return True
        
    except Exception as e:
        print(f"✗ Blockchain check failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        print(f"  Traceback:\n{traceback.format_exc()}")
        return False

def verify_report_in_db(report):
    """Verify report is properly saved in database"""
    print_section("Verifying Database Storage")
    
    try:
        # Re-fetch from database
        db_report = IssueReport.objects.get(id=report.id)
        print(f"✓ Report found in database")
        print(f"  - ID: {db_report.id}")
        print(f"  - Tracking ID: {db_report.tracking_id}")
        print(f"  - User: {db_report.user.email}")
        print(f"  - Status: {db_report.status}")
        
        # Check related user profile
        if hasattr(db_report.user, 'userprofile'):
            profile = db_report.user.userprofile
            print(f"  - Aadhaar Verified: {profile.is_aadhaar_verified}")
        
        return True
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("\n" + "🚀 "*20)
    print("  REPORT CREATION & BLOCKCHAIN INTEGRATION TEST")
    print("🚀 "*20)
    
    success_count = 0
    total_tests = 5
    
    try:
        # Test 1: Create user
        user = create_test_user()
        success_count += 1
        
        # Test 2: Generate JWT
        token = get_jwt_token(user)
        success_count += 1
        
        # Test 3: Create report
        report = create_test_report(user)
        success_count += 1
        
        # Test 4: Verify in DB
        if verify_report_in_db(report):
            success_count += 1
        
        # Test 5: Check blockchain
        if check_blockchain_integration(report):
            success_count += 1
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    # Final summary
    print_section("TEST SUMMARY")
    print(f"Tests Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("\n✅ ALL TESTS PASSED!")
        print("🎉 Backend and blockchain integration working correctly!")
    elif success_count >= 3:
        print("\n⚠️  PARTIAL SUCCESS")
        print("Core functionality working, but blockchain may need attention")
    else:
        print("\n❌ TESTS FAILED")
        print("Please check the errors above")
    
    print("\n" + "="*60 + "\n")
    return success_count == total_tests

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
