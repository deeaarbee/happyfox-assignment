# Happy fox assignment

This project was given as an assignment for the backend developer role at HappyFox Inc.

## Description

This is a standalone python script that connects with Gmail API to filter and perform actions on 
the emails based on certain rules.

### Pre-requisites

```
Python 3.5 above
SQLite
Virtualenv
```

### Installing

Open the terminal.

Clone the repository
```
git clone https://github.com/deeaarbee/happyfox-assignment
cd happyfox-assignment
```

Create virtual environment and activate

```
virtualenv -p python3 happyenv
source happyenv/bin/activate
```

Install requirements

```
pip3 install -r requirements.txt
```

Place the client.json file in the gmail directory.

```
cd gmail
# paste the client.json file
```

In the settings.py in the config directory:

```
# set value for 
MAX_RESULTS_PER_PAGE = 10
TOTAL_PAGES_TO_READ = 2
TESTING = False
```


Run main.py

```
python3 main.py
```

The web browser will open for OAuth for Gmail. Accepting it will show the menu in the terminal.

##### Sample terminal output:
```
+--------+-----------+
| CHOICE | PREDICATE |
+--------+-----------+
|   1    |    ALL    |
|   2    |    ANY    |
|   q    |    QUIT   |
+--------+-----------+
Enter choice: 1
```

## Running the tests

To run the test:

Go to settings.py in config directory:
```
# SET
TESTING = True
```

Now in the project root directory:
```
python3 test.py
```

A new test database will be created to perform the tests.

##### NOTE : Never run test with main database. Set TESTING=True.

##### Sample Test output:

```
(happyenv) bash-3.2$ python3 test.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.038s

OK
```

## Further improvements (Not required for the given tasks.)

* Database schema can be improved to make it scalable and store all fields of an email.
* Pagination support to read emails can be added.
* Mock tests for api requests can be written.


## License

None


