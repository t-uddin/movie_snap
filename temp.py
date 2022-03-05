from cs50 import SQL

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///MM.db")

matchlist = db.execute("SELECT movie_id, title, AVG(rating) AS rating FROM watchlist WHERE user_id = 1 OR user_id = 2 GROUP BY movie_id HAVING COUNT(*) >1 ORDER BY rating DESC")

for movie in matchlist:
    movie['movie_id'] = str(movie['movie_id']).zfill(10)


print(matchlist)