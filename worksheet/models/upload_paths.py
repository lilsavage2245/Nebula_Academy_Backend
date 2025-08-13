# worksheet/models/upload_paths.py
def worksheet_file_upload_path(instance, filename):
    return f"worksheet/{instance.lesson.id}/{filename}"

def submission_upload_path(instance, filename):
    return f"worksheet/submissions/{instance.worksheet.id}/{instance.user.id}/{filename}"
