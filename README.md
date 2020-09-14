# academy_backend

## Development guide

* All of the pages are stored in the `templates/` directory.
Each page inherits from `base.html` and adds the necessary markup.
* All of the static files (CSS, JS, images, etc.) are stored in the `api/static` directory.
* See the templates for examples of extending the base template and accessing static files.
* Run a local server with `python3 manage.py runserver 8000`. You have to run a server to properly view the pages.
* You can create a new page in `api/urls.py`.
