from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Table, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

# Initialize database
DATABASE_URL = "sqlite:///db/srt.db"
Base = declarative_base()

# Define Junction Table for Many-to-Many Relationship
cadet_group = Table(
    'cadet_group',
    Base.metadata,
    Column('cadet_group_id', Integer, primary_key=True),  # Adding primary key
    Column('cadet_id', Integer, ForeignKey('cadet.cadet_id', ondelete="CASCADE"), nullable=False),
    Column('group_id', Integer, ForeignKey('group.group_id', ondelete="CASCADE"), nullable=False),
    UniqueConstraint('cadet_id', 'group_id')  # Adding unique constraint
)

# Define Tables
class Achievement(Base):
    __tablename__ = 'achievement'
    achievement_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Status(Base):
    __tablename__ = 'status'
    status_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Activity(Base):
    __tablename__ = 'activity'
    activity_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Instructor(Base):
    __tablename__ = 'instructor'
    instructor_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)


class Cadet(Base):
    __tablename__ = 'cadet'
    cadet_id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)  # Telegram ID (unique for each user)
    telegram_username = Column(String, unique=True, nullable=True)  # Telegram username
    name = Column(String, nullable=False, unique=True)
    achievement_id = Column(Integer, ForeignKey('achievement.achievement_id', ondelete="CASCADE"))
    achievement = relationship("Achievement", backref="cadets")
    groups = relationship("Group", secondary=cadet_group, back_populates="cadets")  # Many-to-Many Relationship


class Group(Base):
    __tablename__ = 'group'
    group_id = Column(Integer, primary_key=True)
    tele_id = Column(Integer, nullable=True) 
    name = Column(String, nullable=True)
    cadets = relationship("Cadet", secondary=cadet_group, back_populates="groups")  # Many-to-Many Relationship


class srtInfo(Base):
    __tablename__ = 'srt_info'
    srt_id = Column(Integer, primary_key=True)
    cadet_id = Column(Integer, ForeignKey('cadet.cadet_id', ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey('activity.activity_id', ondelete="CASCADE"))
    datetime_in = Column(String, nullable=True)  # (YYYY-MM-DD HH:MM:SS)
    datetime_out = Column(String, nullable=True)
    created_on = Column(String, nullable=False)
    status_id = Column(Integer, ForeignKey('status.status_id', ondelete="CASCADE"))


# Create the Database Engine
engine = create_engine(DATABASE_URL)

# Create Tables
Base.metadata.create_all(engine)

print("Tables created successfully!")
