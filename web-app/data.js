const cuisines = ['italian', 'asian', 'german', 'french'] //+30
const lunches = ['pizza', 'rice', 'noodles', 'tteokbokki'] //30
const breakfasts = ['bread', 'cereals', 'donuts', 'scrambled eggs'] //30

const gpaProb = {1.0:0.03, 1.3:0.05, 1.7:0.08, 2.0:0.10, 2.3:0.12, 2.7:0.14, 3.0:0.16, 3.3:0.18, 3.7:0.10, 4.0:0.04}
const cuisineProb = {0:0.6, 1:0.2, 2:0.1, 3:0.1}

const generateDataset = () => {
    const datasetLimit = 4; //edit on live when 30 datasets are available
    const cuisineId = getRandomWeightedGPA(cuisineProb);
    const lunchId = getRandomInt(0, datasetLimit-1);
    const breakfastId = getRandomInt(0, datasetLimit-1);

    const gpa = getRandomWeightedGPA(gpaProb);
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


function getRandomWeightedGPA(prob) {
    let i, sum=0, r=Math.random();
        for (i in prob) {
    sum += prob[i];
    if (r <= sum) return parseFloat(i);
  }
}

module.exports = {
    generateDataset
}