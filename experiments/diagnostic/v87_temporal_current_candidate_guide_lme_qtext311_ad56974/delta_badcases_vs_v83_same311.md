# v87 vs v83 same-311 delta badcases

- reference_run: `stage1_personalized_advice_contract_v83_lme_s_full_65eebda`
- new_run: `v87_temporal_current_candidate_guide_lme_qtext311_ad56974`
- gains: 14
- losses: 17
- prediction_changed_count: 70

## Gains

### e3b12960136041241dc62c39
- question_type: `multi-session`
- question: How much total money have I spent on bike-related expenses since the start of the year?
- gold: $185
- v83 prediction: 65
- v87 prediction: $185

### 0ee8c25c59cfcb1bb56e1da5
- question_type: `multi-session`
- question: How many total pieces of writing have I completed since I started writing again three weeks ago, including short stories, poems, and pieces for the writing challenge?
- gold: 23
- v83 prediction: 22
- v87 prediction: 23

### d00b4949227c41f760b0f64c
- question_type: `multi-session`
- question: How many fish are there in my 30-gallon tank?
- gold: The information provided is not enough. You did not mention that you have a 30-gallon tank.
- v83 prediction: The provided information is not enough to answer the question: The provided information is about a 20-gallon tank, but the question asks about a 30-gallon tank. No data about fish in a 30-gallon tank is available
- v87 prediction: The provided information is not enough to answer the question: The provided information is about a 20-gallon tank, but the question asks about a 30-gallon tank. No data about fish in a 30-gallon tank is available

### 79579c32a1b250cf632b717b
- question_type: `multi-session`
- question: How many years in total did I spend in formal education from high school to the completion of my Master's degree?
- gold: The information provided is not enough. You mentioned 4 years in high school (2010-2014), 2 years at PCC (2014-2016), and 4 years at UCLA (2016-2020). But you didn't mention the number of years you spend getting the Master's degree
- v83 prediction: 4
- v87 prediction: The provided information is not enough to answer the question: The duration of the Master's degree program and its completion status are unknown, making it impossible to calculate the total years from high school to Master's completion

### 1a7ba85bff9b7cf5acd77b2c
- question_type: `single-session-preference`
- question: I'm planning my meal prep next week, any suggestions for new recipes?
- gold: The user would prefer responses that suggest healthy meal prep recipes, especially those that incorporate quinoa and roasted vegetables, and offer variations in protein sources. They might appreciate suggestions that build upon their existing preferences, such as new twists on chicken Caesar salads or turkey and avocado wraps. The user may not prefer responses that suggest unhealthy or high-calorie meal prep options, or those that deviate significantly from their established healthy eating habits.
- v83 prediction: Try Mexican-inspired chicken fajitas, lentil bolognese with roasted vegetables and sautéed greens, Texas-Style BBQ sauce, and sweet potato fries with spicy mayo or chipotle ranch. Use websites like Allrecipes, Epicurious, and Cooking Light for more healthy recipe ideas.
- v87 prediction: Try lentil bolognese with quinoa and pair it with roasted vegetables (like broccoli, Brussels sprouts, or sweet potatoes), sautéed greens (spinach or kale), crunchy add-ins (pumpkin seeds or nuts), and creamy or tangy cheeses (feta or Parmesan). For variety, consider Mexican-inspired dishes like chicken fajitas or homemade sweet potato fries with spicy mayo or chipotle ranch dressing.

### cdde2a2cdd99eb2b49880db5
- question_type: `multi-session`
- question: How many dinner parties have I attended in the past month?
- gold: three
- v83 prediction: 2
- v87 prediction: 3

### 2152374e46762b936b18b5c5
- question_type: `temporal-reasoning`
- question: What gardening-related activity did I do two weeks ago?
- gold: planting 12 new tomato saplings
- v83 prediction: Using a gardening app to track weather and soil moisture levels
- v87 prediction: Planted 12 new tomato saplings.

### 325a0f2d711df68b798236a3
- question_type: `temporal-reasoning`
- question: What was the airline that I flied with on Valentine's day?
- gold: American Airlines
- v83 prediction: The provided information is not enough to answer the question: specific airline flown on Valentine's Day (2023-02-14)
- v87 prediction: American Airlines

### 1cdde2342583344c28e9a6aa
- question_type: `temporal-reasoning`
- question: What did I do with Rachel on the Wednesday two months ago?
- gold: I started taking ukulele lessons with Rachel.
- v83 prediction: Started ukulele lessons
- v87 prediction: You took ukulele lessons with Rachel.

### 3f1b0d114b185d2ca9d2dc2d
- question_type: `temporal-reasoning`
- question: How many days before the 'Rack Fest' did I participate in the 'Turbocharged Tuesdays' event?
- gold: 4 days.
- v83 prediction: 10
- v87 prediction: 4

### 26c00eb2d2a565814caf44d9
- question_type: `temporal-reasoning`
- question: How long had I been using the new area rug when I rearranged my living room furniture?
- gold: One week. Answers ranging from 7 days to 10 days are also acceptable.
- v83 prediction: 19 days
- v87 prediction: 10 days

### 767dc4d1e636373a70a888ac
- question_type: `knowledge-update`
- question: How many autographed baseballs have I added to my collection in the first three months of collection?
- gold: 15
- v83 prediction: 20
- v87 prediction: 15

### b8c9cbde1dc6e907bc4fc710
- question_type: `knowledge-update`
- question: How much time do I dedicate to coding exercises each day?
- gold: about two hours
- v83 prediction: two hours
- v87 prediction: two hours

