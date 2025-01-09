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
# mã bash tạo topic
TOPIC1 = 'Forecast-raw'
TOPIC2 = 'Forecast-air-raw'

# Schema Registry 
SCHEMA_REGISTRY = "http://schema-registry:8081"
schema_registry_conf = {'url': SCHEMA_REGISTRY}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

# serializer object
WF_SCHEMA_PATH = 'schema/weather_forecast_raw.avsc'
with open(WF_SCHEMA_PATH, 'r') as f:
    schema_weather_forecast_raw = f.read()
avro_serializer_WF = AvroSerializer(schema_registry_client, schema_weather_forecast_raw)

APF_SCHEMA_PATH = 'schema/air_pollution_forecast_raw.avsc'
with open(WF_SCHEMA_PATH, 'r') as f:
    schema_air_polution_forecast_raw = f.read()
avro_serializer_APF = AvroSerializer(schema_registry_client, schema_air_polution_forecast_raw)

# Load coordinate
with open('/opt/Kafka/coord/coordinate.json', 'r') as f:
    coord_list = json.load(f)

# callback function
def callback(err, msg):
    """
    Callback function
    """
    if err is not None:
        print(f"Failed to deliver message: {str(err)}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def filter_fields(data):
    """
    Filter of forecast weather
    """
    filtered_data = {
        "main": {
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "pressure": data["main"]["pressure"],
            "humidity": data["main"]["humidity"]
        },
        "weather": [
            {
                "description": data["weather"][0]["description"]
            }
        ],
        "wind": {
            "speed": data["wind"]["speed"],
            "deg": data["wind"]["deg"],
            "gust": data["wind"]["gust"]
        },
        "visibility": data["visibility"],
        "dt_txt": data["dt_txt"]
    }
    return filtered_data



def Producer_forecast_weather():
    """
    Producer function for weather forecast
    """
    producer_conf = {
        'bootstrap.servers': KAFKA_BROCKER,
        'key.serializer': StringSerializer('utf_8'),
        'value.serializer': avro_serializer_WF
    }
    producer = SerializingProducer(producer_conf)

    for coord in coord_list:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/forecast?lat={coord['lat']}&lon={coord['lon']}&appid=72dc1092f8152fcd1935938246615de4&units=metric")
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            continue
        forecast_datas = data["list"]
        for forecase_data in forecast_datas:
            data_filter = filter_fields(forecase_data)
            data_filter["location"]["city"] = coord["city"]
            data_filter["location"]["district"] = coord["district"]
            producer.produce(TOPIC1, key=f"wf_{data_filter["dt_txt"]}", value=data_filter, on_delivery=callback)
        time.sleep(1)

def Producer_forecast_air_pollution():
    """
    Producer function for weather forecast
    """
    producer_conf = {
        'bootstrap.servers': KAFKA_BROCKER,
        'key.serializer': StringSerializer('utf_8'),
        'value.serializer': avro_serializer_APF
    }
    producer = SerializingProducer(producer_conf)

    for coord in coord_list:
        response = requests.get(f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={coord['lat']}&lon={coord['lon']}&appid=72dc1092f8152fcd1935938246615de4")
        if response.status_code == 200:
            data = response.json()
        else:
            print(f"Error fetching data: {response.status_code}, {response.text}")
            continue
        forecast_datas = data["list"]
        for forecast_data in forecast_datas:
            forecast_data["location"]["city"] = coord["city"]
            forecast_data["location"]["district"] = coord["district"]
            producer.produce(TOPIC2, key=f"apf_{forecast_data['dt']}", value=forecast_data, on_delivery=callback)
        time.sleep(1)
        





