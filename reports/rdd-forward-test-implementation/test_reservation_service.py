from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
import unittest

from reservation_service import (
    NotFoundError,
    ReservationConflictError,
    ReservationService,
    ValidationError,
)


BASE_TIME = datetime(2026, 1, 1, 9, 0, 0)


def at_hour(hour):
    return BASE_TIME + timedelta(hours=hour)


class ReservationServiceTests(unittest.TestCase):
    def test_create_room_then_list_rooms_returns_paginated_rooms(self):
        service = ReservationService()

        first = service.create_room("Blue")
        second = service.create_room("Green")

        self.assertEqual(first.name, "Blue")
        self.assertEqual(second.name, "Green")
        self.assertEqual([room.name for room in service.list_rooms(limit=1, offset=1)], ["Green"])

    def test_list_rooms_rejects_pagination_values_outside_bounds(self):
        service = ReservationService()

        with self.assertRaises(ValidationError):
            service.list_rooms(limit=0)
        with self.assertRaises(ValidationError):
            service.list_rooms(limit=ReservationService.MAX_PAGE_SIZE + 1)
        with self.assertRaises(ValidationError):
            service.list_rooms(limit=1, offset=-1)

    def test_create_reservation_uses_half_open_ranges(self):
        service = ReservationService()
        room = service.create_room("Blue")

        first = service.create_reservation(room.id, "Ada", at_hour(0), at_hour(1))
        second = service.create_reservation(room.id, "Grace", at_hour(1), at_hour(2))

        self.assertEqual(first.room_id, room.id)
        self.assertEqual(second.start, first.end)

    def test_create_reservation_rejects_same_room_overlap(self):
        service = ReservationService()
        room = service.create_room("Blue")
        service.create_reservation(room.id, "Ada", at_hour(0), at_hour(2))

        with self.assertRaises(ReservationConflictError):
            service.create_reservation(room.id, "Grace", at_hour(1), at_hour(3))

    def test_create_reservation_allows_overlap_in_different_rooms(self):
        service = ReservationService()
        blue = service.create_room("Blue")
        green = service.create_room("Green")

        first = service.create_reservation(blue.id, "Ada", at_hour(0), at_hour(2))
        second = service.create_reservation(green.id, "Grace", at_hour(1), at_hour(3))

        self.assertNotEqual(first.room_id, second.room_id)

    def test_cancel_reservation_frees_the_room_for_that_range(self):
        service = ReservationService()
        room = service.create_room("Blue")
        reservation = service.create_reservation(room.id, "Ada", at_hour(0), at_hour(2))

        cancelled = service.cancel_reservation(reservation.id)
        replacement = service.create_reservation(room.id, "Grace", at_hour(1), at_hour(3))

        self.assertTrue(cancelled.cancelled)
        self.assertEqual(replacement.guest, "Grace")

    def test_cancel_reservation_rejects_unknown_id(self):
        service = ReservationService()

        with self.assertRaises(NotFoundError):
            service.cancel_reservation(404)

    def test_concurrent_same_room_overlap_allows_only_one_reservation(self):
        service = ReservationService()
        room = service.create_room("Blue")
        worker_count = 8
        start_line = Barrier(worker_count)

        def attempt(_):
            start_line.wait()
            try:
                return service.create_reservation(room.id, "Ada", at_hour(0), at_hour(2))
            except ReservationConflictError:
                return None

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(attempt, range(worker_count)))

        successful = [result for result in results if result is not None]
        self.assertEqual(len(successful), 1)


if __name__ == "__main__":
    unittest.main()
