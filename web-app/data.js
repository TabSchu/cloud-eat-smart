const cuisines = ['italian', 'asian', 'german', 'french'] //+30
const lunches = ['pizza', 'rice', 'noodles', 'tteokbokki'] //30
const breakfasts = ['bread', 'cereals', 'donuts', 'scrambled eggs'] //30

const generateDataset = () => {
    const datasetLimit = 4; //edit on live when 30 datasets are available
    const cuisineId = getRandomInt(0, datasetLimit-1);
    const lunchId = getRandomInt(0, datasetLimit-1);
    const breakfastId = getRandomInt(0, datasetLimit-1);

    const gpa = (getRandomInt(10, 40) / 10);
	const generatedStudent = {gpa: gpa,
         fav_cuisine: cuisines[cuisineId],
         fav_lunch: lunches[lunchId],
         fav_breakfast: breakfasts[breakfastId],
         timestamp: Math.floor(new Date() / 1000)}

    return generatedStudent;
}

function getRandomInt(min, max) {
    min = Math.ceil(min);
    max = Math.floor(max);
    return Math.floor(Math.random() * (max - min + 1)) + min;
}


module.exports = {
    generateDataset
}