import sys
sys.path.append("/opt")


from confluent_kafka import SerializingProducer, KafkaError, KafkaException
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer
import requests
import json
import time

# Kafka brocker
KAFKA_BROCKER = "kafka0:9093"
# kafka-topics --bootstrap-server kafka0:9093 --create --topic Current-raw --partitions 1 --replication-factor 1 --config retention.ms=300000
TOPIC1 = 'Current-raw'
# kafka-topics --bootstrap-server kafka0:9093 --create --topic Current-air-raw --partitions 1 --replication-factor 1 --config retention.ms=300000
TOPIC2 = 'Current-air-raw'

# Schema Registry
SCHEMA_REGISTRY = "http://schema-registry:8081"
schema_registry_conf = {'url': SCHEMA_REGISTRY}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# serializer object for topic 1
CW_SCHEMA_PATH = '/opt/Kafka/schema/current_weather_raw.avsc'
with open(CW_SCHEMA_PATH, 'r') as f:
    schema_current_weather_raw = f.read()
avro_serializer_CR = AvroSerializer(schema_registry_client, schema_current_weather_raw)   # current weather

# serializer object for topic 2
AP_SCHEMA_PATH = '/opt/Kafka/schema/air_pollution_raw.avsc'
with open(AP_SCHEMA_PATH, 'r') as f:
    schema_air_pollution_raw = f.read()
avro_serializer_AP = AvroSerializer(schema_registry_client, schema_air_pollution_raw)    # air pollution


# Load coordinate
with open('/opt/Kafka/coord/coordinate.json', 'r') as f:
    coord_list = json.load(f)

# filter for current weather
def filter_fields(data):
    """
    Filter fields from the response of current weather OpenWeatherMap API
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
        "visibility": data.get("visibility", 0),
        "wind": {
            "speed": data["wind"].get("speed", 0.0),
            "deg": data["wind"].get("deg", 0),
            "gust": data["wind"].get("gust", 0.0)
        },
        "dt": data["dt"]
    }

    
    return filtered_current_weather

# callback function
def callback(err, msg):
    """
    Callback function
    """
    if err is not None:
        print(f"Failed to deliver message: {str(err)}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")


# Producer weather and pollution
def Producer_current_weather():
    """
    Producer function for current weather
    """
    producer_conf = {
        'bootstrap.servers': KAFKA_BROCKER,
        'key.serializer': StringSerializer('utf_8'),
        'value.serializer': avro_serializer_CR
        # 'message.timestamp.type': 'LogAppendTime'
    }
    producer = SerializingProducer(producer_conf)

    # while True:
    for coord in coord_list:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/weather?lat={coord['lat']}&lon={coord['lon']}&appid=72dc1092f8152fcd1935938246615de4&units=metric")
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            continue
        data["coord"]['city'] = coord['city']
        data["coord"]['district'] = coord['district']
        filtered_current_weather = filter_fields(data)
        producer.produce(TOPIC1, key=f"cr_{data['dt']}", value=filtered_current_weather, on_delivery=callback)
        time.sleep(1)
    print("Flushing producer...")
    producer.flush()


def Producer_air_pollution():
    """
    Producer function for air pollution
    """
    producer_conf = {
        'bootstrap.servers': KAFKA_BROCKER,
        'key.serializer': StringSerializer('utf_8'),
        'value.serializer': avro_serializer_AP
    }
    producer = SerializingProducer(producer_conf)
    while True:
        for coord in coord_list:
            response = requests.get(f"http://api.openweathermap.org/data/2.5/air_pollution?lat={coord['lat']}&lon={coord['lon']}&appid=ac2644f6a06e2b3b1651f4c8a53206c5")
            if response.status_code == 200:
                data = response.json()
            else:
                print(f"Error fetching data: {response.status_code}, {response.text}")
                continue
            data["coord"]['city'] = coord['city']
            data["coord"]['district'] = coord['district']
            producer.produce(TOPIC2, key=f"ap_{data['list'][0]['dt']}", value=data, on_delivery=callback)
            time.sleep(1)



Producer_current_weather()