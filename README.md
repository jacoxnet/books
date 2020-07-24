# *CX Books*

This project was prepared to satisfy project1 in the online version of CS50x Web Programming with Python and JavaScript.

## Introduction

**CX Books** is a web application that allows users to see query information loaded in a database about 5000 books and to add and display reviews and ratings of these books.

In addition to registration and login, there are three basic functional pages in the web app.

- *Home* The home screen presents allows the user to enter a query in a search box.
- *Display search results* After conducting a search, the results are displayed on this screen in a table
- *Book and review display* After clicking on a book in the search results, this page allows the user to see additional information on a single book and to enter a review and rating.  

In addition, the web app provides an api to request book information given an ISBN number.

These pages and the API are described in more detail below.

## Technologies

The web app is implemented using Flask, python3, and SQL. The python code interacts with SQL using the SQLAlchemy library, but in this case only to make raw SQL queries. The app uses a PostgreSQL database provided for free by Heroku. It also uses the requests library to query the api for the goodreads.com site.

The foundation of the web app was code distributed for the finance app in the web track of the CS50x course.

## How to Use

### Creating the database structure

The web app depends on three preexisting tables in the SQL database: **books**, **reviews**, and **users**. The SQL creation commands for the tables are as follows:

```sql
CREATE SEQUENCE books_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE TABLE "public"."books" (
    "id" integer DEFAULT nextval('books_id_seq') NOT NULL,
    "isbn" character varying NOT NULL,
    "title" character varying NOT NULL,
    "author" character varying NOT NULL,
    "year" integer NOT NULL,
    CONSTRAINT "books_pkey" PRIMARY KEY ("id")
) WITH (oids = false);
```

```sql
CREATE SEQUENCE reviews_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE TABLE "public"."reviews" (
    "id" integer DEFAULT nextval('reviews_id_seq') NOT NULL,
    "user_id" integer,
    "book_id" integer,
    "review" character varying,
    "score" integer,
    CONSTRAINT "reviews_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "reviews_book_id_fkey" FOREIGN KEY (book_id) REFERENCES books(id) NOT DEFERRABLE,
    CONSTRAINT "reviews_user_id_fkey" FOREIGN KEY (user_id) REFERENCES users(id) NOT DEFERRABLE
) WITH (oids = false);
```

```sql
CREATE SEQUENCE users_id_seq INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE TABLE "public"."users" (
    "id" integer DEFAULT nextval('users_id_seq') NOT NULL,
    "fullname" character varying NOT NULL,
    "username" character varying NOT NULL,
    "password_hash" character varying NOT NULL,
    CONSTRAINT "users_id" PRIMARY KEY ("id")
) WITH (oids = false);
```

### Loading the **books** table

The books table must be pre-populated with books. Here the class provided a 5000-line csv file called **books.csv**, which had to loaded into the **books** table using **import.py**.

### Starting the App

After creating the database, and making sure as well that all requirements listed in **requirements.txt** have been installed, start the app under flask's development server in the project's home directory. 

```shell
$ flask run
```

### Files

- application.py  (main repository of python3 code)
- auxiliary.py (python functions called from application.py)
- README.md
- requirements.txt
- books.csv (supplied by class)
- templates directory
  - displaybook.html
  - error.html
  - layout.html
  - login.html
  - matchingbooks.html
  - register.html
  - search.html
  - import.py (loads the database with the data from books.csv)
- static directory
  - book.png (app pic)
  - favicon.ico (icon version of app pic)
  - styles.css

## Instructions for Using Web Pages

### Homepage

This page contains a single search box. The user may enter a single query that is run against the author, title, and ISBN fields.

### Search results

This page displays the search results in a table listing ISBN, title, author, and year of the matching books. The search matches partial strings as well as complete names (thus a search for "5005" would return any books with that string in any of the three fields. The ISBN number field is a link to display further information on the book. The user can also return to the search page by clicking the "New Search" button.

### Display book and reviews

This page displays detailed information about the book. The display includes a cover picture, if one can be obtained from the simple URL-based API at covers.openlibrary.org/b/isbn/. It also includes the number of ratings and the ratings average as reported by the goodreads API, which is accessed through the requests library. Finally, it includes the text of the reviews and the ratings of each user of the web app.

The user can submit a rating (1 - 5) and review in appropriate boxes toward the bottom of the page, or ask for another "New Search."

### API

The app contains an API that is publicly accessible wtihout key or login at /API/<isbn>. Given an ISBN number, the site returns a JSON object with the book's title, author, year, ISBN, number of reviews on this web app, and average rating of the reviewers.
