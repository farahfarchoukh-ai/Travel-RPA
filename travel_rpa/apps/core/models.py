from django.db import models
import uuid


class Case(models.Model):
    case_id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    message_id = models.CharField(max_length=255, unique=True, db_index=True)
    thread_id = models.CharField(max_length=255)
    idempotency_key = models.CharField(max_length=64, unique=True, db_index=True)
    
    from_email = models.EmailField()
    subject = models.TextField()
    body = models.TextField()
    received_at = models.DateTimeField()
    
    direction = models.CharField(max_length=20, null=True, blank=True)
    scope = models.CharField(max_length=50, null=True, blank=True)
    plan = models.CharField(max_length=50, null=True, blank=True)
    coverage_limit = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    days = models.IntegerField(null=True, blank=True)
    sports_coverage = models.BooleanField(default=False)
    
    premium_base = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_age_load = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_sports_load = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_subtotal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_group_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_net = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_tax = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    premium_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    route = models.CharField(max_length=20)
    missing_fields = models.JSONField(default=list)
    intent_ok = models.BooleanField(default=False)
    
    email_storage_url = models.URLField(null=True, blank=True)
    attachments_storage_urls = models.JSONField(default=list)
    policy_pdf_url = models.URLField(null=True, blank=True)
    audit_json_url = models.URLField(null=True, blank=True)
    
    kb_version = models.CharField(max_length=50, default='v1.0')
    trace_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    latency_ms = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cases'
        indexes = [
            models.Index(fields=['received_at']),
            models.Index(fields=['route']),
            models.Index(fields=['trace_id']),
        ]


class Traveller(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name='travellers')
    full_name = models.CharField(max_length=255)
    passport_number = models.CharField(max_length=50)
    date_of_birth = models.DateField(null=True, blank=True)
    age_at_travel = models.IntegerField(null=True, blank=True)
    is_senior = models.BooleanField(default=False)
    mrz_data = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'travellers'
