import unittest
import os
import time
import subprocess
from devbox_manager import DevBoxManager

class TestDevBoxManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a dummy file in the current directory to test read-only mount
        with open("dummy_test_file.txt", "w") as f:
            f.write("test_content")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists("dummy_test_file.txt"):
            os.remove("dummy_test_file.txt")

    def setUp(self):
        self.manager = DevBoxManager(codebase_path=os.getcwd())
        # Time the startup
        start = time.time()
        self.manager.start()
        self.startup_time = time.time() - start

    def tearDown(self):
        self.manager.stop()

    def test_startup_time(self):
        self.assertLess(self.startup_time, 10.0, "Container took longer than 10 seconds to start")

    def test_network_isolation(self):
        # Try to ping an external address like google.com or 8.8.8.8
        # Should fail since there's no network access
        with self.assertRaises(RuntimeError) as context:
            self.manager.execute_command("ping -c 1 8.8.8.8")
        self.assertIn("failed", str(context.exception).lower())

        # Another test for network
        with self.assertRaises(RuntimeError):
            self.manager.execute_command("wget -qO- https://google.com")

    def test_readonly_mount(self):
        # We mounted the current directory to /code
        # Check if dummy_test_file.txt exists
        output = self.manager.execute_command("cat /code/dummy_test_file.txt")
        self.assertEqual(output.strip(), "test_content")

        # Try to modify the file, should fail
        with self.assertRaises(RuntimeError):
            self.manager.execute_command("echo 'modified' > /code/dummy_test_file.txt")

        # Try to create a file in /code
        with self.assertRaises(RuntimeError):
            self.manager.execute_command("touch /code/new_file.txt")

    def test_execute_command(self):
        output = self.manager.execute_command("echo 'hello world'")
        self.assertEqual(output.strip(), "hello world")

if __name__ == '__main__':
    unittest.main()
