# EGASP Project
This project is the EGASP Database. Below is the guide to set up the project on your local machine.

# Getting Started


1. Open terminal and Clone the Repository

Start by cloning the repository from GitHub:
git clone https://github.com/squarfie/EGASP_project.git

2. Create a Virtual Environment
Once the repository is cloned, navigate to the project directory and create a Python virtual environment. This will isolate the dependencies for the project.


cd egasp_project
python -m venv egasp  # or customize the name of your virtual environment

3. Activate the Virtual Environment
Activate the virtual environment. The activation command depends on your operating system:

Windows:

egasp\Scripts\activate

Mac/Linux:

source egasp/bin/activate

You should now see (egasp) before your command prompt, indicating that the virtual environment is active.

4. Install the Required Modules
Install all the necessary dependencies listed in the requirements.txt file:

pip install -r requirements.txt

This will install all the Python modules required for the project.

5. Set Up the Database

If the project uses an SQLite or PostgreSQL database, follow these steps to set it up:

# Create a new PostgreSQL database.

Database names:

Default (for testing): test_db

For deployment: Egasp_db

⚡ You may need to update the DB_NAME in the .env file.
⚡ Uncomment DB_NAME=Egasp_db for deployment, and comment out DB_NAME=test_db.

# Run migrations:

python manage.py makemigrations
python manage.py migrate

6. Start the Application (Development Mode)
To start the server:

python manage.py runserver  # Default port 8000

or, if you want the server accessible over the network:

python manage.py runserver 0.0.0.0:8000

🔔 You can change the port number if desired.
🔔 Important: If deploying with Gunicorn, ensure the port is also updated in the gunicorn-cfg.py configuration file.

# Application Setup:

7. Register Your Account
Register your name and password, then log in to the system.

8. Configure System Settings
Configure your codes, breakpoints, antibiotics, and locations using the options under the "Utilities" menu.

9. Upload Breakpoints and Antibiotics
Use the "Breakpoints_egasp.xlsx" template.

First, add the antibiotics and breakpoints into the Excel file.

Upload it through the "Breakpoints" option under the "Utilities" menu on the dashboard.

You can find the template files inside the template_docs folder located in the main app directory.

⚡ You can also add more antibiotics and breakpoints directly through the database.
⚡ However, if you are setting up the database for the first time, it is more convenient to use the Excel file.

10. Upload Cities List
Click on "Add Cities" under the Utilities menu, and upload the file named "Citieslist.xlsx" to add the complete list of cities in the Philippines.

✨ If you need to add more cities later, you do not need to modify the Excel file.
✨ The database provides a feature to add and edit the list of cities and barangays directly.

# Done! 🎉
You now have the EGASP Database running on your local machine!


# RUNNING IN PRODUCTION MODE

# Prerequisites
Before proceeding, ensure that you have the following:

Docker and Docker Compose installed on your machine or server.

A .env file containing the necessary PostgreSQL credentials.

Your project files, including configurations for Gunicorn, Nginx, and Docker.

# Setup Instructions

1. Create the .env file

In the root of your project, make sure you have created a .env file containing the following environment variables for PostgreSQL:

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password

Replace your_db_name, your_db_user, and your_db_password with your actual PostgreSQL database credentials.

2. Build the Docker Images

Use the following command to build the Docker images based on the Dockerfiles and configurations you have set up:

docker-compose build
Start the Services

3. Start the services (Django app, PostgreSQL database, and Nginx) in detached mode by running:

docker-compose up -d

This will launch the containers in the background.

4. Run Migrations

Apply the Django database migrations to set up the schema by running:

docker-compose exec web python manage.py migrate

5. Collect Static Files

Collect static files to be served by Nginx:

docker-compose exec web python manage.py collectstatic --noinput

6. Running the Application
Once all the services are up and running, the application should be accessible.

---> Local Development

You can access the app on your local machine at http://localhost.

---> Production Server

If you are deploying to a production server, replace localhost with your server's IP address or domain name.

7. Accessing the Application

After running the above commands and confirming that the services are running, you can access the application on the following URLs:

Local Machine: http://localhost

Remote Server: http://<your_server_ip_or_domain>

8. Optional Steps
Monitoring Logs

You can monitor the logs for any of the containers (web, nginx, db) by running:

docker-compose logs -f

9. Stopping the Services

To stop all services, use the following command:

docker-compose down

10. Restarting the Services

If you need to restart all services, use:

docker-compose restart

# Notes for Production

Security: Make sure your PostgreSQL credentials and any other sensitive information are securely stored in the .env file and not exposed in public repositories.

Scaling: If your application grows, you might want to adjust the number of Gunicorn workers or scale your database and web containers.

Backups: Set up regular backups for the PostgreSQL database to ensure data is protected.

# Troubleshooting
PostgreSQL Connection Errors:

Ensure the credentials in your .env file are correct.

Verify that PostgreSQL is running using docker-compose ps.

Static Files Not Loading:

Run python manage.py collectstatic to ensure static files are collected properly.

Make sure Nginx is correctly configured to serve the static files from the correct location.

# Gunicorn Issues:

If Gunicorn isn’t starting, check the logs with docker-compose logs web for any errors related to Gunicorn or Django.

Ensure the correct Gunicorn command is being executed by reviewing the docker-compose.yml configuration.

By following this guide, you should be able to successfully deploy your EGASP application in a production environment.