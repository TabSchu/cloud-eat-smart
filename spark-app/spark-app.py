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

# Create a spark session
spark = SparkSession.builder \
    .appName("Structured Streaming").getOrCreate()

# Set log level
spark.sparkContext.setLogLevel('WARN')

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
trackingStudentSchema = StructType() \
    .add("gpa", DoubleType()) \
    .add("fav_cuisine", StringType()) \
    .add("fav_lunch", StringType()) \
    .add("fav_breakfast", StringType()) \
    .add("timestamp", IntegerType())

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



# Compute most favorite cuisine 
smart_cuisine = trackingStudentMessages.groupBy(
        column("fav_cuisine")

).agg(avg('gpa').alias('avg_gpa'), count("fav_cuisine").alias('amount_of_entries'))

# Compute most favorite lunch 
smart_lunch = trackingStudentMessages.groupBy(
        column("fav_lunch")

).agg(avg('gpa').alias('avg_gpa'), count("fav_lunch").alias('amount_of_entries'))

# Compute most favorite breakfast
smart_breakfast = trackingStudentMessages.groupBy(
        column("fav_breakfast")

).agg(avg('gpa').alias('avg_gpa'), count("fav_breakfast").alias('amount_of_entries'))

# Start running the cuisine query; print running counts to the console
consoleCuisineDumb = smart_cuisine \
    .writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# Start running the lunch query; print running counts to the console
consoleLunchDumb = smart_lunch \
    .writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

# Start running the breakfast query; print running counts to the console
consoleBreakfastDumb = smart_breakfast \
    .writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .format("console") \
    .option("truncate", "false") \
    .start()

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
                #since there are 3 different tables hasattr(column_name) is a way to determine to which table the value should be written to
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

# Start Cuisine Batch Processing
dbCuisineInsertStream = smart_cuisine.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveDataframeToDatabase) \
    .start()

# Start Lunch Batch Processing
dbLunchInsertStream = smart_lunch.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveDataframeToDatabase) \
    .start()

# Start Breakfast Batch Processing
dbBreakfastInsertStream = smart_breakfast.writeStream \
    .trigger(processingTime=slidingDuration) \
    .outputMode("update") \
    .foreachBatch(saveDataframeToDatabase) \
    .start()


# Wait for termination
spark.streams.awaitAnyTermination()
