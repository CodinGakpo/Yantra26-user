#!/bin/bash

# Blockchain Evidence Storage Refactor - Migration Script
# This script helps migrate from IPFS to local file storage

set -e  # Exit on error

echo "================================"
echo "Blockchain Evidence Refactor"
echo "IPFS → Local File Storage"
echo "================================"
echo ""

# Navigate to backend directory
cd "$(dirname "$0")"

echo "Step 1: Creating upload directory..."
mkdir -p media/uploads
chmod 755 media/uploads
echo "✅ Upload directory created: media/uploads/"
echo ""

echo "Step 2: Creating .gitkeep for media directory..."
mkdir -p media
touch media/.gitkeep
echo "✅ Git placeholder created"
echo ""

echo "Step 3: Checking for existing evidence records..."
python manage.py shell -c "
from blockchain.models import EvidenceHash
count = EvidenceHash.objects.count()
print(f'Found {count} existing evidence records')
if count > 0:
    print('⚠️  Warning: You have existing evidence records!')
    print('   These will need to be handled during migration.')
    print('   See BLOCKCHAIN_REFACTOR_GUIDE.md for options.')
" || echo "⚠️  Could not check database (might not be configured yet)"
echo ""

echo "Step 4: Creating database migration..."
python manage.py makemigrations blockchain --name change_ipfs_cid_to_file_path
echo "✅ Migration created"
echo ""

echo "Step 5: Do you want to apply the migration now? (yes/no)"
read -r apply_migration

if [ "$apply_migration" = "yes" ]; then
    echo "Applying migration..."
    python manage.py migrate blockchain
    echo "✅ Migration applied"
else
    echo "⚠️  Migration NOT applied. Run manually with:"
    echo "   python manage.py migrate blockchain"
fi
echo ""

echo "Step 6: Verifying migration..."
python manage.py shell -c "
from blockchain.models import EvidenceHash
try:
    field = EvidenceHash._meta.get_field('file_path')
    print(f'✅ field_path field exists: {field}')
    print(f'   Type: {field.get_internal_type()}')
    print(f'   Max length: {field.max_length}')
except Exception as e:
    print(f'❌ Error: {e}')
" || echo "⚠️  Could not verify (database might not be migrated yet)"
echo ""

echo "================================"
echo "Migration Steps Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Review BLOCKCHAIN_REFACTOR_GUIDE.md for detailed documentation"
echo "2. Update your URL configuration to serve media files (see guide)"
echo "3. Test file upload with: python manage.py shell"
echo "4. Test API endpoint with curl/Postman"
echo ""
echo "Quick test command:"
echo "  python manage.py shell -c 'from blockchain.ipfs_service import get_local_storage_service; s = get_local_storage_service(); print(s.upload_dir)'"
echo ""
