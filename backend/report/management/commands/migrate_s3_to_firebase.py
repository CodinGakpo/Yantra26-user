"""
Management command to migrate images from AWS S3 to Firebase Storage.

Usage:
    python manage.py migrate_s3_to_firebase --settings=report_hub.settings.local

Options:
    --dry-run: Show what would be migrated without actually doing it
    --batch-size: Number of records to process at once (default: 10)
    --skip-errors: Continue migration even if some files fail
"""

import os
import boto3
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from report.models import IssueReport

try:
    from firebase_service import get_firebase_storage_service
except ImportError:
    get_firebase_storage_service = None


class Command(BaseCommand):
    help = 'Migrate images from AWS S3 to Firebase Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of records to process at once (default: 10)',
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Continue migration even if some files fail',
        )
        parser.add_argument(
            '--image-field',
            default='image_url',
            help='Name of the image field to migrate (default: image_url)',
        )
        parser.add_argument(
            '--completion-field',
            default='completion_url',
            help='Name of the completion image field (default: completion_url)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting S3 to Firebase migration...'))
        self.stdout.write('')

        # Check prerequisites
        if not get_firebase_storage_service:
            raise CommandError(
                'firebase_service module not found. Please install firebase-admin.'
            )

        # Validate AWS credentials
        if not hasattr(settings, 'AWS_ACCESS_KEY_ID') or not settings.AWS_ACCESS_KEY_ID:
            raise CommandError('AWS_ACCESS_KEY_ID not configured')

        if not hasattr(settings, 'AWS_SECRET_ACCESS_KEY') or not settings.AWS_SECRET_ACCESS_KEY:
            raise CommandError('AWS_SECRET_ACCESS_KEY not configured')

        if not hasattr(settings, 'REPORT_IMAGES_BUCKET') or not settings.REPORT_IMAGES_BUCKET:
            raise CommandError('REPORT_IMAGES_BUCKET not configured')

        # Validate Firebase credentials
        try:
            firebase = get_firebase_storage_service()
        except Exception as e:
            raise CommandError(f'Failed to initialize Firebase: {str(e)}')

        # Initialize S3 client
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_REGION', 'ap-south-1'),
            )
        except Exception as e:
            raise CommandError(f'Failed to initialize S3 client: {str(e)}')

        dry_run = options['dry_run']
        batch_size = options['batch_size']
        skip_errors = options['skip_errors']
        image_field = options['image_field']
        completion_field = options['completion_field']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write('')

        # Find all reports with images
        reports = IssueReport.objects.filter(**{f'{image_field}__isnull': False})
        total_reports = reports.count()

        if total_reports == 0:
            self.stdout.write(self.style.WARNING('No reports with images found'))
            return

        self.stdout.write(f'Found {total_reports} report(s) with images')
        self.stdout.write(f'Batch size: {batch_size}')
        self.stdout.write('')

        migrated = 0
        failed = 0
        skipped = 0

        # Process in batches
        for i in range(0, total_reports, batch_size):
            batch = reports[i:i + batch_size]
            self.stdout.write(f'Processing batch {i // batch_size + 1}...')

            for report in batch:
                try:
                    # Migrate image_url if present
                    if getattr(report, image_field) and getattr(report, image_field) != '':
                        self._migrate_image(
                            s3_client,
                            firebase,
                            report,
                            image_field,
                            dry_run
                        )
                        migrated += 1

                    # Migrate completion_url if present
                    if hasattr(report, completion_field) and getattr(report, completion_field):
                        if getattr(report, completion_field) != '':
                            self._migrate_image(
                                s3_client,
                                firebase,
                                report,
                                completion_field,
                                dry_run
                            )
                            migrated += 1

                    if not dry_run:
                        report.save()

                except Exception as e:
                    failed += 1
                    error_msg = f'✗ Failed to migrate {report.tracking_id}: {str(e)}'
                    self.stdout.write(self.style.ERROR(error_msg))

                    if not skip_errors:
                        raise CommandError(error_msg)
                    else:
                        skipped += 1

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== Migration Summary ==='))
        self.stdout.write(f'Total reports processed: {total_reports}')
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated: {migrated}'))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed}'))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'Skipped due to errors: {skipped}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes were made to the database'))
        else:
            self.stdout.write(self.style.SUCCESS('\nMigration completed!'))

    def _migrate_image(self, s3_client, firebase, report, field_name, dry_run):
        """
        Migrate a single image from S3 to Firebase.

        Args:
            s3_client: Boto3 S3 client
            firebase: Firebase service instance
            report: IssueReport instance
            field_name: Name of the field (image_url or completion_url)
            dry_run: If True, don't actually perform the migration
        """
        s3_key = getattr(report, field_name)

        if not s3_key:
            return

        self.stdout.write(f'  Migrating {field_name} for {report.tracking_id}...')

        try:
            # Download from S3
            bucket_name = getattr(settings, 'REPORT_IMAGES_BUCKET')
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
            file_content = response['Body'].read()

            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'    [DRY RUN] Would migrate {len(file_content)} bytes to Firebase'
                    )
                )
                return

            # Extract filename from S3 key
            file_name = s3_key.split('/')[-1]

            # Upload to Firebase
            result = firebase.upload_image(
                file_content=file_content,
                file_name=file_name,
                content_type=response.get('ContentType', 'image/jpeg'),
            )

            # Update the report with new Firebase path
            setattr(report, field_name, result['key'])

            self.stdout.write(
                self.style.SUCCESS(
                    f'    ✓ Migrated {field_name}: {result["key"]}'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'    ✗ Failed to migrate {field_name}: {str(e)}'
                )
            )
            raise
