from datetime import datetime, timedelta

class DateUtils:

    """Calculate the age of a Steam account"""
    @staticmethod
    def calculate_age(timecreated):
        delta = datetime.now() - datetime.fromtimestamp(timecreated)
        age_years = delta.days // 365
        delta -= timedelta(days=age_years*365)
        age_months = delta.days // 30
        delta -= timedelta(days=age_months*30)
        age_days = delta.days
        return f"{age_years} year(s), {age_months} month(s), {age_days} day(s)"
    
    """Format a timestamp to a human-readable format"""
    @staticmethod
    def format_timestamp(timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%d/%m/%y %H:%M:%S')