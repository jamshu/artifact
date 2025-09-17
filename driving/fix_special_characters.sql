-- Fix special characters in question explanations that cause frontend errors
-- Replace single quotes and other problematic characters

BEGIN TRANSACTION;

-- Fix specific questions with single quotes by rewriting them cleanly
UPDATE QuizQuestion 
SET explanation = 'According to the "Right Before Left Rule", the vehicle on the right has the right-of-way at equal intersections.'
WHERE id = 360;

UPDATE QuizQuestion 
SET explanation = 'The sources explicitly list "At intersections and railway lanes" and "At pedestrian crossings" as places where overtaking is prohibited.'
WHERE id = 361;

UPDATE QuizQuestion 
SET explanation = 'The procedure for withdrawing a license is applied if the number of points recorded in the violating driver record reaches 24 points within one Hijri year.'
WHERE id = 365;

UPDATE QuizQuestion 
SET explanation = 'A driver fitness is crucial for safety. This includes being well-rested and not under the influence of any substances or emotional distress.'
WHERE id = 366;

UPDATE QuizQuestion 
SET explanation = 'Blind spots are areas that are obscured from the driver view and require a physical head check to see.'
WHERE id = 397;

UPDATE QuizQuestion 
SET explanation = 'The minimum age to obtain a driver license in Saudi Arabia is 18 years.'
WHERE id = 423;

UPDATE QuizQuestion 
SET explanation = 'A driver must carry a valid driver license, vehicle registration, and insurance at all times.'
WHERE id = 424;

UPDATE QuizQuestion 
SET explanation = 'A driver must always carry their valid driver license, vehicle registration (Istimara), and proof of insurance.'
WHERE id = 432;

UPDATE QuizQuestion 
SET explanation = 'Accumulating 24 points in one Hijri year results in driver license withdrawal.'
WHERE id = 442;

UPDATE QuizQuestion 
SET explanation = 'The minimum age for obtaining a private driver license is 18 years (with exceptions for 17-year-olds with temporary permits).'
WHERE id = 443;

UPDATE QuizQuestion 
SET explanation = 'A private driver license is valid for a maximum of 10 years.'
WHERE id = 444;

UPDATE QuizQuestion 
SET explanation = 'A broken white line indicates that you may cross it when it is safe to do so, such as for overtaking.'
WHERE id = 449;

-- General cleanup: Replace any remaining single quotes with double quotes for quoted terms
UPDATE QuizQuestion 
SET explanation = REPLACE(REPLACE(explanation, '''', '"'), '''', '"')
WHERE explanation LIKE '%''%';

-- Also check and fix questions text if needed
UPDATE QuizQuestion 
SET question = REPLACE(REPLACE(question, '''', '"'), '''', '"')
WHERE question LIKE '%''%';

-- Fix any backslashes that might cause issues
UPDATE QuizQuestion 
SET explanation = REPLACE(explanation, '\', '')
WHERE explanation LIKE '%\%';

UPDATE QuizQuestion 
SET question = REPLACE(question, '\', '')
WHERE question LIKE '%\%';

COMMIT;
