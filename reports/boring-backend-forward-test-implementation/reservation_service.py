from dataclasses import dataclass, replace
from threading import RLock


class ReservationError(Exception):
    pass


class ValidationError(ReservationError):
    pass


class NotFoundError(ReservationError):
    pass


class ReservationConflictError(ReservationError):
    pass


@dataclass(frozen=True)
class Room:
    id: int
    name: str


@dataclass(frozen=True)
class Reservation:
    id: int
    room_id: int
    guest: str
    start: object
    end: object
    cancelled: bool = False


class ReservationService:
    MAX_PAGE_SIZE = 50

    def __init__(self):
        self._rooms = {}
        self._reservations = {}
        self._next_room_id = 1
        self._next_reservation_id = 1
        # This protects only threads in this Python process, not multiple workers or hosts.
        self._lock = RLock()

    def create_room(self, name):
        with self._lock:
            room = Room(id=self._next_room_id, name=name)
            self._next_room_id += 1
            self._rooms[room.id] = room
            return room

    def list_rooms(self, *, limit, offset=0):
        if limit < 1 or limit > self.MAX_PAGE_SIZE:
            raise ValidationError("limit must be between 1 and MAX_PAGE_SIZE")
        if offset < 0:
            raise ValidationError("offset must be non-negative")

        with self._lock:
            return list(self._rooms.values())[offset : offset + limit]

    def create_reservation(self, room_id, guest, start, end):
        if start >= end:
            raise ValidationError("reservation start must be before end")

        with self._lock:
            if room_id not in self._rooms:
                raise NotFoundError("room not found")
            for reservation in self._reservations.values():
                if (
                    reservation.room_id == room_id
                    and not reservation.cancelled
                    and start < reservation.end
                    and reservation.start < end
                ):
                    raise ReservationConflictError("room is already reserved for that range")

            reservation = Reservation(
                id=self._next_reservation_id,
                room_id=room_id,
                guest=guest,
                start=start,
                end=end,
            )
            self._next_reservation_id += 1
            self._reservations[reservation.id] = reservation
            return reservation

    def cancel_reservation(self, reservation_id):
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise NotFoundError("reservation not found")
            cancelled = replace(reservation, cancelled=True)
            self._reservations[reservation_id] = cancelled
            return cancelled
