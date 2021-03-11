// defining probabilites for more diverse data
// this assumes we have 10 cuisines, 20 lunches and 20 breakfasts
const gpaProb = {1.0:0.03, 1.3:0.05, 1.7:0.08, 2.0:0.10, 2.3:0.12, 2.7:0.14, 3.0:0.16, 3.3:0.18, 3.7:0.10, 4.0:0.04};
const cuisineProb = {0:0.25, 1:0.2, 2:0.05, 3:0.1, 4:0.1, 5:0.15, 6:0.05, 7:0.03, 8:0.02, 9:0.05};
const lunchProb = {0:0.13, 1:0.075, 2:0.075, 3:0.075, 4:0.075, 5:0.038, 6:0.038, 7:0.038, 8:0.038, 9:0.038,
                    10:0.038, 11:0.038, 12:0.038, 13:0.038, 14:0.038, 15:0.038, 16:0.038, 17:0.038, 18:0.03, 19:0.038};

const breakfastProb = {0:0.10, 1:0.075, 2:0.038, 3:0.075, 4:0.075, 5:0.038, 6:0.038, 7:0.038, 8:0.038, 9:0.038,
                        10:0.038, 11:0.038, 12:0.038, 13:0.038, 14:0.038, 15:0.038, 16:0.038, 17:0.038, 18:0.038, 19:0.105}; 


/**
 * Generates a random Survey result with given arrays and a gpa
 * @param {*} cuisines available cuisines array ['italian', 'german',..]
 * @param {*} lunches available lunches array ['pizza', 'rice',..]
 * @param {*} breakfasts available breakfast array ['cereals', 'donuts',...]
 * @returns a survey object with gpa, cuisine, lunch, breakfast and timestamp
 */
const generateDataset = (cuisines, lunches, breakfasts) => {
    const cuisineId = getRandomWeighted(cuisineProb);
    const lunchId = getRandomWeighted(lunchProb);
    const breakfastId = getRandomWeighted(breakfastProb);

    const gpa = getRandomWeighted(gpaProb);
	const generatedStudentSurvey = {gpa: gpa,
         fav_cuisine: cuisines[cuisineId],
         fav_lunch: lunches[lunchId],
         fav_breakfast: breakfasts[breakfastId],
         timestamp: Math.floor(new Date() / 1000)}


    return generatedStudentSurvey;
}

/**
 * Method that gives back a random number with given probablility
 * @param {*} prob the probablity, e.g. {0:0.1, 1:0.9} 10% for 0, 90% for 1
 * @returns a random weighted integer
 */
function getRandomWeighted(prob) {
    let i, sum=0, r=Math.random();
    for (i in prob) {
        sum += prob[i];
        if (r <= sum) {
            return parseInt(i);    

        } 
    }
  return 0;
}

//export the method to require it in index.js
module.exports = {
    generateDataset
}

//keeping the arrays below as reference
// const cuisines = ['italian', 'chinese', 'mexican','german', 'french',
//                  'indian', 'thai', 'korean', 'japanese', 'american'] 
                 
// const lunches = ['pizza', 'rice', 'noodles', 'tteokbokki', 'ham sandwich',
//                 'lasagna','buddha bowl','pea soup','grilled chicken salad','chili con carne',
//                 'gyros','bbq','pho','cevapcici','sausages',
//                 'curry','tacos','tuna salad','sushi','cassoulet']
                
// const breakfasts = ['bread', 'cereals', 'donuts', 'scrambled eggs', 'smoothie',
//                 'baguette','avocado toast','jam toast','bacon','protein drink',
//                 'yogurt','fruit salad','vegetables','sweet bread','nutella toast',
//                 'rice dish','jelly','pudding','quinoa','no breakfast'] 

