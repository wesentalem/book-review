
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def setID(self, id):
        self.id = id


class Book:
    def __init__(self, ISBN, bookTitle, bookAuthor, publicationDate):
        self.ISBN = ISBN
        self.bookTitle = bookTitle
        self.bookAuthor = bookAuthor
        self.publicationDate = publicationDate
        self.rating = 0

    def setAverageRating(self, rating):
        self.rating = rating


class Review:
    def __init__(self, userID, isbn, username, review, rating):
        self.userID = userID
        self.ISBN = isbn
        self.username = username
        self.review = review
        self.rating = rating
