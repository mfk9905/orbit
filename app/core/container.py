"""
Dependency Injection Container for Orbit application.
Provides explicit service registration, lifecycle management, and resolution.
"""

from typing import Dict, Any, Type, TypeVar, Callable

T = TypeVar("T")


class ServiceContainer:
    """Simple thread-safe Dependency Injection container."""

    _instance = None

    def __init__(self) -> None:
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}

    @classmethod
    def get_instance(cls) -> "ServiceContainer":
        """Get or create singleton container instance."""
        if cls._instance is None:
            cls._instance = ServiceContainer()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (primarily for testing)."""
        cls._instance = None

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """Register an existing object instance as a singleton service."""
        self._services[service_type] = instance

    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """Register a factory function for transient resolution."""
        self._factories[service_type] = factory

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service by type."""
        if service_type in self._services:
            return self._services[service_type]

        if service_type in self._factories:
            return self._factories[service_type]()

        raise KeyError(f"Service of type {service_type.__name__} is not registered in container.")

    def has(self, service_type: Type) -> bool:
        """Check if a service type is registered."""
        return service_type in self._services or service_type in self._factories
