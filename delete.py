from sqlalchemy import create_engine
from instance.config import DATABASE_URL

# Set up database
engine = create_engine(DATABASE_URL)

sql = "delete from \"Books\";"

try:
    engine.execute(sql)
except Exception as e:
    print(e)
