"""Hardware-free checks of argument validation and HID framing/failure handling."""
import importlib.machinery
import importlib.util
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader('light', str(__import__('pathlib').Path(__file__).with_name('falchion-light')))
spec = importlib.util.spec_from_loader(loader.name, loader)
light = importlib.util.module_from_spec(spec)
loader.exec_module(light)

class LightTests(unittest.TestCase):
    def test_wave_chunk_sequence(self):
        packets = light.effect_payloads('wave', bytes([51, 102, 153]), 50, 'slow')
        self.assertEqual(len(packets), 3)
        self.assertEqual(packets[0], bytes.fromhex('51 2c 04 02 ff 32 01 00 02') + bytes(6))
        self.assertEqual(packets[1], bytes.fromhex('51 2c 04 01') + bytes(11))
        self.assertEqual(packets[2], bytes.fromhex('51 2c 04 00') + bytes(11))

    def test_static_payload_unchanged(self):
        self.assertEqual(light.effect_payloads('static', bytes([51, 102, 153]), 50, 'medium'),
                         [bytes.fromhex('51 2c 00 00 80 32 00 00 02 33 66 99')])

    def test_color(self):
        self.assertEqual(light.color('#336699'), bytes([51, 102, 153]))
        for bad in ['123', 'gg0000', '00000000', '-10000']:
            with self.assertRaises(Exception):
                light.color(bad)

    def exchange(self, reply):
        payload = b'\x51\x2c\x00'
        with patch.object(light.select, 'select', side_effect=[([], [], []), ([], [9], []), ([9], [], [])]), patch.object(light.os, 'write', return_value=65) as write, patch.object(light.os, 'read', return_value=reply):
            result = light.exchange(9, payload)
            self.assertEqual(write.call_args.args[1], b'\0' + payload + bytes(61))
            self.assertEqual(write.call_count, 1)
            return result

    def test_framing_and_reply(self):
        self.assertEqual(self.exchange(b'\x51\x2c\x00' + bytes(61))[0], 0x51)

    def test_reject_negative_or_unrelated_reply(self):
        for reply in [b'', b'\x51\xff', b'\x12\x00']:
            with self.assertRaises(RuntimeError):
                self.exchange(reply)

    def test_timeout_does_not_retry_write(self):
        with patch.object(light.select, 'select', side_effect=[([], [], []), ([], [9], []), ([], [], [])]), patch.object(light.os, 'write', return_value=65) as write:
            with self.assertRaises(RuntimeError):
                light.exchange(9, b'\x12\0')
            self.assertEqual(write.call_count, 1)

    def test_key_ids(self):
        # LED ids confirmed on a wired unit: column * 8 + row.
        self.assertEqual([light.KEYS[k] for k in ['esc', 'q', 'a', 'w', 's', 'd']], [0x01, 0x0a, 0x0b, 0x12, 0x13, 0x1b])
        self.assertEqual([light.KEYS[k] for k in ['up', 'left', 'down', 'right', 'space']], [0x6c, 0x65, 0x6d, 0x75, 0x35])
        self.assertEqual(len(set(light.KEYS.values())), len(light.KEYS))

    def test_key_payloads(self):
        entries = light.key_entries(None, [('Esc', bytes.fromhex('ff0000')), ('q', bytes.fromhex('00ff00'))])
        self.assertEqual(light.key_payloads(entries),
                         [bytes.fromhex('c0 81 02 00 01 ff 00 00 0a 00 ff 00')])
        packets = light.key_payloads(light.key_entries(bytes(3), [('W', bytes.fromhex('ffffff'))]))
        self.assertEqual(sum(p[2] for p in packets), len(light.KEYS))
        self.assertTrue(all(p[2] <= 14 and len(p) == 4 + 4 * p[2] for p in packets))
        self.assertIn(bytes.fromhex('12 ff ff ff'), b''.join(packets))

    def test_key_color_rejects_unknown(self):
        self.assertEqual(light.key_color('Up=00ffff'), ('Up', bytes.fromhex('00ffff')))
        for bad in ['F1=ff0000', 'Esc', 'Esc=fff']:
            with self.assertRaises(Exception):
                light.key_color(bad)

    def test_direct_ack(self):
        payload = bytes.fromhex('c0 81 01 00 01 ff 00 00')
        with patch.object(light.select, 'select', side_effect=[([], [], []), ([], [9], []), ([9], [], [])]), patch.object(light.os, 'write', return_value=65), patch.object(light.os, 'read', return_value=b'\xc0\x82\x01\x00' + bytes(60)):
            light.exchange(9, payload, expect=b'\xc0\x82\x01\x00')

if __name__ == '__main__':
    unittest.main()
