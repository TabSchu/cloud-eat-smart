const os = require('os')
const dns = require('dns').promises
const { program: optionparser } = require('commander')
const { Kafka } = require('kafkajs')
const mysqlx = require('@mysql/xdevapi');
const MemcachePlus = require('memcache-plus');
const express = require('express')
const path = require('path')

const app = express()
app.engine('html', require('ejs').renderFile);
app.set('view engine', 'html');


const cacheTimeSecs = 15;

const {generateDataset} = require('./data');

// -------------------------------------------------------
// Command-line options
// -------------------------------------------------------

let options = optionparser
	.storeOptionsAsProperties(true)
	// Web server
	.option('--port <port>', "Web server port", 3000)
	// Kafka options
	.option('--kafka-broker <host:port>', "Kafka bootstrap host:port", "my-cluster-kafka-bootstrap:9092")
	.option('--kafka-topic-tracking <topic>', "Kafka topic to tracking data send to", "tracking-data")
	.option('--kafka-client-id < id > ', "Kafka client ID", "tracker-" + Math.floor(Math.random() * 100000))
	// Memcached options
	.option('--memcached-hostname <hostname>', 'Memcached hostname (may resolve to multiple IPs)', 'my-memcached-service')
	.option('--memcached-port <port>', 'Memcached port', 11211)
	.option('--memcached-update-interval <ms>', 'Interval to query DNS for memcached IPs', 5000)
	// Database options
	.option('--mysql-host <host>', 'MySQL host', 'my-app-mysql-service')
	.option('--mysql-port <port>', 'MySQL port', 33060)
	.option('--mysql-schema <db>', 'MySQL Schema/database', 'popular')
	.option('--mysql-username <username>', 'MySQL username', 'root')
	.option('--mysql-password <password>', 'MySQL password', 'mysecretpw')
	// Misc
	.addHelpCommand()
	.parse()
	.opts()

// -------------------------------------------------------
// Database Configuration
// -------------------------------------------------------

const dbConfig = {
	host: options.mysqlHost,
	port: options.mysqlPort,
	user: options.mysqlUsername,
	password: options.mysqlPassword,
	schema: options.mysqlSchema
};

async function executeQuery(query, data) {
	let session = await mysqlx.getSession(dbConfig);
	return await session.sql(query, data).bind(data).execute()
}

// -------------------------------------------------------
// Memcache Configuration
// -------------------------------------------------------

//Connect to the memcached instances
let memcached = null
let memcachedServers = []

async function getMemcachedServersFromDns() {
	try {
		// Query all IP addresses for this hostname
		let queryResult = await dns.lookup(options.memcachedHostname, { all: true })

		// Create IP:Port mappings
		let servers = queryResult.map(el => el.address + ":" + options.memcachedPort)

		// Check if the list of servers has changed
		// and only create a new object if the server list has changed
		if (memcachedServers.sort().toString() !== servers.sort().toString()) {
			console.log("Updated memcached server list to ", servers)
			memcachedServers = servers

			//Disconnect an existing client
			if (memcached)
				await memcached.disconnect()

			memcached = new MemcachePlus(memcachedServers);
		}
	} catch (e) {
		console.log("Unable to get memcache servers", e)
	}
}

//Initially try to connect to the memcached servers, then each 5s update the list
getMemcachedServersFromDns()
setInterval(() => getMemcachedServersFromDns(), options.memcachedUpdateInterval)

//Get data from cache if a cache exists yet
async function getFromCache(key) {
	if (!memcached) {
		console.log(`No memcached instance available, memcachedServers = ${memcachedServers}`)
		return null;
	}
	return await memcached.get(key);
}

// -------------------------------------------------------
// Kafka Configuration
// -------------------------------------------------------

// Kafka connection
const kafka = new Kafka({
	clientId: options.kafkaClientId,
	brokers: [options.kafkaBroker],
	retry: {
		retries: 0
	}
})

const producer = kafka.producer()
// End

// Send tracking message to Kafka
// async function sendTrackingMessage(data) {
// 	//Ensure the producer is connected
// 	await producer.connect()

// 	//Send message
// 	await producer.send({
// 		topic: options.kafkaTopicTracking,
// 		messages: [
// 			{ value: JSON.stringify(data) }
// 		]
// 	})
// }
// // End

// Send tracking message to Kafka
//TODO :RENAME FUNCTION
async function sendStudentMessage(data) {
	//Ensure the producer is connected
	await producer.connect()

	//Send message
	await producer.send({
		topic: options.kafkaTopicTracking,
		messages: [
			{ value: JSON.stringify(data) }
		]
	})
}
// End


// -------------------------------------------------------
// Start page
// -------------------------------------------------------

