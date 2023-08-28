from database.models import User, CarWash, Appointment, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Database():
    def __init__(self, db_filename):
        self.engine = create_engine(db_filename)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_user(self, record):
        session = self.Session()
        self.session.add(record)
        session.commit()
        session.close()

# database = Database('sqlite:///sqlite_pomoika.db')