### 7933cff5854d25ce3c9e8901
- question_type: `knowledge-update`
- question: How long have I been living in my current apartment in Shinjuku?
- gold: The information provided is not enough. You mentioned living in Harajuku but not Shinjuku.
- v83 prediction: 7 months
- v87 prediction: The provided information is not enough to determine how long you've been living in your current apartment in Shinjuku, as all evidence points to Harajuku, not Shinjuku.

## Losses

### 81df9103418e931f73ff48af
- question_type: `single-session-user`
- question: How long is my daily commute to work?
- gold: 45 minutes each way
- v83 prediction: 45 minutes each way
- v87 prediction: 45 minutes

### d43529e1b75f789f824ffba9
- question_type: `multi-session`
- question: How many different museums or galleries did I visit in the month of February?
- gold: 2
- v83 prediction: 2
- v87 prediction: 1

### 0e3b85f1ae5dddca4b328a0f
- question_type: `multi-session`
- question: How many fitness classes do I attend in a typical week?
- gold: 5
- v83 prediction: 5
- v87 prediction: 4

### 1afa4fb00c6e7626e63dca62
- question_type: `multi-session`
- question: How many pieces of jewelry did I acquire in the last two months?
- gold: 3
- v83 prediction: 3
- v87 prediction: 2

### 5662691a4bc7b9290f5727a8
- question_type: `multi-session`
- question: How much total money did I spend on attending workshops in the last four months?
- gold: $720
- v83 prediction: 720
- v87 prediction: 500

### b29ecee4bbd616d18f051048
- question_type: `multi-session`
- question: How many different museums or galleries did I visit in December?
- gold: 0. You did not mention visitng any museum in December
- v83 prediction: The provided information is not enough to answer the question: No information about visits to museums or galleries in December
- v87 prediction: The provided information is not enough to answer the question: No information about visits to museums or galleries in December

### 45ccdf8947da04d80402bb2e
- question_type: `multi-session`
- question: How many days did I spend in total traveling in Hawaii and in Seattle?
- gold: The information provided is not enough. You mentioned traveling for 10 days in Hawaii but did not mention abything about the trip to Seattle.
- v83 prediction: The provided information is not enough to answer the question: duration of Hawaii trip and any mention of Seattle
- v87 prediction: The provided information is not enough to answer the question: No information on days spent in Hawaii or Seattle; no duration for Hawaii trip and no mention of Seattle at all

### 34b46e8aabe038118cec7681
- question_type: `multi-session`
- question: What was the approximate increase in Instagram followers I experienced in two weeks?
- gold: 100
- v83 prediction: 100
- v87 prediction: 350

### 3e1b497a50eb3120dc176277
- question_type: `temporal-reasoning`
- question: How many weeks passed between the time I sold homemade baked goods at the Farmers' Market for the last time and the time I participated in the Spring Fling Market?
- gold: 3 weeks
- v83 prediction: 3
- v87 prediction: 3.29 weeks

### 2976f637e5d717258b993c04
- question_type: `temporal-reasoning`
- question: I mentioned participating in a sports event two weeks ago. What was the event?
- gold: The company's annual charity soccer tournament.
- v83 prediction: company's annual charity soccer tournament
- v87 prediction: The provided information is not enough to answer the question: No memory confirms a sports event from exactly two weeks ago (2023-06-03)

### 453f3e55b4b3725c16004ac9
- question_type: `temporal-reasoning`
- question: What was the the life event of one of my relatives that I participated in a week ago?
- gold: my cousin's wedding
- v83 prediction: The life event was attending my cousin's wedding as a bridesmaid.
- v87 prediction: The provided information is not enough to answer the question: No memory context describes a life event of a relative that the user participated in a week ago (June 15–21, 2023)

### 2a18e972b47c27c2c1f2fdb8
- question_type: `temporal-reasoning`
- question: How long have I been working before I started my current job at NovaTech?
- gold: 4 years and 9 months
- v83 prediction: 4 years and 9 months
- v87 prediction: The provided information is not enough to determine how long you worked before starting at NovaTech.

### 57d8cea68364dd86035b1945
- question_type: `temporal-reasoning`
- question: How long had I been bird watching when I attended the bird watching workshop?
- gold: Two months
- v83 prediction: two months
- v87 prediction: The provided information is not enough to answer the question: The duration of bird watching specifically before attending the workshop is not explicitly stated. The only related information is that the workshop was a month ago, but the user's bird watching duration prior to that...

### 1f7723fca5c03dfc8ff0e0ca
- question_type: `temporal-reasoning`
- question: How long have I been working before I started my current job at Google?
- gold: The information provided is not enough. From the information provided, You haven't started working at Google yet.
- v83 prediction: The provided information is not enough to determine how long you have been working before starting your current job at Google.
- v87 prediction: 4 years and 3 months

### 71c309443747c6d8faf4a7d2
- question_type: `temporal-reasoning`
- question: How many days before I bought my iPad did I attend the Holiday Market?
- gold: The information provided is not enough. You mentioned getting the iPhone 13 Pro and attending the market, but you did not mention buying an iPad.
- v83 prediction: The provided information is not enough to answer the question: The date of the iPad purchase is not provided in the context, making it impossible to calculate the number of days between the Holiday Market and the iPad purchase
- v87 prediction: 7

### 37b842706f89305f735ceb16
- question_type: `knowledge-update`
- question: How long have my parents been staying with me in the US?
- gold: nine months
- v83 prediction: nine months
- v87 prediction: six months

### 7623367fb36a659f5152c676
- question_type: `single-session-assistant`
- question: I was looking back at our previous chat and I wanted to confirm, how many times did the Chiefs play the Jaguars at Arrowhead Stadium?
- gold: The Chiefs played the Jaguars 12 times at Arrowhead Stadium.
- v83 prediction: 12
- v87 prediction: 12
