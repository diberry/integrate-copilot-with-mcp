# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install -r ../requirements.txt
   ```

2. Create at least one teacher account. Passwords are stored as salted PBKDF2
   hashes in the ignored local file `teachers.json`, not as plaintext:

   ```
   python create_teacher.py teacher-name
   ```

3. Run the application:

   ```
   uvicorn app:app --reload
   ```

4. Open your browser and go to:
   - Application: http://localhost:8000/
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

Students can view activities and participant lists without logging in. Only an
authenticated teacher can register or unregister students. Teacher sessions
expire after eight hours and are also cleared when the server restarts.

## Tests

Install the development dependencies and run the test suite:

```
pip install -r ../requirements-dev.txt
python -m unittest discover -s tests
```

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
