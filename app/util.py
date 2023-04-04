def get_weekday_str(weekday: int | str):
    weekday = int(weekday)
    week = ["月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜"]
    day = week[weekday]
    return day
