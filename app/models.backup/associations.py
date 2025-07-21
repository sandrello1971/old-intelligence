# app/models/associations.py
from sqlalchemy import Table, Column, Integer, ForeignKey
from app.core.database import Base
from sqlalchemy import Table, Column, Integer, ForeignKey

# Tabella ponte Ticket <-> Hashtag
ticket_hashtag = Table(
    'ticket_hashtag', Base.metadata,
    Column('ticket_id', Integer, ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True),
    Column('hashtag_id', Integer, ForeignKey('hashtags.id', ondelete='CASCADE'), primary_key=True)
)

# Tabella ponte Task <-> Hashtag
task_hashtag = Table(
    'task_hashtag', Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('hashtag_id', Integer, ForeignKey('hashtags.id', ondelete='CASCADE'), primary_key=True)
)
