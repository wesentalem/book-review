import csv
from sqlalchemy import create_engine
from instance.config import DATABASE_URL
import os
import json
from models import Book

# Set up database
#engine = create_engine(os.getenv("DATABASE_URL"))
engine = create_engine(DATABASE_URL)
errors = []

# Get absolute path
dirname = os.path.dirname(__file__)
csvFilePath = os.path.join(dirname, 'books.csv')

with open(csvFilePath, newline='') as csvFile:
    reader = csv.DictReader(csvFile)
    count = 0
    for row in reader:

        print("{:<13} | {:<30} | {:<30} | {:<5} ... ".format(
            row['isbn'], row['title'], row['author'], row['year']), end="")

        newBook = Book(row['isbn'].strip(), row['title'].strip(),
                       row['author'].strip(), row['year'].strip())

        if('\'' in row['title']):
            row['title'].replace('\'', '`')

        sqlBookInsert = "insert into \"Books\" (isbn, book_title, book_author, publication_date)"
        sqlBookValues = "values('{book.ISBN}', '{book.bookTitle}', '{book.bookAuthor}', {book.publicationDate})".format(
            book=newBook)

        try:
            engine.execute("{} {}".format(sqlBookInsert, sqlBookValues))
        except Exception as e:
            print("[ERROR]\n")
            errors.append({'error': str(
                e.args[0]), 'line': count, 'book_title': newBook.bookTitle})
        else:
            print("[COMPLETE]\n")

        count += 1

    print("-----UPLOAD COMPLETE ------")
    print(" Number of errors: ", len(errors))
    if(len(errors) == 0):
        print("\n Upload completed with no errors")
    elif(len(errors) == 1):
        print("\n\tLine number:{line}\n\tError:{error}\n\tBook Title:{title}".format(
            error=errors[0]['error'], line=errors[0]['line'], title=errors[0]['book_title']))
    else:
        done = False
        while not done:
            print("Do you wish to generate a error report?")
            query = input("(y\\n):")
            if(query == 'y'):
                errorFilePath = os.path.join(dirname, 'error_report.json')
                with open(errorFilePath, 'w') as outFile:
                    json.dump(errors, outFile)
                done = True
                print("error_report.json generated")
                os.startfile(errorFilePath)
            elif(query == 'n'):
                done = True
