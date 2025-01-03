import sys
sys.path.append("/opt")


from confluent_kafka import SerializingProducer, KafkaError, KafkaException
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import requests
import json
import time

# Kafka
KAFKA_BROCKER = "kafka0:9093"
TOPIC = 'Current-Weather-raw'
# Schema Registry
SCHEMA_REGISTRY = "http://schema-registry:8081"
schema_registry_conf = {'url': SCHEMA_REGISTRY}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

SCHEMA_PATH = 'schema/current_weather_raw.avsc'
with open(SCHEMA_PATH, 'r') as f:
    schema_current_weather_raw = f.read()

avro_serializer = AvroSerializer(schema_registry_client, schema_current_weather_raw)
# Load coordinate
with open('/opt/Kafka/coord/coordinate.json', 'r') as f:
    coord_list = json.load(f)


def filter_fields(data):
    """
    Filter fields from the response of OpenWeatherMap API
    """
    filtered_current_weather = {
        "coord": data["coord"],
        "weather": [{"description": item["description"]} for item in data["weather"]],
        "main": {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "pressure": data["main"]["pressure"],
            "humidity": data["main"]["humidity"]
        },
        "visibility": data["visibility"],
        "wind": {
            "speed": data["wind"]["speed"],
            "deg": data["wind"]["deg"],
            "gust": data["wind"]["gust"]
        },
        "dt": data["dt"],
        "district": data["district"],
        "city": data["city"]
    }
    
    return filtered_current_weather

def callback(err, msg):
    """
    Callback function
    """
    if err is not None:
        print(f"Failed to deliver message: {str(err)}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def Producer():
    """
    Producer function
    """
    for coord in coord_list:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?lat={coord['lat']}&lon={coord['lon']}&appid=72dc1092f8152fcd1935938246615de4")
        data = response.json()
        data['city'] = coord['city']
        data['district'] = coord['distirct']
        filtered_current_weather = filter_fields(data)

        producer_conf = {
            'bootstrap.servers': KAFKA_BROCKER,
            'key.serializer': StringSerializer('utf_8'),
            'value.serializer': avro_serializer
        }
        producer = SerializingProducer(producer_conf)
        producer.produce(TOPIC, key=coord['dt'], value=filtered_current_weather, on_delivery=callback)
        time.sleep(1)

### viết tiếp về pollution cho vào mỗi partition trong cùng topic
