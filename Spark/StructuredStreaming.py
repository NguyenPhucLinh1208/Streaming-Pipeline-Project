from pyspark.sql import SparkSession
from pyspark.sql.avro.functions import from_avro # tuần tự hóa bằng Avro
from pyspark.sql.functions import col, from_json
import requests

# khởi tạo một SparkSession
spark = SparkSession.builder \
    .appName("StructuredStreaming") \
    .config("spark.jars", "/opt/Spark/jars/spark-sql-kafka-0-10_2.12-3.5.4.jar,/opt/Spark/jars/kafka-clients-7.8.0-ce.jar,/opt/Spark/jars/spark-avro_2.12-3.5.4.jar,/opt/Spark/jars/commons-pool2-2.12.0.jar,/opt/Spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.4.jar") \
    .master("spark://spark-master:7077") \
    .getOrCreate()

# kafka_df chứa toàn bộ dữ liệu từ topic, được biểu diễn như một dataframe (cột key, cột value, cột topic,...)
kafka_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "kafka0:9093") \
    .option("subscribe", "Current-raw") \
    .option("startingOffsets", "earliest") \
    .load()

# http://localhost:8081/subjects/Current-raw-value/versions/latest
def get_avro_schema(subject_name):
    response = requests.get(f"http://schema-registry:8081/subjects/{subject_name}/versions/latest")
    schema_str = response.json()['schema']
    return schema_str

CR_schema = get_avro_schema('Current-raw-value')

deserialized_df = kafka_df \
    .selectExpr("CAST(key AS STRING)", "value") \
    .withColumn("parsed_value", from_avro(col("value"), CR_schema, {"mode": "PERMISSIVE"}))

final_df = deserialized_df.select("key", "parsed_value.*")


query = final_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()


spark.stop()
