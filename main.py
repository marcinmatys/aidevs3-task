import argparse
from importlib import import_module
from common.logger_config import setup_logger

logger = setup_logger('Main')

def main(task_name: str):

    try:
        # Dynamically import the task module
        task_module = import_module(f"tasks.{task_name}")

        # Dynamically get the task class from the module
        task_class = getattr(task_module, task_name)

        # Instantiate and solve the task
        task = task_class()
        task.run()

    except (ModuleNotFoundError, AttributeError) as e:
        logger.error(f"Error: {e}")
        logger.error(f"Task {task_name} not found.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a specific task.')
    parser.add_argument('--task', type=str, help='The name of the task class to run')
    args = parser.parse_args()

    main(args.task)
