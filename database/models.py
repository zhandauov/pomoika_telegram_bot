from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytz



ALMATY_TZ = pytz.timezone('Asia/Almaty')
TIME_NOW = datetime.now(ALMATY_TZ)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    phone_number = Column(String(20), primary_key=True)
    name = Column(String(100))
    last_name = Column(String(100))
    date_created = Column(DateTime, default=TIME_NOW)

class CarWash(Base):
    __tablename__ = "car_washes"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    contact_phone_number = Column(String(20))
    available_hours = Column(String(100))  # Hours are stored as comma-separated string
    link_2gis = Column(String(500))
    created_date = Column(DateTime, default=TIME_NOW)
    modified_date = Column(DateTime, default=TIME_NOW, onupdate=TIME_NOW)
    price = Column(Integer)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    user_phone_number = Column(String(20), ForeignKey('users.phone_number'))
    car_wash_id = Column(Integer, ForeignKey('car_washes.id'))
    start_date = Column(DateTime, default=TIME_NOW)
    end_date = Column(DateTime)
    status = Column(String(50))
    price = Column(Integer)

    user = relationship("User", backref="appointments")
    car_wash = relationship("CarWash", backref="appointments")


engine = create_engine('sqlite:///sqlite_pomoika.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
