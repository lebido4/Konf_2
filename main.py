import toml
import subprocess
import os
from urllib.parse import urlparse


class DependencyGraphVisualizer:

    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.graph = set()  # Изменяем на множество для хранения уникальных зависимостей

    # Остальные методы остаются без изменений...

    def fetch_dependencies(self, package_name, current_depth, max_depth):
        if current_depth > max_depth:
            return

        try:
            result = subprocess.run(
                ["apt-cache", "depends", package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        except FileNotFoundError:
            raise EnvironmentError("The 'apt-cache' command is required but not available on this system.")

        dependencies = []

        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Depends:"):
                dependency = line.split("Depends:")[1].strip()
                dependencies.append(dependency)
                # Добавляем в множество для уникальности
                self.graph.add((package_name, dependency))

        for dependency in dependencies:
            self.fetch_dependencies(dependency, current_depth + 1, max_depth)

    def generate_plantuml_code(self):
        uml = ["@startuml", "digraph dependencies {"]

        for source, target in self.graph:
            uml.append(f' "{source}" -> "{target}"')

        uml.append("}")
        uml.append("@enduml")

        return "\n".join(uml)

    def load_config(self, path):
        try:
            with open(path, 'r') as file:
                return toml.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {path}")
        except toml.TomlDecodeError:
            raise ValueError(f"Invalid TOML file format: {path}")

    def validate_config(self):
        required_keys = ["visualizer_path", "package_name", "result_path", "max_depth", "repository_url"]
        for key in required_keys:
            if key not in self.config:
                raise KeyError(f"Missing required configuration key: {key}")

        if not os.path.exists(self.config["visualizer_path"]):
            raise FileNotFoundError(f"Visualizer program not found: {self.config['visualizer_path']}")

        try:
            int(self.config["max_depth"])
        except ValueError:
            raise ValueError("Max depth must be an integer.")

        parsed_url = urlparse(self.config["repository_url"])
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid repository URL.")


    def save_to_file(self, content):
        # Читаем текущее содержимое файла, если он существует
        if os.path.exists(self.config["result_path"]):
            with open(self.config["result_path"], "r") as file:
                existing_content = set(file.read().splitlines())  # Используем множество для быстрого поиска
        else:
            existing_content = set()

        # Разбиваем новый контент на строки
        new_lines = content.splitlines()

        # Находим уникальные строки
        unique_lines = [line for line in new_lines if line not in existing_content]

        # Записываем только уникальные строки
        if unique_lines:
            with open(self.config["result_path"], "a") as file:  # Используем "a" для добавления
                for line in unique_lines:
                    print(line)
                    file.write(line + "\n")

    def visualize(self):
        self.validate_config()
        self.fetch_dependencies(self.config["package_name"], 0, int(self.config["max_depth"]))
        plantuml_code = self.generate_plantuml_code()
        self.save_to_file(plantuml_code)
        print("Dependency graph written to:", self.config["result_path"])

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Visualize package dependency graph.")
    parser.add_argument("config", help="Path to the configuration file.")

    args = parser.parse_args()

    visualizer = DependencyGraphVisualizer(args.config)
    visualizer.visualize()