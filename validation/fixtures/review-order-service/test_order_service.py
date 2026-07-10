import unittest

import order_service


class OrderServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        order_service.reset_state()

    def test_create_and_exact_retry(self) -> None:
        first = order_service.create_order("acct-a", "widget", 1, "key-1")
        replay = order_service.create_order("acct-a", "widget", 1, "key-1")

        self.assertEqual(first, replay)
        self.assertEqual(order_service.STOCK["widget"], 1)

    def test_rejects_insufficient_stock(self) -> None:
        status, body = order_service.create_order("acct-a", "widget", 3, "key-2")

        self.assertEqual(status, 409)
        self.assertEqual(body, {"error": "insufficient_stock"})


if __name__ == "__main__":
    unittest.main()
