"""
Idea Inc - Event Bus

Event bus abstraction supporting:
- In-memory mock for MVP/development
- Kafka for production

Provides publish/subscribe functionality for events.
"""

import asyncio
import json
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.utils.logging import get_logger

logger = get_logger(__name__)


class Event:
    """Base event class"""
    
    def __init__(
        self,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ):
        self.event_id = event_id or str(uuid4())
        self.event_type = event_type
        self.payload = payload
        self.timestamp = datetime.utcnow().isoformat()
        self.correlation_id = correlation_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            event_type=data["event_type"],
            payload=data["payload"],
            event_id=data.get("event_id"),
            correlation_id=data.get("correlation_id"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        return cls.from_dict(json.loads(json_str))


# Type alias for event handlers
EventHandler = Callable[[Event], None]
AsyncEventHandler = Callable[[Event], Any]


class EventBus(ABC):
    """Abstract event bus interface"""
    
    @abstractmethod
    async def publish(self, topic: str, event: Event) -> None:
        """Publish an event to a topic"""
        pass
    
    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        handler: AsyncEventHandler,
        group: Optional[str] = None,
    ) -> None:
        """Subscribe to a topic with a handler"""
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str, handler: AsyncEventHandler) -> None:
        """Unsubscribe a handler from a topic"""
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the event bus"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus"""
        pass


class InMemoryEventBus(EventBus):
    """
    In-memory event bus for development and testing.
    
    Provides basic pub/sub functionality without external dependencies.
    Events are processed asynchronously but not persisted.
    """
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[AsyncEventHandler]] = {}
        self._history: Dict[str, List[Event]] = {}
        self._max_history = max_history
        self._running = False
        self._lock = asyncio.Lock()
    
    async def publish(self, topic: str, event: Event) -> None:
        """Publish an event to a topic"""
        async with self._lock:
            # Store in history
            if topic not in self._history:
                self._history[topic] = []
            self._history[topic].append(event)
            
            # Trim history
            if len(self._history[topic]) > self._max_history:
                self._history[topic] = self._history[topic][-self._max_history:]
            
            # Get subscribers
            handlers = self._subscribers.get(topic, [])
        
        # Notify subscribers (outside lock)
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    "Event handler error",
                    topic=topic,
                    event_type=event.event_type,
                    error=str(e),
                )
        
        logger.debug(
            "Event published",
            topic=topic,
            event_type=event.event_type,
            handlers=len(handlers),
        )
    
    async def subscribe(
        self,
        topic: str,
        handler: AsyncEventHandler,
        group: Optional[str] = None,
    ) -> None:
        """Subscribe to a topic"""
        async with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            
            if handler not in self._subscribers[topic]:
                self._subscribers[topic].append(handler)
                logger.info("Subscribed to topic", topic=topic)
    
    async def unsubscribe(self, topic: str, handler: AsyncEventHandler) -> None:
        """Unsubscribe from a topic"""
        async with self._lock:
            if topic in self._subscribers:
                if handler in self._subscribers[topic]:
                    self._subscribers[topic].remove(handler)
                    logger.info("Unsubscribed from topic", topic=topic)
    
    async def start(self) -> None:
        """Start the event bus"""
        self._running = True
        logger.info("In-memory event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus"""
        self._running = False
        logger.info("In-memory event bus stopped")
    
    def get_history(self, topic: str, limit: int = 100) -> List[Event]:
        """Get event history for a topic"""
        events = self._history.get(topic, [])
        return events[-limit:]
    
    def get_topics(self) -> List[str]:
        """Get all topics with subscribers or history"""
        topics = set(self._subscribers.keys()) | set(self._history.keys())
        return list(topics)


class KafkaEventBus(EventBus):
    """
    Kafka-based event bus for production.
    
    Requires aiokafka package and running Kafka cluster.
    """
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        consumer_group: str = "ideainc",
    ):
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self._producer = None
        self._consumers: Dict[str, Any] = {}
        self._running = False
        self._consumer_tasks: Dict[str, asyncio.Task] = {}
    
    async def start(self) -> None:
        """Start the Kafka producer"""
        try:
            from aiokafka import AIOKafkaProducer
            
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: v.encode('utf-8'),
            )
            await self._producer.start()
            self._running = True
            logger.info("Kafka event bus started", servers=self.bootstrap_servers)
            
        except ImportError:
            logger.error("aiokafka not installed, Kafka event bus unavailable")
            raise
        except Exception as e:
            logger.error("Failed to start Kafka producer", error=str(e))
            raise
    
    async def stop(self) -> None:
        """Stop Kafka connections"""
        self._running = False
        
        # Stop consumers
        for topic, task in self._consumer_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        for consumer in self._consumers.values():
            await consumer.stop()
        
        # Stop producer
        if self._producer:
            await self._producer.stop()
        
        logger.info("Kafka event bus stopped")
    
    async def publish(self, topic: str, event: Event) -> None:
        """Publish event to Kafka topic"""
        if not self._producer:
            raise RuntimeError("Kafka producer not started")
        
        try:
            await self._producer.send_and_wait(topic, event.to_json())
            logger.debug("Event published to Kafka", topic=topic, event_type=event.event_type)
        except Exception as e:
            logger.error("Failed to publish event to Kafka", error=str(e))
            raise
    
    async def subscribe(
        self,
        topic: str,
        handler: AsyncEventHandler,
        group: Optional[str] = None,
    ) -> None:
        """Subscribe to Kafka topic"""
        try:
            from aiokafka import AIOKafkaConsumer
            
            consumer_group = group or self.consumer_group
            
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=consumer_group,
                value_deserializer=lambda v: v.decode('utf-8'),
            )
            await consumer.start()
            
            self._consumers[topic] = consumer
            
            # Start consumer task
            task = asyncio.create_task(
                self._consume_loop(topic, consumer, handler)
            )
            self._consumer_tasks[topic] = task
            
            logger.info("Subscribed to Kafka topic", topic=topic, group=consumer_group)
            
        except ImportError:
            logger.error("aiokafka not installed")
            raise
    
    async def _consume_loop(
        self,
        topic: str,
        consumer: Any,
        handler: AsyncEventHandler,
    ) -> None:
        """Consumer loop for processing messages"""
        try:
            async for message in consumer:
                try:
                    event = Event.from_json(message.value)
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(
                        "Error processing Kafka message",
                        topic=topic,
                        error=str(e),
                    )
        except asyncio.CancelledError:
            logger.info("Consumer loop cancelled", topic=topic)
    
    async def unsubscribe(self, topic: str, handler: AsyncEventHandler) -> None:
        """Unsubscribe from Kafka topic"""
        if topic in self._consumer_tasks:
            self._consumer_tasks[topic].cancel()
            try:
                await self._consumer_tasks[topic]
            except asyncio.CancelledError:
                pass
            del self._consumer_tasks[topic]
        
        if topic in self._consumers:
            await self._consumers[topic].stop()
            del self._consumers[topic]
        
        logger.info("Unsubscribed from Kafka topic", topic=topic)


