To use the keydb, first create a database (for example, named 'keydb'). Then
run the schema.sql file on the database to create the necessary tables.
Next, enter the database connection information in the config.py file.

Important: If the website is running on the same server as the keydb resides on,
make sure the config.py file is not readable by the website (that is, not
readable by the webserver user if the seattlegeni website is running as the
webserver user).
