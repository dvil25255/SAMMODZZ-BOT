def format_stats(db):
    files = db.file_count()
    events = db.activity_count()
    return (
        "<b>SAMMODZZ statistics</b>\n"
        f"Stored files: <code>{files}</code>\n"
        f"Logged activities: <code>{events}</code>"
    )
