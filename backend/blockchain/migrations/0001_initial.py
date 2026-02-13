import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BlockchainTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('complaint_id', models.CharField(db_index=True, max_length=100)),
                ('event_type', models.CharField(choices=[('CREATED', 'Complaint Created'), ('ASSIGNED', 'Complaint Assigned'), ('STATUS_UPDATED', 'Status Updated'), ('ESCALATED', 'Complaint Escalated'), ('RESOLVED', 'Complaint Resolved'), ('EVIDENCE_ADDED', 'Evidence Added')], db_index=True, max_length=20)),
                ('event_hash', models.CharField(help_text='Keccak256 hash of event payload', max_length=66)),
                ('tx_hash', models.CharField(help_text='Ethereum transaction hash', max_length=66, unique=True)),
                ('block_number', models.BigIntegerField(blank=True, null=True)),
                ('gas_used', models.BigIntegerField(blank=True, null=True)),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('FAILED', 'Failed')], default='PENDING', max_length=10)),
                ('timestamp', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('event_payload', models.JSONField(help_text='Original event data that was hashed')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['complaint_id', '-timestamp'], name='blockchain__complai_5cf609_idx'), models.Index(fields=['event_type', '-timestamp'], name='blockchain__event_t_3830b1_idx')],
            },
        ),
        migrations.CreateModel(
            name='EvidenceHash',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('complaint_id', models.CharField(db_index=True, max_length=100)),
                ('file_hash', models.CharField(help_text='SHA-256 hash of file content', max_length=64)),
                ('file_path', models.CharField(help_text='Local file path (relative to MEDIA_ROOT)', max_length=500)),
                ('tx_hash', models.CharField(help_text='Blockchain transaction hash', max_length=66)),
                ('block_timestamp', models.BigIntegerField(help_text='Block timestamp from blockchain')),
                ('verified', models.BooleanField(default=False, help_text='Has integrity been verified?')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('file_name', models.CharField(blank=True, max_length=255)),
                ('file_size', models.BigIntegerField(blank=True, null=True)),
                ('content_type', models.CharField(blank=True, max_length=100)),
            ],
            options={
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['complaint_id', '-created_at'], name='blockchain__complai_961442_idx'), models.Index(fields=['file_path'], name='blockchain__file_pa_1ae588_idx')],
            },
        ),
        migrations.CreateModel(
            name='SLATracker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('complaint_id', models.CharField(db_index=True, max_length=100, unique=True)),
                ('sla_deadline', models.BigIntegerField(help_text='Unix timestamp of SLA deadline')),
                ('escalated', models.BooleanField(db_index=True, default=False)),
                ('escalation_tx_hash', models.CharField(blank=True, max_length=66)),
                ('escalation_timestamp', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['sla_deadline'],
                'indexes': [models.Index(fields=['escalated', 'sla_deadline'], name='blockchain__escalat_743bc4_idx')],
            },
        ),
    ]
