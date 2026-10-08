# College Event Reservation API

A FastAPI REST API for managing college events and student reservations.

## Features

* Create, view, update and delete events
* Create and cancel student reservations
* Check event availability
* Prevent reservations when an event is full
* Prevent reservations for closed events
* SQLite database
* SQLModel for database operations
* Email validation
* Automatic database table creation

## Technologies

* Python
* FastAPI
* SQLModel
* SQLite
* Uvicorn

## Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/event-reservation-api.git
cd event-reservation-api
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn main:app --reload
```

Open the Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Events

* `POST /events` - Create an event
* `GET /events` - Get all events
* `GET /events/{event_id}` - Get a specific event
* `PUT /events/{event_id}` - Update an event
* `DELETE /events/{event_id}` - Delete an event

### Reservations

* `POST /events/{event_id}/reserve` - Create a reservation
* `GET /events/{event_id}/reservations` - Get event reservations
* `DELETE /reservations/{reservation_id}` - Cancel a reservation
* `GET /events/{event_id}/availability` - Check event availability

## Database

The application uses SQLite with SQLModel. The required tables are automatically created when the application starts.

## Capacity Management

The API checks the number of existing reservations before creating a new reservation. If the event reaches its capacity, further reservations are rejected.

Reservations are also rejected when an event is marked as `Closed`.

## Proof of Work

The project was tested using FastAPI Swagger UI with screenshots demonstrating:

* Event creation
* Retrieving events
* Successful reservation
* Retrieving reservations
* Event availability
* Reservation cancellation
* Rejected reservation when the event is full or closed
