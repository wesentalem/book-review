# Web Programming Project I

Book review site

## Dependencies

Use the package manager pip to install the necessary requirements

```bash
python -m pip install -r requirement.txt
```

## Usage

You can run the application by default

```bash
python application.py
python import.py
```

OR

You can run

```
flask run
```

## Some things to note

1.Heroku doesn't work sometimes in AAiT

2.Sometimes the search doesn't work correctly. Stop and
restart the server if it does that

3.Covers, descriptions, subject lists are gotten from the
open library api but there isn't one for all the books

4.All the books in books.csv have already been pushed to the
database. Running import.py without replacing with new books.csv
will result in duplicate error. 

Alternatively, if you don't wish to replace books.csv, you can run 
the delete.py which will empty the books database

<img href="https://github.com/wesentalem/book-review/blob/master/screenshot.PNG?raw=true" alt="screenshot1">
<img href="https://raw.githubusercontent.com/wesentalem/book-review/master/screenshot2.PNG" alt="screenshot2">
