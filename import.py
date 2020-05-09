import csv
import os

# adapted from import.py in Brian's src3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    # skip over header line
    next(reader)
    count = 0
    for isbn, title, author, year in reader:
        yearnum = int(year)
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": yearnum})
        
        count += 1
        if count % 100 == 0:
            print("*", end="")
    db.commit()
    
    print(f"\nAdded {count} books.")
    
if __name__ == "__main__":
    main()
