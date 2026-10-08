from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select
from pydantic import EmailStr


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

sqlite_file_name = "events.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(
    sqlite_url,
    echo=True,
    connect_args={"check_same_thread": False}
)


# --------------------------------------------------
# EVENT MODEL
# --------------------------------------------------

class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    venue: str
    capacity: int = Field(gt=0)
    organizer: str
    status: str = "Open"


# --------------------------------------------------
# RESERVATION MODEL
# --------------------------------------------------

class Reservation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    event_id: int
    student_name: str
    roll_number: str
    email: EmailStr


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class EventCreate(SQLModel):
    title: str
    venue: str
    capacity: int = Field(gt=0)
    organizer: str
    status: str = "Open"


class EventUpdate(SQLModel):
    title: str | None = None
    venue: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    organizer: str | None = None
    status: str | None = None


class ReservationCreate(SQLModel):
    student_name: str
    roll_number: str
    email: EmailStr


# --------------------------------------------------
# FASTAPI APPLICATION
# --------------------------------------------------

app = FastAPI(
    title="College Event Reservation API",
    description="API for managing college events and student reservations",
    version="1.0.0"
)


# --------------------------------------------------
# CREATE DATABASE TABLES
# --------------------------------------------------

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


# --------------------------------------------------
# 1. CREATE EVENT
# POST /events
# --------------------------------------------------

@app.post("/events", response_model=Event)
def create_event(event: EventCreate):

    if event.status not in ["Open", "Closed"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be Open or Closed"
        )

    if event.title.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Event title cannot be empty"
        )

    with Session(engine) as session:
        new_event = Event(
            title=event.title,
            venue=event.venue,
            capacity=event.capacity,
            organizer=event.organizer,
            status=event.status
        )

        session.add(new_event)
        session.commit()
        session.refresh(new_event)

        return new_event


# --------------------------------------------------
# 2. GET ALL EVENTS
# GET /events
# --------------------------------------------------

@app.get("/events", response_model=list[Event])
def get_events():

    with Session(engine) as session:
        events = session.exec(
            select(Event)
        ).all()

        return events


# --------------------------------------------------
# 3. GET SPECIFIC EVENT
# GET /events/{event_id}
# --------------------------------------------------

@app.get("/events/{event_id}", response_model=Event)
def get_event(event_id: int):

    with Session(engine) as session:

        event = session.get(Event, event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        return event


# --------------------------------------------------
# 4. UPDATE EVENT
# PUT /events/{event_id}
# --------------------------------------------------

@app.put("/events/{event_id}", response_model=Event)
def update_event(event_id: int, event_data: EventUpdate):

    with Session(engine) as session:

        event = session.get(Event, event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        if event_data.status is not None:
            if event_data.status not in ["Open", "Closed"]:
                raise HTTPException(
                    status_code=400,
                    detail="Status must be Open or Closed"
                )
            event.status = event_data.status

        if event_data.title is not None:
            if event_data.title.strip() == "":
                raise HTTPException(
                    status_code=400,
                    detail="Event title cannot be empty"
                )
            event.title = event_data.title

        if event_data.venue is not None:
            event.venue = event_data.venue

        if event_data.capacity is not None:

            reservation_count = len(
                session.exec(
                    select(Reservation)
                    .where(Reservation.event_id == event_id)
                ).all()
            )

            if event_data.capacity < reservation_count:
                raise HTTPException(
                    status_code=400,
                    detail="Capacity cannot be less than current reservations"
                )

            event.capacity = event_data.capacity

        if event_data.organizer is not None:
            event.organizer = event_data.organizer

        session.add(event)
        session.commit()
        session.refresh(event)

        return event


# --------------------------------------------------
# 5. DELETE EVENT
# DELETE /events/{event_id}
# --------------------------------------------------

@app.delete("/events/{event_id}")
def delete_event(event_id: int):

    with Session(engine) as session:

        event = session.get(Event, event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        reservations = session.exec(
            select(Reservation)
            .where(Reservation.event_id == event_id)
        ).all()

        for reservation in reservations:
            session.delete(reservation)

        session.delete(event)
        session.commit()

        return {
            "message": "Event deleted successfully"
        }


# --------------------------------------------------
# 6. CREATE RESERVATION
# POST /events/{event_id}/reserve
# --------------------------------------------------

@app.post("/events/{event_id}/reserve", response_model=Reservation)
def create_reservation(
    event_id: int,
    reservation_data: ReservationCreate
):

    if reservation_data.student_name.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="Student name cannot be empty"
        )

    with Session(engine) as session:

        # Check whether event exists
        event = session.get(Event, event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        # Check whether event is open
        if event.status != "Open":
            raise HTTPException(
                status_code=400,
                detail="Reservations are closed for this event"
            )

        # Count existing reservations
        reservations = session.exec(
            select(Reservation)
            .where(Reservation.event_id == event_id)
        ).all()

        booked = len(reservations)

        # Check capacity
        if booked >= event.capacity:
            raise HTTPException(
                status_code=400,
                detail="Event is full. No seats are available."
            )

        # Create reservation
        reservation = Reservation(
            event_id=event_id,
            student_name=reservation_data.student_name,
            roll_number=reservation_data.roll_number,
            email=reservation_data.email
        )

        session.add(reservation)
        session.commit()
        session.refresh(reservation)

        return reservation


# --------------------------------------------------
# 7. GET EVENT RESERVATIONS
# GET /events/{event_id}/reservations
# --------------------------------------------------

@app.get(
    "/events/{event_id}/reservations",
    response_model=list[Reservation]
)
def get_event_reservations(event_id: int):

    with Session(engine) as session:

        event = session.get(Event, event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        reservations = session.exec(
            select(Reservation)
            .where(Reservation.event_id == event_id)
        ).all()

        return reservations


# --------------------------------------------------
# 8. DELETE RESERVATION
# DELETE /reservations/{reservation_id}
# --------------------------------------------------

@app.delete("/reservations/{reservation_id}")
def delete_reservation(reservation_id: int):

    with Session(engine) as session:

        reservation = session.get(
            Reservation,
            reservation_id
        )

        if not reservation:
            raise HTTPException(
                status_code=404,
                detail="Reservation not found"
            )

        session.delete(reservation)
        session.commit()

        return {
            "message": "Reservation cancelled successfully"
        }


# --------------------------------------------------
# 9. EVENT AVAILABILITY
# GET /events/{event_id}/availability
# --------------------------------------------------

@app.get("/events/{event_id}/availability")
def get_availability(event_id: int):

    with Session(engine) as session:

        event = session.get(Event, event_id)

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        reservations = session.exec(
            select(Reservation)
            .where(Reservation.event_id == event_id)
        ).all()

        booked = len(reservations)

        remaining = event.capacity - booked

        return {
            "capacity": event.capacity,
            "booked": booked,
            "remaining": remaining
        }