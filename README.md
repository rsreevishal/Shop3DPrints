# Shop3DPrints

## Development guide

* All of the pages are stored in the `templates/` directory.
Each page inherits from `base.html` and adds the necessary markup.
* All of the static files (CSS, JS, images, etc.) are stored in the `api/static` directory.
* See the templates for examples of extending the base template and accessing static files.
* Run a local server with `python3 manage.py runserver 8000`. You have to run a server to properly view the pages.
* You can create a new page in `api/urls.py`.


## Local Environment Setup
1. Clone the repo - `git clone <repo_url>` in your working directory
2. Create a virtual env - `virtualenv academyenv` and then activate thee virtual env - `source /academyenv/bin/activate`
(Note: You should be in the project root directory)
3. If step 2 gives you an error, make sure you have virtual env installed. Run `pip3 install --upgrade pip` and 
`pip3 install virtualenv` to install virtualenv
4. Make sure pip points to your activated virtual env via `which pip` and then run `pip install -r requirements.txt`
5. Go to `/academy_backend` sub dir and make a .env file - `vim .env` and paste the env configuration in the slack
6. In the env file, make the following change if you want to use the local sqlite db - `DJANGO_DATABASE=debug`
7. Run `python manage.py makemigrations` and then `python manage.py migrate` ONLY if you are using sqlite db. (Note: Make sure
you are in the project root directory)
8. You can create a superuser(for Django admin) by running `python manage.py createsuperuser` and follow the instructions
9. Run `python manage.py runserver` to locally run the application
