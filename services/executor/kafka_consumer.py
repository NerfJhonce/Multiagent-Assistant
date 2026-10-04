import json
import os
from confluent_kafka import Consumer, Producer, KafkaError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

consumer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'group.id': 'executor-group',
    'auto.offset.reset': 'earliest'
}


producer_conf = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS
}

consumer = Consumer(consumer_conf)
producer = Producer(producer_conf)


def delivery_report(err, msg):
    if err is not None:
        print(f"Error delivering message: {err}")
    else:
        print(f"message posted on {msg.topic()} [{msg.partition()}]")


def start_kafka_listener():
    consumer.subscribe(['agent.execution.requested'])
    print("Executor Service listening to the topic 'agent.execution.requested'...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"Error de Kafka: {msg.error()}")
                    break


            data = json.loads(msg.value().decode('utf-8'))
            task_id = data.get('task_id')
            code = data.get('code', '')

            print(f"Running task {task_id} in sandbox...")


            execution_result = {"status": "success", "output": f"Simulated result for {task_id}"}


            response_payload = {
                "task_id": task_id,
                "result": execution_result
            }

            producer.produce(
                'agent.execution.completed',
                key=task_id,
                value=json.dumps(response_payload).encode('utf-8'),
                callback=delivery_report
            )
            producer.flush()

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()


if __name__ == "__main__":
    start_kafka_listener()