def create_event_bus(
    use_kafka: bool = False,
    kafka_servers: str = "localhost:9092",
    consumer_group: str = "ideainc",
) -> EventBus:
    """
    Factory function to create appropriate event bus.
    
    Args:
        use_kafka: Whether to use Kafka (requires aiokafka)
        kafka_servers: Kafka bootstrap servers
        consumer_group: Kafka consumer group
    
    Returns:
        EventBus instance
    """
    if use_kafka:
        return KafkaEventBus(
            bootstrap_servers=kafka_servers,
            consumer_group=consumer_group,
        )
    else:
        return InMemoryEventBus()


# =============================================================================
# Predefined Event Types
# =============================================================================

class EventTypes:
    """Standard event type constants"""
    
    # Idea events
    IDEA_INJECTED = "idea.injected"
    IDEA_SPREAD = "idea.spread"
    IDEA_MUTATED = "idea.mutated"
    IDEA_DECAYED = "idea.decayed"
    
    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_ADOPTED = "agent.adopted"
    AGENT_REJECTED = "agent.rejected"
    
    # World events
    WORLD_CREATED = "world.created"
    WORLD_STARTED = "world.started"
    WORLD_PAUSED = "world.paused"
    WORLD_COMPLETED = "world.completed"
    SNAPSHOT_READY = "snapshot.ready"
    
    # User events
    USER_CREATED = "user.created"
    USER_LOGGED_IN = "user.logged_in"
    USER_LOGGED_OUT = "user.logged_out"


class Topics:
    """Standard topic constants"""
    
    IDEA_EVENTS = "idea-events"
    AGENT_EVENTS = "agent-events"
    WORLD_EVENTS = "world-events"
    USER_EVENTS = "user-events"
    ANALYTICS_EVENTS = "analytics-events"

