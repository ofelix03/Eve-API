# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, scoped_session
#
# engine = create_engine('postgresql://postgres:123@localhost:5432/Eve', echo=True)
#
# Session = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=False))
# session = Session()


#SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:123@db:5432/Eve2'
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres@127.0.0.1:5432/Eve2'
SQLALCHEMY_ECHO = True
SQLALCHEMY_TRACK_MODIFICATIONS = False