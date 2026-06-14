# v86 vs v83 same-311 delta badcases

- reference_run: `stage1_personalized_advice_contract_v83_lme_s_full_65eebda`
- new_run: `v86_chronological_context_lme_qtext311_d7bd5e2`
- gains: 18
- losses: 27
- prediction_changed_count: 102

## Gains

### e949cd5d8d5d41bba8ff0ab3
- question_type: `single-session-user`
- question: How long have I been collecting vintage films?
- gold: You did not mention this information. You mentioned collecting vintage cameras but not vintage films.
- v83 prediction: three months
- v86 prediction: The provided information is not enough to answer the question: No memory explicitly states the duration of collecting vintage films

### 8997d3cef1a1f658fe97f7c5
- question_type: `multi-session`
- question: How many projects have I led or am currently leading?
- gold: 2
- v83 prediction: 1
- v86 prediction: 2

### 8c9932c7f15a04659e83d505
- question_type: `multi-session`
- question: How many different doctors did I visit?
- gold: I visited three different doctors: a primary care physician, an ENT specialist, and a dermatologist.
- v83 prediction: 3
- v86 prediction: 3

### 995a370e23572760a2fdf6f3
- question_type: `multi-session`
- question: What time did I go to bed on the day before I had a doctor's appointment?
- gold: 2 AM
- v83 prediction: The provided information is not enough to answer the question: Bedtime on May 17, 2023 (the day before the doctor's appointment) is not mentioned in any memory
- v86 prediction: 2 AM

### 2a27a0337e415cc76e0b82b3
- question_type: `multi-session`
- question: How many properties did I view before making an offer on the townhouse in the Brookside neighborhood?
- gold: I viewed four properties before making an offer on the townhouse in the Brookside neighborhood. The reasons I didn't make an offer on them were: the kitchen of the bungalow needed serious renovation, the property in Cedar Creek was out of my budget, the noise from the highway was a deal-breaker for the 1-bedroom condo, and my offer on the 2-bedroom condo was rejected due to a higher bid.
- v83 prediction: The provided information is not enough to answer the question: The total number of properties viewed before the Brookside townhouse offer is not explicitly stated. Multiple viewings are implied but not quantified
- v86 prediction: 4

### e9095a025f6dbf39641ff990
- question_type: `multi-session`
- question: How many musical instruments do I currently own?
- gold: I currently own 4 musical instruments. I've had the Fender Stratocaster electric guitar for 5 years, the Yamaha FG800 acoustic guitar for 8 years, the 5-piece Pearl Export drum set for an unspecified amount of time, and the Korg B1 piano for 3 years.
- v83 prediction: 3
- v86 prediction: 4

### 0ee8c25c59cfcb1bb56e1da5
- question_type: `multi-session`
- question: How many total pieces of writing have I completed since I started writing again three weeks ago, including short stories, poems, and pieces for the writing challenge?
- gold: 23
- v83 prediction: 22
- v86 prediction: 23

### 1a7ba85bff9b7cf5acd77b2c
- question_type: `single-session-preference`
- question: I'm planning my meal prep next week, any suggestions for new recipes?
- gold: The user would prefer responses that suggest healthy meal prep recipes, especially those that incorporate quinoa and roasted vegetables, and offer variations in protein sources. They might appreciate suggestions that build upon their existing preferences, such as new twists on chicken Caesar salads or turkey and avocado wraps. The user may not prefer responses that suggest unhealthy or high-calorie meal prep options, or those that deviate significantly from their established healthy eating habits.
- v83 prediction: Try Mexican-inspired chicken fajitas, lentil bolognese with roasted vegetables and sautéed greens, Texas-Style BBQ sauce, and sweet potato fries with spicy mayo or chipotle ranch. Use websites like Allrecipes, Epicurious, and Cooking Light for more healthy recipe ideas.
- v86 prediction: Try lentil bolognese with quinoa and roasted vegetables. Add sides like roasted broccoli with garlic and lemon, Brussels sprouts with balsamic glaze, sweet potato wedges with rosemary, or sautéed spinach with garlic. Include crunchy add-ins like toasted pumpkin seeds or chopped nuts, and cheesy delights such as shaved Parmesan or crumbled feta. Prep components in advance for easy assembly throughout the week.

### e9b0f742a1e2300420a4ca02
- question_type: `multi-session`
- question: What is the total distance of the hikes I did on two consecutive weekends?
- gold: 8 miles
- v83 prediction: 5 miles
- v86 prediction: 8 miles

### 128a1895ab851f148bbea790
- question_type: `multi-session`
- question: How many plants did I initially plant for tomatoes and chili peppers?
- gold: The information provided is not enough. You mentioned planting 5 plants for tomatoes but you did not mention chili peppers.
- v83 prediction: The provided information is not enough to answer the question: initial plants for chili peppers
- v86 prediction: The provided information is not enough to answer the question: Information about initial chili pepper plants is not provided

### 2152374e46762b936b18b5c5
- question_type: `temporal-reasoning`
- question: What gardening-related activity did I do two weeks ago?
- gold: planting 12 new tomato saplings
- v83 prediction: Using a gardening app to track weather and soil moisture levels
- v86 prediction: planted 12 new tomato saplings

### 1cdde2342583344c28e9a6aa
- question_type: `temporal-reasoning`
- question: What did I do with Rachel on the Wednesday two months ago?
- gold: I started taking ukulele lessons with Rachel.
- v83 prediction: Started ukulele lessons
- v86 prediction: You took ukulele lessons with Rachel.

### 3f1b0d114b185d2ca9d2dc2d
- question_type: `temporal-reasoning`
- question: How many days before the 'Rack Fest' did I participate in the 'Turbocharged Tuesdays' event?
- gold: 4 days.
- v83 prediction: 10
- v86 prediction: 4

### e74a916402e973452dae7af4
- question_type: `knowledge-update`
- question: How many stars do I need to reach the gold level on my Starbucks Rewards app?
- gold: 120
- v83 prediction: 125
- v86 prediction: 120

### 767dc4d1e636373a70a888ac
- question_type: `knowledge-update`
- question: How many autographed baseballs have I added to my collection in the first three months of collection?
- gold: 15
- v83 prediction: 20
- v86 prediction: 15

### b8c9cbde1dc6e907bc4fc710
- question_type: `knowledge-update`
- question: How much time do I dedicate to coding exercises each day?
- gold: about two hours
- v83 prediction: two hours
- v86 prediction: two hours

### bfed71c5f7001160a920c1c8
- question_type: `knowledge-update`
- question: Where do I currently keep my old sneakers?
- gold: in a shoe rack in my closet
- v83 prediction: under the bed
- v86 prediction: shoe rack in the closet

### 4b2d65beb209dbf5f2059c19
- question_type: `single-session-assistant`
- question: I was going through our previous conversation about making a classic French omelette, and I wanted to confirm - how many eggs did you say we need for the recipe?
- gold: 2-3 eggs
- v83 prediction: 3
- v86 prediction: 2-3 eggs

## Losses

### 5a37a93ab3c66f6b71a739ad
- question_type: `multi-session`
- question: How many model kits have I worked on or bought?
- gold: I have worked on or bought five model kits. The scales of the models are: Revell F-15 Eagle (scale not mentioned), Tamiya 1/48 scale Spitfire Mk.V, 1/16 scale German Tiger I tank, 1/72 scale B-29 bomber, and 1/24 scale '69 Camaro.
- v83 prediction: 5 model kits: Revell F-15 Eagle, 1/72 scale B-29 bomber, 1/24 scale '69 Camaro, 1/16 scale German Tiger I tank, and Tamiya 1/48 scale Spitfire Mk.V
- v86 prediction: 2

### 86de49c52907a01f387b7c5c
- question_type: `multi-session`
- question: How many babies were born to friends and family members in the last few months?
- gold: 5
- v83 prediction: 5
- v86 prediction: 4

### 3327f6bb9f2b962d1187cd6b
- question_type: `multi-session`
- question: How many times did I bake something in the past two weeks?
- gold: 4
- v83 prediction: 4
- v86 prediction: 5

### d43529e1b75f789f824ffba9
- question_type: `multi-session`
- question: How many different museums or galleries did I visit in the month of February?
- gold: 2
- v83 prediction: 2
- v86 prediction: 1

### 1afa4fb00c6e7626e63dca62
- question_type: `multi-session`
- question: How many pieces of jewelry did I acquire in the last two months?
- gold: 3
- v83 prediction: 3
- v86 prediction: 2

### 1ee64dcf571ca60c0e4ef6c1
- question_type: `multi-session`
- question: How much money did I raise in total through all the charity events I participated in?
- gold: $5,850
- v83 prediction: $5,850
- v86 prediction: $5,250

### c186751ffc51e53f6fac2422
- question_type: `multi-session`
- question: How many days did I spend participating in faith-related activities in December?
- gold: 3 days.
- v83 prediction: 3
- v86 prediction: 2

### 4be721ae00fda00fbb5ac16b
- question_type: `multi-session`
- question: How many kitchen items did I replace or fix?
- gold: I replaced or fixed five items: the kitchen faucet, the kitchen mat, the toaster, the coffee maker, and the kitchen shelves.
- v83 prediction: 5
- v86 prediction: 3

### 2ea366047e35ba03b980953f
- question_type: `multi-session`
- question: How many graduation ceremonies have I attended in the past three months?
- gold: 3
- v83 prediction: 3
- v86 prediction: 4

### b6d4bc26da6c5292c4a9645a
- question_type: `multi-session`
- question: How many days did it take for my iPad case to arrive after I bought it?
- gold: The information provided is not enough. You did not mention buying an iPad case.
- v83 prediction: The provided information is not enough to answer the question: iPad case purchase or delivery information
- v86 prediction: 2

### 45ccdf8947da04d80402bb2e
- question_type: `multi-session`
- question: How many days did I spend in total traveling in Hawaii and in Seattle?
- gold: The information provided is not enough. You mentioned traveling for 10 days in Hawaii but did not mention abything about the trip to Seattle.
- v83 prediction: The provided information is not enough to answer the question: duration of Hawaii trip and any mention of Seattle
- v86 prediction: 10

### e3353ec1ec904aa2876b1a3e
- question_type: `multi-session`
- question: How many plants did I initially plant for tomatoes and cucumbers?
- gold: 8
- v83 prediction: 5 tomato plants and 3 cucumber plants
- v86 prediction: 5 tomato plants; initial cucumber plant count not available

### ef038b977b2e1598e0c0e026
- question_type: `multi-session`
- question: How many Marvel movies did I re-watch?
- gold: 2
- v83 prediction: 2
- v86 prediction: 3

### 42bc66bb30b91380d77e5e92
- question_type: `multi-session`
- question: How many sports have I played competitively in the past?
- gold: two
- v83 prediction: 2
- v86 prediction: 1

### 9fd04c3718fe7091041034e7
- question_type: `multi-session`
- question: What is the total number of days I spent in Japan and Chicago?
- gold: 11 days (or 12 days, if April 15th to 22nd is considered as 8 days)
- v83 prediction: 12
- v86 prediction: 9

### 15d167d1ad74265d5887e5b9
- question_type: `temporal-reasoning`
- question: How many weeks ago did I start using the cashback app 'Ibotta'?
- gold: 3 weeks ago
- v83 prediction: 3
- v86 prediction: 2.86 weeks

### 3e1b497a50eb3120dc176277
- question_type: `temporal-reasoning`
- question: How many weeks passed between the time I sold homemade baked goods at the Farmers' Market for the last time and the time I participated in the Spring Fling Market?
- gold: 3 weeks
- v83 prediction: 3
- v86 prediction: 3.29 weeks

### 6850b04ec8944eaaf1874648
- question_type: `temporal-reasoning`
- question: How many weeks ago did I attend the 'Summer Nights' festival at Universal Studios Hollywood?
- gold: 3 weeks ago
- v83 prediction: 3
- v86 prediction: 6

### d1194f5e15857de1239046fc
- question_type: `temporal-reasoning`
- question: Which book did I finish a week ago?
- gold: 'The Nightingale' by Kristin Hannah
- v83 prediction: The Nightingale by Kristin Hannah
- v86 prediction: The Nightingale

### 453f3e55b4b3725c16004ac9
- question_type: `temporal-reasoning`
- question: What was the the life event of one of my relatives that I participated in a week ago?
- gold: my cousin's wedding
- v83 prediction: The life event was attending my cousin's wedding as a bridesmaid.
- v86 prediction: The provided information is not enough to answer the question: No memory context describes a life event of a relative that occurred in the week prior to June 22, 2023

### 57d8cea68364dd86035b1945
- question_type: `temporal-reasoning`
- question: How long had I been bird watching when I attended the bird watching workshop?
- gold: Two months
- v83 prediction: two months
- v86 prediction: The provided information is not enough to answer the question: The duration of bird watching at the time of the workshop is not explicitly stated; the only available duration is current (three months), which cannot be used to infer the past duration without additional assumptions

### c88235d467ee2d0ffc286a2a
- question_type: `knowledge-update`
- question: How many Korean restaurants have I tried in my city?
- gold: four
- v83 prediction: 4
- v86 prediction: 3

### 5ef4036fc92607e9cbe4591d
- question_type: `knowledge-update`
- question: What day of the week do I take a cocktail-making class?
- gold: Friday
- v83 prediction: Friday
- v86 prediction: Thursday

### beb0a3bdb35a23a257132b5e
- question_type: `knowledge-update`
- question: Where did I go on my most recent family trip?
- gold: Paris
- v83 prediction: Paris
- v86 prediction: Santa Monica

### 997f749ec7c829ed33f026b8
- question_type: `knowledge-update`
- question: How many sessions of the bereavement support group did I attend?
- gold: five
- v83 prediction: 5
- v86 prediction: 3

### ad7692deb1c06e5ee69c7b5d
- question_type: `knowledge-update`
- question: How many projects have I completed since starting painting classes?
- gold: 5
- v83 prediction: 5
- v86 prediction: 4

### c5c250ebd8ee91505c171efe
- question_type: `knowledge-update`
- question: How many women are on the team led by my former manager Rachel?
- gold: 6
- v83 prediction: 6
- v86 prediction: 5
