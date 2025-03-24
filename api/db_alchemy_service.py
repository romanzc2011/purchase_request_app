
from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Approval(Base):
    __tablename__ =  "approvals"

    id = Column(Integer, primary_key=True, autoincrement=False)
    reqID = Column(String, nullable=False)
    recipient = Column(String, nullable=False)
    requester = Column(String, nullable=False)
    budgetObjCode = Column(String)
    fund = Column(String)
    location = Column(String)
    status = Column(String)

    def __repr__(self):
        return f"<Approval(reqID='{self.reqID}', requester='{self.requester}')"
    
engine = create_engine('sqlite:///db/purchase_requests.db', echo=True)
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

approvals = session.query(Approval).all()

for approval in approvals:
    print(approval.reqID, approval.requester, approval.status)