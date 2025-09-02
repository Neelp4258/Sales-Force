"""
Analytics models for Ambivare ERP
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import uuid

User = get_user_model()


class Dashboard(models.Model):
    """Custom dashboard configuration"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Owner
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboards')
    
    # Sharing
    is_public = models.BooleanField(default=False)
    shared_with = models.ManyToManyField(User, blank=True, related_name='shared_dashboards')
    
    # Layout
    layout_config = models.JSONField(default=dict)
    
    # Default dashboard
    is_default = models.BooleanField(default=False)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dashboard'
        verbose_name_plural = 'Dashboards'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Widget(models.Model):
    """Dashboard widgets"""
    
    WIDGET_TYPE_CHOICES = [
        ('revenue_chart', 'Revenue Chart'),
        ('sales_pipeline', 'Sales Pipeline'),
        ('lead_funnel', 'Lead Funnel'),
        ('task_summary', 'Task Summary'),
        ('recent_activities', 'Recent Activities'),
        ('top_performers', 'Top Performers'),
        ('customer_growth', 'Customer Growth'),
        ('product_performance', 'Product Performance'),
        ('invoice_status', 'Invoice Status'),
        ('kpi_card', 'KPI Card'),
        ('custom', 'Custom Widget'),
    ]
    
    CHART_TYPE_CHOICES = [
        ('line', 'Line Chart'),
        ('bar', 'Bar Chart'),
        ('pie', 'Pie Chart'),
        ('donut', 'Donut Chart'),
        ('area', 'Area Chart'),
        ('scatter', 'Scatter Plot'),
        ('heatmap', 'Heatmap'),
        ('table', 'Table'),
        ('number', 'Number Card'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='widgets')
    
    # Widget Configuration
    title = models.CharField(max_length=100)
    widget_type = models.CharField(max_length=30, choices=WIDGET_TYPE_CHOICES)
    chart_type = models.CharField(max_length=20, choices=CHART_TYPE_CHOICES, default='line')
    
    # Position and Size
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=6)  # Grid units
    height = models.IntegerField(default=4)  # Grid units
    
    # Data Configuration
    data_source = models.CharField(max_length=100)  # Model or custom query
    filters = models.JSONField(default=dict)
    date_range = models.CharField(max_length=20, default='last_30_days')
    
    # Display Options
    show_legend = models.BooleanField(default=True)
    show_labels = models.BooleanField(default=True)
    color_scheme = models.CharField(max_length=20, default='default')
    
    # Refresh
    auto_refresh = models.BooleanField(default=False)
    refresh_interval = models.IntegerField(default=300)  # seconds
    
    class Meta:
        verbose_name = 'Widget'
        verbose_name_plural = 'Widgets'
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} - {self.dashboard.name}"


class Report(models.Model):
    """Saved reports"""
    
    REPORT_TYPE_CHOICES = [
        ('sales', 'Sales Report'),
        ('revenue', 'Revenue Report'),
        ('customer', 'Customer Report'),
        ('product', 'Product Report'),
        ('invoice', 'Invoice Report'),
        ('activity', 'Activity Report'),
        ('performance', 'Performance Report'),
        ('custom', 'Custom Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    # Owner
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    
    # Configuration
    filters = models.JSONField(default=dict)
    columns = models.JSONField(default=list)
    sort_by = models.CharField(max_length=50, blank=True)
    group_by = models.CharField(max_length=50, blank=True)
    
    # Schedule
    is_scheduled = models.BooleanField(default=False)
    schedule_pattern = models.CharField(max_length=50, blank=True)  # cron pattern
    recipients = models.ManyToManyField(User, blank=True, related_name='scheduled_reports')
    
    # Format
    default_format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='pdf')
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ReportExecution(models.Model):
    """Report execution history"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='executions')
    
    # Execution Details
    executed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    executed_at = models.DateTimeField(auto_now_add=True)
    
    # Parameters
    parameters = models.JSONField(default=dict)
    date_range_start = models.DateField(null=True, blank=True)
    date_range_end = models.DateField(null=True, blank=True)
    
    # Output
    format = models.CharField(max_length=10, choices=Report.FORMAT_CHOICES)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    row_count = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)
    
    # Performance
    execution_time = models.DurationField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Report Execution'
        verbose_name_plural = 'Report Executions'
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.report.name} - {self.executed_at}"


class Metric(models.Model):
    """Key Performance Indicators (KPIs)"""
    
    METRIC_TYPE_CHOICES = [
        ('revenue', 'Revenue'),
        ('count', 'Count'),
        ('percentage', 'Percentage'),
        ('average', 'Average'),
        ('sum', 'Sum'),
    ]
    
    AGGREGATION_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Metric Configuration
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    model_name = models.CharField(max_length=50)
    field_name = models.CharField(max_length=50)
    filters = models.JSONField(default=dict)
    
    # Aggregation
    aggregation = models.CharField(max_length=20, choices=AGGREGATION_CHOICES, default='daily')
    
    # Target/Goal
    has_target = models.BooleanField(default=False)
    target_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    target_period = models.CharField(max_length=20, blank=True)
    
    # Display
    format_string = models.CharField(max_length=50, default='{value}')
    unit = models.CharField(max_length=20, blank=True)
    
    # Active
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Metric'
        verbose_name_plural = 'Metrics'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class MetricValue(models.Model):
    """Historical metric values"""
    
    metric = models.ForeignKey(Metric, on_delete=models.CASCADE, related_name='values')
    date = models.DateField()
    value = models.DecimalField(max_digits=20, decimal_places=4)
    
    # Additional dimensions
    dimension1 = models.CharField(max_length=100, blank=True)  # e.g., user, product
    dimension2 = models.CharField(max_length=100, blank=True)  # e.g., region, category
    
    # Tracking
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Metric Value'
        verbose_name_plural = 'Metric Values'
        ordering = ['-date']
        unique_together = ['metric', 'date', 'dimension1', 'dimension2']
    
    def __str__(self):
        return f"{self.metric.name} - {self.date}: {self.value}"


class DataExport(models.Model):
    """Data export tracking"""
    
    EXPORT_TYPE_CHOICES = [
        ('leads', 'Leads'),
        ('customers', 'Customers'),
        ('deals', 'Deals'),
        ('invoices', 'Invoices'),
        ('products', 'Products'),
        ('tasks', 'Tasks'),
        ('custom', 'Custom Query'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPE_CHOICES)
    
    # User
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='data_exports')
    
    # Export Details
    filters = models.JSONField(default=dict)
    columns = models.JSONField(default=list)
    row_count = models.IntegerField(default=0)
    
    # File
    format = models.CharField(max_length=10)
    file = models.FileField(upload_to='exports/')
    file_size = models.IntegerField()  # in bytes
    
    # Tracking
    exported_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    # Security
    is_encrypted = models.BooleanField(default=False)
    download_count = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = 'Data Export'
        verbose_name_plural = 'Data Exports'
        ordering = ['-exported_at']
    
    def __str__(self):
        return f"{self.export_type} export by {self.exported_by.email}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at