EGASP Project
This project is the EGASP Database, a comprehensive system for storing and analyzing data related to various health assessments. Below is the guide to set up the project on your local machine.

# Getting Started
1. Clone the Repository

Start by cloning the repository from GitHub:
 git clone https://github.com/squarfie/EGASP_project.git


2. Create a Virtual Environment

Once the repository is cloned, navigate to the project directory and create a Python virtual environment. This will isolate the dependencies for this project.


cd egasp_project

python -m venv egasp #or customize the name of your venv

3. Activate the Virtual Environment:
   
Activate the virtual environment. The activation command depends on your operating system.

Windows:

egasp\Scripts\activate

Mac/Linux:

source egasp/bin/activate

You should now see (egasp) before your command prompt, indicating that the virtual environment is active.

4. Install the Required Modules

Now, install all the necessary dependencies listed in the requirements.txt file.

 pip3 install -r requirements.txt

This will install all the Python modules required for the project.

5. Set Up the Database (if applicable)

If the project uses an SQLite database or any other type of database, follow these steps to set it up.

Create a new postgresql database

# use the details below:
default (for testing): test_db 

for deployment: Egasp_db  

----> you may need to change the DB_NAME in .env 

----> uncomment DB_NAME: Egasp_db, comment-out DB_NAME: test_db


# run migrations

python manage.py makemigrations

python manage.py migrate

# Start the application (development mode)
$ python manage.py runserver # default port 8000

6. Set up your codes, breakpoints, antibiotics and locations using the "Utilities" Menu options





