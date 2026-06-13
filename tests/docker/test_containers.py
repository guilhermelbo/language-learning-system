"""
Docker container fixtures for test infrastructure.

This module provides pytest fixtures for managing Docker containers
during test execution using testcontainers-python.
"""

import pytest
from typing import Generator, Dict, Any
import subprocess
import time


@pytest.fixture
def docker_compose_up():
    """
    Fixture to start Docker Compose services for testing.
    
    Starts all services defined in docker-compose.test.yml
    and yields control when services are healthy.
    """
    # Start Docker Compose
    subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd="/home/guilherme/projects/language-learning-system",
        check=True
    )
    
    # Wait for services to be healthy
    time.sleep(10)
    
    yield
    
    # Stop Docker Compose
    subprocess.run(
        ["docker-compose", "down"],
        cwd="/home/guilherme/projects/language-learning-system",
        check=True
    )


@pytest.fixture
def docker_compose_down():
    """
    Fixture to stop Docker Compose services after test.
    
    Cleanup fixture to ensure containers are stopped after tests.
    """
    yield
    
    # Stop Docker Compose on cleanup
    subprocess.run(
        ["docker-compose", "down"],
        cwd="/home/guilherme/projects/language-learning-system",
        check=False
    )


def get_container_health(container_name: str) -> bool:
    """
    Check if a Docker container is healthy.
    
    Args:
        container_name: Name of the container
        
    Returns:
        True if container is healthy, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Health.Status}}", container_name],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() == "healthy"
    except subprocess.CalledProcessError:
        return False


def wait_for_service(
    url: str,
    timeout: int = 30,
    interval: int = 2
) -> bool:
    """
    Wait for a service to be available.
    
    Args:
        url: Service URL to check
        timeout: Maximum wait time in seconds
        interval: Check interval in seconds
        
    Returns:
        True if service becomes available, False on timeout
    """
    import urllib.request
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(interval)
    
    return False


class TestContainerManager:
    """
    Manager for test Docker containers.
    
    Provides utilities for starting, stopping, and monitoring
    Docker containers used in tests.
    """
    
    def __init__(self, compose_file: str = "docker-compose.test.yml"):
        """
        Initialize the container manager.
        
        Args:
            compose_file: Path to docker-compose file
        """
        self.compose_file = compose_file
        self.working_dir = "/home/guilherme/projects/language-learning-system"
    
    def start(self) -> bool:
        """
        Start all services in docker-compose file.
        
        Returns:
            True if services started successfully, False otherwise
        """
        try:
            subprocess.run(
                ["docker-compose", "-f", self.compose_file, "up", "-d"],
                cwd=self.working_dir,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to start containers: {e}")
            return False
    
    def stop(self) -> bool:
        """
        Stop all services in docker-compose file.
        
        Returns:
            True if services stopped successfully, False otherwise
        """
        try:
            subprocess.run(
                ["docker-compose", "-f", self.compose_file, "down"],
                cwd=self.working_dir,
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to stop containers: {e}")
            return False
    
    def status(self) -> Dict[str, str]:
        """
        Get status of all services.
        
        Returns:
            Dictionary mapping service names to their status
        """
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.compose_file, "ps", "--format", 
                 "{{.Service}}:{{.Status}}"],
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            status = {}
            for line in result.stdout.strip().split('\n'):
                if ':' in line:
                    name, status_line = line.split(':', 1)
                    status[name.strip()] = status_line.strip()
            
            return status
        except subprocess.CalledProcessError:
            return {}


# Example usage as pytest fixture
@pytest.fixture
def test_controllers():
    """Fixture providing TestContainerManager instance."""
    manager = TestContainerManager()
    yield manager
    manager.stop()
