from sqlalchemy import Column, DateTime, Boolean, String
from sqlalchemy import Integer

from database.base import Base


class DBRun(Base):
    run_number = Column(Integer, primary_key=True)
    run_date = Column(DateTime)

    def __repr__(self):
        return '<Run number = %d, Run date =%s>' % (self.run_number, str(self.run_date))