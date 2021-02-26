from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from builtins import round as rounding
from pyspark.sql.types import IntegerType, StringType, StructType, TimestampType, DoubleType
import mysqlx
import math

dbOptions = {"host": "my-app-mysql-service", 'port': 33060, "user": "root", "password": "mysecretpw"}
dbSchema = 'popular'
windowDuration = '5 minutes'
slidingDuration = '1 minute'

# Example Part 1
# Create a spark session
spark = SparkSession.builder \
    .appName("Structured Streaming").getOrCreate()

# Set log level
spark.sparkContext.setLogLevel('WARN')

# Example Part 2
# Read messages from Kafka
kafkaMessages = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers",
            "my-cluster-kafka-bootstrap:9092") \
    .option("subscribe", "tracking-data") \
    .option("startingOffsets", "earliest") \
    .load()

# Define schema of tracking data
# trackingMessageSchema = StructType() \
#     .add("mission", StringType()) \
#     .add("timestamp", IntegerType())

trackingStudentSchema = StructType() \
    .add("gpa", DoubleType()) \
    .add("fav_cuisine", StringType()) \
    .add("timestamp", IntegerType())


# # Example Part 3
# # Convert value: binary -> JSON -> fields + parsed timestamp
# trackingMessages = kafkaMessages.select(
#     # Extract 'value' from Kafka message (i.e., the tracking data)
#     from_json(
#         column("value").cast("string"),
#         trackingMessageSchema
#     ).alias("json")
# ).select(
#     # Convert Unix timestamp to TimestampType
#     from_unixtime(column('json.timestamp'))
#     .cast(TimestampType())
#     .alias("parsed_timestamp"),

#     # Select all JSON fields
#     column("json.*")
# ) \
#     .withColumnRenamed('json.mission', 'mission') \
#     .withWatermark("parsed_timestamp", windowDuration)



# Example Part 3.2
# Convert value: binary -> JSON -> fields + parsed timestamp
trackingStudentMessages = kafkaMessages.select(
    # Extract 'value' from Kafka message (i.e., the tracking data)
    from_json(
        column("value").cast("string"),
        trackingStudentSchema
    ).alias("json")
).select(
     # Convert Unix timestamp to TimestampType
    from_unixtime(column('json.timestamp'))
    .cast(TimestampType())
    .alias("parsed_timestamp"),

    # Select all JSON fields
    column("json.*")
) \
    .withColumnRenamed('json.gpa', 'gpa') \
    .withColumnRenamed('json.fav_cuisine', 'fav_cuisine') \
    .withWatermark("parsed_timestamp", windowDuration)


# # Example Part 4
# # Compute most popular slides
# popular = trackingMessages.groupBy(
#     window(
#         column("parsed_timestamp"),
#         windowDuration,
#         slidingDuration
#     ),
#     column("mission")
# ).count().withColumnRenamed('count', 'views')

# Example Part 4.2
# Compute most popular slides
smart_cuisine = trackingStudentMessages.groupBy(
    window(
        column("parsed_timestamp"),
        windowDuration,
        slidingDuration
    ),
    column("fav_cuisine")
).avg('gpa').withColumnRenamed('avg(gpa)', 'avg_gpa')

# # Example Part 5
# # Start running the query; print running counts to the console
# consoleDump = popular \
#     .writeStream \
#     .trigger(processingTime=slidingDuration) \
#     .outputMode("update") \
#     .format("console") \
#     .option("truncate", "false") \
#     .start()

# Example Part 5.2
# Start running the query; print running counts to the console
consoleStudentDump = smart_cuisine \
    .writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()


# # Example Part 6
# def saveToDatabase(batchDataframe, batchId):
#     # Define function to save a dataframe to mysql
#     def save_to_db(iterator):
#         # Connect to database and use schema
#         session = mysqlx.get_session(dbOptions)
#         session.sql("USE popular").execute()

#         for row in iterator:
#             # Run upsert (insert or update existing)
#             sql = session.sql("INSERT INTO popular "
#                               "(mission, count) VALUES (?, ?) "
#                               "ON DUPLICATE KEY UPDATE count=?")
#             sql.bind(row.mission, row.views, row.views).execute()

#         session.close()

#     # Perform batch UPSERTS per data partition
#     batchDataframe.foreachPartition(save_to_db)

# Example Part 6.2
def saveStudentToDatabase(batchDataframe, batchId):
    # Define function to save a dataframe to mysql
    def save_to_db(iterator):
        # Connect to database and use schema
        session = mysqlx.get_session(dbOptions)
        session.sql("USE popular").execute()

        for row in iterator:
            # Run upsert (insert or update existing)
            print('################### avg_gpa')

            if row.avg_gpa is not None:
                avg_gpa = str(rounding(row.avg_gpa, 2))
                sql = session.sql("INSERT INTO smart_cuisine (cuisine, avg_gpa) VALUES (?, ?) ON DUPLICATE KEY UPDATE avg_gpa=?")
                sql.bind(row.fav_cuisine, avg_gpa, avg_gpa).execute()

        session.close()

    # Perform batch UPSERTS per data partition
    batchDataframe.foreachPartition(save_to_db)

# Example Part 7
# test

# dbInsertStream = popular.writeStream \
#     .trigger(processingTime=slidingDuration) \
#     .outputMode("update") \
#     .foreachBatch(saveToDatabase) \
#     .start()

# test

dbStudentInsertStream = smart_cuisine.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveStudentToDatabase) \
    .start()

# Wait for termination
spark.streams.awaitAnyTermination()
