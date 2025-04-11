import datetime
from django.core.exceptions import ValidationError

def validate_date_in_range(value):
    if isinstance(value, datetime.date):
        if value.year < 1000 or value.year > 9999:
            raise ValidationError('Date is out of range: Year must be in four digits.')
        
        min_date = datetime.date(1000, 1, 1)
        max_date = datetime.date(9999, 12, 31)
        if value < min_date or value > max_date:
            raise ValidationError(f'Date is out of range: Must be between {min_date} and {max_date}.')
    else:
        raise ValidationError('Invalid date format.')