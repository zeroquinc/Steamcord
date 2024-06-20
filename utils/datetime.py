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
    
    """Calculate the seconds until the next hour"""
    @staticmethod
    def seconds_until_next_hour():
        now = datetime.now()
        return (60 - now.minute) * 60 - now.second
    
    @staticmethod
    def convert_to_datetime(unix_timestamp):
        try:
            return datetime.fromtimestamp(int(unix_timestamp))
        except ValueError as e:
            # Handle or log the error as needed
            raise ValueError(f"Error converting Unix timestamp: {e}") from e

    @staticmethod
    def calculate_time_span(start_date, end_date):
        return end_date - start_date

    @staticmethod
    def format_time_span(time_span):
        days, seconds = time_span.days, time_span.seconds
        years, days = divmod(days, 365)
        hours = seconds // 3600

        if years > 0:
            return f"{years} years, {days} days and {hours} hours"
        elif days > 0:
            return f"{days} days and {hours} hours"
        else:
            return f"{hours} hours"