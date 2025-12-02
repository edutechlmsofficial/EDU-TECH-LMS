"""
Script to delete all user records from the database using app.app as Flask instance.
"""

from models import db, User
import app

def delete_all_users():
    app_instance = app.app
    with app_instance.app_context():
        users = User.query.all()
        print(f"Found {len(users)} users in the database.")
        try:
            num_deleted = User.query.delete()
            db.session.commit()
            print(f"Deleted {num_deleted} user(s).")
        except Exception as e:
            db.session.rollback()
            print(f"Error while deleting users: {str(e)}")

if __name__ == '__main__':
    delete_all_users()
