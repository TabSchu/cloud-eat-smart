from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from builtins import round as rounding
from pyspark.sql.types import IntegerType, StringType, StructType, TimestampType, DoubleType
import mysqlx
import math

dbOptions = {"host": "my-app-mysql-service", 'port': 33060, "user": "root", "password": "mysecretpw"}
dbSchema = 'popular'
windowDuration = '5 minutes'
slidingDuration = '5 minutes'

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
    .add("fav_lunch", StringType()) \
    .add("fav_breakfast", StringType()) \
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
    .withColumnRenamed('json.fav_lunch', 'fav_lunch') \
    .withColumnRenamed('json.fav_breakfast', 'fav_breakfast') \
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
        column("fav_cuisine")

).agg(avg('gpa').alias('avg_gpa'), count("fav_cuisine").alias('amount_of_entries'))

smart_lunch = trackingStudentMessages.groupBy(
        column("fav_lunch")

).agg(avg('gpa').alias('avg_gpa'), count("fav_lunch").alias('amount_of_entries'))

smart_breakfast = trackingStudentMessages.groupBy(
        column("fav_breakfast")

).agg(avg('gpa').alias('avg_gpa'), count("fav_breakfast").alias('amount_of_entries'))



# smart_cuisine = trackingStudentMessages.groupBy(
#     window(
#         column("parsed_timestamp"),
#         windowDuration,
#         slidingDuration
#     ),
#     column("fav_cuisine")

# ).agg(avg('gpa').alias('avg_gpa'), count("fav_cuisine").alias('amount_of_entries'))

#new_avg_gpa = smart_cuisine.avg('gpa').avg('gpa').withColumnRenamed('avg(gpa)', 'avg_gpa')
#new_count = smart_cuisine.count()

#.avg('gpa').withColumnRenamed('avg(gpa)', 'avg_gpa')
#).agg(avg('gpa').alias('avg_gpa'), count("fav_cuisine").alias('amount_of_entries'))


#

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
consoleCuisineDumb = smart_cuisine \
    .writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

consoleLunchDumb = smart_lunch \
    .writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

consoleBreakfastDumb = smart_breakfast \
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
def saveDataframeToDatabase(batchDataframe, batchId):
    # Define function to save a dataframe to mysql
    
    def save_to_db(iterator):
        # Connect to database and use schema
        session = mysqlx.get_session(dbOptions)
        session.sql("USE popular").execute()
              
        for row in iterator:
            # Run upsert (insert or update existing)        

            if row.avg_gpa is not None:
                avg_gpa = str(rounding(row.avg_gpa, 2))   
   
                if hasattr(row, 'fav_cuisine'):
                    sql = session.sql("INSERT INTO smart_cuisine (cuisine, avg_gpa, count) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE avg_gpa = ?, count = ?")              
                    sql.bind(row.fav_cuisine, avg_gpa, row.amount_of_entries, avg_gpa, row.amount_of_entries).execute()
                elif hasattr(row, 'fav_lunch'):
                    sql = session.sql("INSERT INTO smart_lunch (lunch, avg_gpa, count) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE avg_gpa = ?, count = ?")
                    sql.bind(row.fav_lunch, avg_gpa, row.amount_of_entries, avg_gpa, row.amount_of_entries).execute()
                elif hasattr(row, 'fav_breakfast'):
                    sql = session.sql("INSERT INTO smart_breakfast (breakfast, avg_gpa, count) VALUES (?, ?, ?) ON DUPLICATE KEY UPDATE avg_gpa = ?, count = ?")
                    sql.bind(row.fav_breakfast, avg_gpa, row.amount_of_entries, avg_gpa, row.amount_of_entries).execute()                
                
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

dbCuisineInsertStream = smart_cuisine.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveDataframeToDatabase) \
    .start()

dbLunchInsertStream = smart_lunch.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveDataframeToDatabase) \
    .start()

dbBreakfastInsertStream = smart_breakfast.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveDataframeToDatabase) \
    .start()


# Wait for termination
spark.streams.awaitAnyTermination()