// Get list of food (from cache or db)
async function getFoods() {
	const key = 'food'
	let cachedata = await getFromCache(key)

	if (cachedata) {
		console.log(`Cache hit for key=${key}, cachedata = ${cachedata}`)
		return { result: cachedata, cached: true }
	} else {
		console.log(`Cache miss for key=${key}, querying database`)
		let executeResult = await executeQuery("SELECT id, name FROM food", [])
		let data = executeResult.fetchAll()
		if (data) {
			let result = data.map(row => ({id: row[0], name: row[1]}));
			
			console.log(`Got result=${result}, storing in cache`)
			if (memcached)
				await memcached.set(key, result, cacheTimeSecs);
			return { result, cached: false }
		} else {
			throw "No food data found"
		}
	}
}




// // Get popular missions (from db only)
// async function getPopular(maxCount) {
// 	const query = "SELECT mission, count FROM popular ORDER BY count DESC LIMIT ?"
// 	return (await executeQuery(query, [maxCount]))
// 		.fetchAll()
// 		.map(row => ({ mission: row[0], count: row[1] }))
// }

// Get popular cuisines (from db only)
async function getSmartCuisine(maxCount) {
	const query = "SELECT cuisine, avg_gpa, count FROM smart_cuisine ORDER BY avg_gpa DESC LIMIT ?"
	return (await executeQuery(query, [maxCount]))
		.fetchAll()
		.map(row => { console.log("#######: " + row); return ({ cuisine: row[0], avg_gpa: Number(row[1].toFixed(2)), count: row[2] }); })
}

// Get popular lunches (from db only)
async function getSmartLunch(maxCount) {
	const query = "SELECT lunch, avg_gpa, count FROM smart_lunch ORDER BY avg_gpa DESC LIMIT ?"
	return (await executeQuery(query, [maxCount]))
		.fetchAll()
		.map(row => { console.log("#######: " + row); return ({ lunch: row[0], avg_gpa: Number(row[1].toFixed(2)), count: row[2] }); })
}

// Get popular breakfasts (from db only)
async function getSmartBreakfast(maxCount) {
	const query = "SELECT breakfast, avg_gpa, count FROM smart_breakfast ORDER BY avg_gpa DESC LIMIT ?"
	return (await executeQuery(query, [maxCount]))
		.fetchAll()
		.map(row => { console.log("#######: " + row); return ({ breakfast: row[0], avg_gpa: Number(row[1].toFixed(2)), count: row[2] }); })
}

// Return HTML for start page
app.get("/", (req, res) => {
	const topX = 10;
	Promise.all([getFoods(), getSmartCuisine(topX), getSmartLunch(topX), getSmartBreakfast(topX)]).then(values => {  //, getPopular(topX)
		const foods = values[0];
		const smartCuisine = values[1];
		const smartLunch = values[2];
		const smartBreakfast = values[3];

					
		const parameters = {
			foods: foods.result, smartCuisine, smartBreakfast, smartLunch, cachedResult: foods.cached, topX,
			hostname: os.hostname(), date: new Date(), memcachedServers, 
		}
		res.render(path.join(__dirname, 'public/index.html'), 
		parameters);

	})
})

// -------------------------------------------------------
// Get a specific mission (from cache or DB)
// -------------------------------------------------------

async function getFood(foodId) {
	const query = "SELECT id, name, type, description FROM food WHERE id = ?";
	const key = foodId;
	let cachedata = await getFromCache(key);

	if (cachedata) {
		console.log(`Cache hit for key=${key}, cachedata = ${cachedata}`)
		return { ...cachedata, cached: true }
	} else {
		console.log(`Cache miss for key=${key}, querying database`)

		let data = (await executeQuery(query, [foodId])).fetchOne()
		if (data) {
			//let result = { mission: data[0], heading: data[1], description: data[2] }
			let result = { id: data[0], name: data[1], type: data[2], description: data[3]};
			console.log(`Got result=${result}, storing in cache`)
			if (memcached)
				await memcached.set(key, result, cacheTimeSecs);
			return { ...result, cached: false }
		} else {
			throw "No data found for this food"
		}
	}
}

app.get("/survey", (req, res) => {
	const student = generateDataset();
	console.log(student);
	
	// Send the tracking message to Kafka
	sendStudentMessage(student).then(() => console.log("Sent Student to kafka"))
		.catch(e => console.log("Student Error sending to kafka", e))

	res.send("Survey done");
	
});

app.get("/food/:foodId", (req, res) => {
	let foodId = req.params["foodId"];
	console.log(foodId);
	getFood(foodId).then(data => {

		
		//foods: foods.result, smartCuisine, smartBreakfast, smartLunch, cachedResult: foods.cached, topX,
		//	hostname: os.hostname(), date: new Date(), memcachedServers, 
		const parameters = {
			food: data, cachedResult: data.cached, hostname: os.hostname(), date: new Date(), memcachedServers

		}
		res.render(path.join(__dirname, 'public/detail.html'), 
		parameters);

		//sendResponse(res, `<h1>hello from ${data.name}</h1><span>${data.description}</span>`, data.cached)
	}).catch(err => {
		console.error(err)
	})
})



// -------------------------------------------------------
// Main method
// -------------------------------------------------------

app.use(express.static('/public'));

app.listen(options.port, function () {
	console.log("Node app is running at http://localhost:" + options.port)
	
});
