import unittest
from unittest.mock import patch, mock_open, MagicMock
import os
from main import DependencyGraphVisualizer


class TestDependencyGraphVisualizer(unittest.TestCase):

    @patch("builtins.open", new_callable=mock_open, read_data="""
    visualizer_path = "/path/to/plantuml"
    package_name = "curl"
    result_path = "./output.puml"
    max_depth = 3
    repository_url = "http://archive.ubuntu.com/ubuntu"
    """)
    def test_load_config(self, mock_file):
        visualizer = DependencyGraphVisualizer("config.toml")
        self.assertEqual(visualizer.config["visualizer_path"], "/path/to/plantuml")
        self.assertEqual(visualizer.config["package_name"], "curl")

    def test_validate_config_success(self):
        config = {
            "visualizer_path": "/path/to/plantuml",
            "package_name": "curl",
            "result_path": "./output.puml",
            "max_depth": 3,
            "repository_url": "http://archive.ubuntu.com/ubuntu"
        }
        visualizer = DependencyGraphVisualizer.__new__(DependencyGraphVisualizer)
        visualizer.config = config

        with patch("os.path.exists", return_value=True):
            visualizer.validate_config()

    def test_validate_config_missing_key(self):
        config = {
            "visualizer_path": "/path/to/plantuml"
            # Missing keys
        }
        visualizer = DependencyGraphVisualizer.__new__(DependencyGraphVisualizer)
        visualizer.config = config

        with self.assertRaises(KeyError):
            visualizer.validate_config()

    @patch("subprocess.run")
    def test_fetch_dependencies(self, mock_subprocess):
        mock_subprocess.return_value.stdout = """
        curl
        Depends: libcurl4
        Depends: openssl
        """

        visualizer = DependencyGraphVisualizer.__new__(DependencyGraphVisualizer)
        visualizer.graph = []

        visualizer.fetch_dependencies("curl", 0, 3)

        self.assertIn(("curl", "libcurl4"), visualizer.graph)
        self.assertIn(("curl", "openssl"), visualizer.graph)

    def test_generate_plantuml_code(self):
        visualizer = DependencyGraphVisualizer.__new__(DependencyGraphVisualizer)
        visualizer.graph = [("curl", "libcurl4"), ("curl", "openssl")]

        result = visualizer.generate_plantuml_code()

        self.assertIn("@startuml", result)
        self.assertIn("@enduml", result)

    @patch("builtins.open", new_callable=mock_open)
    def test_save_to_file(self, mock_file):
        visualizer = DependencyGraphVisualizer.__new__(DependencyGraphVisualizer)
        visualizer.config = {"result_path": "./output.puml"}

        visualizer.save_to_file("test content")

        mock_file.assert_called_once_with("./output.puml", "w")
        mock_file().write.assert_called_once_with("test content")


if __name__ == "__main__":
    unittest.main()
