import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stream import dispatcher
from stream import driver


class TestDispatcher(unittest.TestCase):
    def test_build_message_good(self):
        """Test that normal messages (non-10th) have a zone field."""
        rk, msg = dispatcher.build_message(1)
        self.assertIn("zone", msg)
        self.assertNotIn("malformed", msg)
        self.assertIn(msg["city"], dispatcher.CITIES)
        self.assertIn(msg["zone"], dispatcher.ZONES[msg["city"]])
        self.assertIn(msg["type"], dispatcher.TYPES)
        self.assertEqual(rk, f"{msg['city']}.{msg['zone']}.{msg['type']}")

    def test_build_message_bad(self):
        """Test that every 10th message is malformed (missing zone)."""
        rk, msg = dispatcher.build_message(10)
        self.assertNotIn("zone", msg)
        self.assertTrue(msg["malformed"])
        # routing key has only 2 parts: city.type
        self.assertEqual(len(rk.split(".")), 2)

    def test_dispatcher_main_publishes_11_messages(self):
        """Test that main() publishes 11 messages and stops on KeyboardInterrupt."""
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_conn.channel.return_value = mock_channel

        publish_calls = []

        def fake_publish(exchange, routing_key, body):
            publish_calls.append((routing_key, json.loads(body)))
            if len(publish_calls) == 11:
                raise KeyboardInterrupt()

        mock_channel.basic_publish.side_effect = fake_publish

        with patch('stream.dispatcher.get_connection', return_value=mock_conn):
            with patch('stream.dispatcher.time.sleep'):  # Speed up test
                dispatcher.main()

        # Check that 11 messages were published
        self.assertEqual(len(publish_calls), 11)
        # Check that the 10th message (index 9) is malformed
        rk_10, msg_10 = publish_calls[9]
        self.assertNotIn("zone", msg_10)
        self.assertTrue(msg_10["malformed"])
        # Check that the 1st message is well-formed
        rk_1, msg_1 = publish_calls[0]
        self.assertIn("zone", msg_1)


class TestDriver(unittest.TestCase):
    def test_driver_callback_ack(self):
        """Test that a good message (with zone) is ACKed."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 42
        mock_method.routing_key = "bangalore.koramangala.ride"

        body = json.dumps({
            "id": "REQ-0001",
            "city": "bangalore",
            "zone": "koramangala",
            "type": "ride",
            "ts": 1234567890.0
        }).encode("utf-8")

        driver.process_message("Ravi", mock_ch, mock_method, body)

        mock_ch.basic_ack.assert_called_once_with(delivery_tag=42)
        mock_ch.basic_nack.assert_not_called()

    def test_driver_callback_nack_missing_zone(self):
        """Test that a message missing 'zone' is NACKed with requeue=False."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 43

        body = json.dumps({
            "id": "REQ-0010",
            "city": "bangalore",
            "type": "food",
            "ts": 1234567890.0,
            "malformed": True
        }).encode("utf-8")

        driver.process_message("Meena", mock_ch, mock_method, body)

        mock_ch.basic_nack.assert_called_once_with(delivery_tag=43, requeue=False)
        mock_ch.basic_ack.assert_not_called()

    def test_driver_callback_nack_bad_json(self):
        """Test that unparseable JSON is NACKed with requeue=False."""
        mock_ch = MagicMock()
        mock_method = MagicMock()
        mock_method.delivery_tag = 44

        body = b"this is not json"

        driver.process_message("Arjun", mock_ch, mock_method, body)

        mock_ch.basic_nack.assert_called_once_with(delivery_tag=44, requeue=False)
        mock_ch.basic_ack.assert_not_called()


if __name__ == '__main__':
    unittest.main()
