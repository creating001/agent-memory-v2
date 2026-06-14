# v87 vs v86 same-311 delta badcases

- reference_run: `v86_chronological_context_lme_qtext311_d7bd5e2`
- new_run: `v87_temporal_current_candidate_guide_lme_qtext311_ad56974`
- gains: 28
- losses: 22
- prediction_changed_count: 108

## Gains

### 5a37a93ab3c66f6b71a739ad
- question_type: `multi-session`
- question: How many model kits have I worked on or bought?
- gold: I have worked on or bought five model kits. The scales of the models are: Revell F-15 Eagle (scale not mentioned), Tamiya 1/48 scale Spitfire Mk.V, 1/16 scale German Tiger I tank, 1/72 scale B-29 bomber, and 1/24 scale '69 Camaro.
- v86 prediction: 2
- v87 prediction: 5 model kits: Revell F-15 Eagle, 1/72 scale B-29 bomber, 1/24 scale '69 Camaro, 1/16 scale German Tiger I tank, and Tamiya 1/48 scale Spitfire Mk.V

### e3b12960136041241dc62c39
- question_type: `multi-session`
- question: How much total money have I spent on bike-related expenses since the start of the year?
- gold: $185
- v86 prediction: 65
- v87 prediction: $185

### 86de49c52907a01f387b7c5c
- question_type: `multi-session`
- question: How many babies were born to friends and family members in the last few months?
- gold: 5
- v86 prediction: 4
- v87 prediction: 5

### 3327f6bb9f2b962d1187cd6b
- question_type: `multi-session`
- question: How many times did I bake something in the past two weeks?
- gold: 4
- v86 prediction: 5
- v87 prediction: 4

### 1ee64dcf571ca60c0e4ef6c1
- question_type: `multi-session`
- question: How much money did I raise in total through all the charity events I participated in?
- gold: $5,850
- v86 prediction: $5,250
- v87 prediction: $5,850

### c186751ffc51e53f6fac2422
- question_type: `multi-session`
- question: How many days did I spend participating in faith-related activities in December?
- gold: 3 days.
- v86 prediction: 2
- v87 prediction: 3

### 4be721ae00fda00fbb5ac16b
- question_type: `multi-session`
- question: How many kitchen items did I replace or fix?
- gold: I replaced or fixed five items: the kitchen faucet, the kitchen mat, the toaster, the coffee maker, and the kitchen shelves.
- v86 prediction: 3
- v87 prediction: 5

### 2ea366047e35ba03b980953f
- question_type: `multi-session`
- question: How many graduation ceremonies have I attended in the past three months?
- gold: 3
- v86 prediction: 4
- v87 prediction: 3

### d00b4949227c41f760b0f64c
- question_type: `multi-session`
- question: How many fish are there in my 30-gallon tank?
- gold: The information provided is not enough. You did not mention that you have a 30-gallon tank.
- v86 prediction: The provided information is not enough to answer the question: information about a 30-gallon tank and its fish count
- v87 prediction: The provided information is not enough to answer the question: The provided information is about a 20-gallon tank, but the question asks about a 30-gallon tank. No data about fish in a 30-gallon tank is available

### b6d4bc26da6c5292c4a9645a
- question_type: `multi-session`
- question: How many days did it take for my iPad case to arrive after I bought it?
- gold: The information provided is not enough. You did not mention buying an iPad case.
- v86 prediction: 2
- v87 prediction: The provided information is not enough to answer the question: iPad case purchase and delivery timeline

### 79579c32a1b250cf632b717b
- question_type: `multi-session`
- question: How many years in total did I spend in formal education from high school to the completion of my Master's degree?
- gold: The information provided is not enough. You mentioned 4 years in high school (2010-2014), 2 years at PCC (2014-2016), and 4 years at UCLA (2016-2020). But you didn't mention the number of years you spend getting the Master's degree
- v86 prediction: 8
- v87 prediction: The provided information is not enough to answer the question: The duration of the Master's degree program and its completion status are unknown, making it impossible to calculate the total years from high school to Master's completion

### e3353ec1ec904aa2876b1a3e
- question_type: `multi-session`
- question: How many plants did I initially plant for tomatoes and cucumbers?
- gold: 8
- v86 prediction: 5 tomato plants; initial cucumber plant count not available
- v87 prediction: 5 tomato plants and 3 cucumber plants

### ef038b977b2e1598e0c0e026
- question_type: `multi-session`
- question: How many Marvel movies did I re-watch?
- gold: 2
- v86 prediction: 3
- v87 prediction: 2

### 42bc66bb30b91380d77e5e92
- question_type: `multi-session`
- question: How many sports have I played competitively in the past?
- gold: two
- v86 prediction: 1
- v87 prediction: 2

### 9fd04c3718fe7091041034e7
- question_type: `multi-session`
- question: What is the total number of days I spent in Japan and Chicago?
- gold: 11 days (or 12 days, if April 15th to 22nd is considered as 8 days)
- v86 prediction: 9
- v87 prediction: 12

### cdde2a2cdd99eb2b49880db5
- question_type: `multi-session`
- question: How many dinner parties have I attended in the past month?
- gold: three
- v86 prediction: 2
- v87 prediction: 3

### 15d167d1ad74265d5887e5b9
- question_type: `temporal-reasoning`
- question: How many weeks ago did I start using the cashback app 'Ibotta'?
- gold: 3 weeks ago
- v86 prediction: 2.86 weeks
- v87 prediction: 3 weeks

### 6850b04ec8944eaaf1874648
- question_type: `temporal-reasoning`
- question: How many weeks ago did I attend the 'Summer Nights' festival at Universal Studios Hollywood?
- gold: 3 weeks ago
- v86 prediction: 6
- v87 prediction: 3 weeks

### d1194f5e15857de1239046fc
- question_type: `temporal-reasoning`
- question: Which book did I finish a week ago?
- gold: 'The Nightingale' by Kristin Hannah
- v86 prediction: The Nightingale
- v87 prediction: The Nightingale by Kristin Hannah

### 325a0f2d711df68b798236a3
- question_type: `temporal-reasoning`
- question: What was the airline that I flied with on Valentine's day?
- gold: American Airlines
- v86 prediction: JetBlue
- v87 prediction: American Airlines

### 26c00eb2d2a565814caf44d9
- question_type: `temporal-reasoning`
- question: How long had I been using the new area rug when I rearranged my living room furniture?
- gold: One week. Answers ranging from 7 days to 10 days are also acceptable.
- v86 prediction: three weeks
- v87 prediction: 10 days

### c88235d467ee2d0ffc286a2a
- question_type: `knowledge-update`
- question: How many Korean restaurants have I tried in my city?
- gold: four
- v86 prediction: 3
- v87 prediction: 4

### 5ef4036fc92607e9cbe4591d
- question_type: `knowledge-update`
- question: What day of the week do I take a cocktail-making class?
- gold: Friday
- v86 prediction: Thursday
- v87 prediction: Friday

### beb0a3bdb35a23a257132b5e
- question_type: `knowledge-update`
- question: Where did I go on my most recent family trip?
- gold: Paris
- v86 prediction: Santa Monica
- v87 prediction: Paris

### 997f749ec7c829ed33f026b8
- question_type: `knowledge-update`
- question: How many sessions of the bereavement support group did I attend?
- gold: five
- v86 prediction: 3
- v87 prediction: 5

### ad7692deb1c06e5ee69c7b5d
- question_type: `knowledge-update`
- question: How many projects have I completed since starting painting classes?
- gold: 5
- v86 prediction: 4
- v87 prediction: 5

### c5c250ebd8ee91505c171efe
- question_type: `knowledge-update`
- question: How many women are on the team led by my former manager Rachel?
- gold: 6
- v86 prediction: 5
- v87 prediction: 6

### 7933cff5854d25ce3c9e8901
- question_type: `knowledge-update`
- question: How long have I been living in my current apartment in Shinjuku?
- gold: The information provided is not enough. You mentioned living in Harajuku but not Shinjuku.
- v86 prediction: 7 months
- v87 prediction: The provided information is not enough to determine how long you've been living in your current apartment in Shinjuku, as all evidence points to Harajuku, not Shinjuku.

## Losses

### 81df9103418e931f73ff48af
- question_type: `single-session-user`
- question: How long is my daily commute to work?
- gold: 45 minutes each way
- v86 prediction: 45 minutes each way
- v87 prediction: 45 minutes

### e949cd5d8d5d41bba8ff0ab3
- question_type: `single-session-user`
- question: How long have I been collecting vintage films?
- gold: You did not mention this information. You mentioned collecting vintage cameras but not vintage films.
- v86 prediction: The provided information is not enough to answer the question: No memory explicitly states the duration of collecting vintage films
- v87 prediction: three months

### 8997d3cef1a1f658fe97f7c5
- question_type: `multi-session`
- question: How many projects have I led or am currently leading?
- gold: 2
- v86 prediction: 2
- v87 prediction: 1

### 8c9932c7f15a04659e83d505
- question_type: `multi-session`
- question: How many different doctors did I visit?
- gold: I visited three different doctors: a primary care physician, an ENT specialist, and a dermatologist.
- v86 prediction: 3
- v87 prediction: 3

### 995a370e23572760a2fdf6f3
- question_type: `multi-session`
- question: What time did I go to bed on the day before I had a doctor's appointment?
- gold: 2 AM
- v86 prediction: 2 AM
- v87 prediction: The provided information is not enough to answer the question: Bedtime on May 17, 2023, the day before the doctor's appointment

### 2a27a0337e415cc76e0b82b3
- question_type: `multi-session`
- question: How many properties did I view before making an offer on the townhouse in the Brookside neighborhood?
- gold: I viewed four properties before making an offer on the townhouse in the Brookside neighborhood. The reasons I didn't make an offer on them were: the kitchen of the bungalow needed serious renovation, the property in Cedar Creek was out of my budget, the noise from the highway was a deal-breaker for the 1-bedroom condo, and my offer on the 2-bedroom condo was rejected due to a higher bid.
- v86 prediction: 4
- v87 prediction: The provided information is not enough to answer the question: The total number of properties viewed before the Brookside townhouse offer is not explicitly stated. Multiple viewings are implied but not quantified

### 0e3b85f1ae5dddca4b328a0f
- question_type: `multi-session`
- question: How many fitness classes do I attend in a typical week?
- gold: 5
- v86 prediction: 5
- v87 prediction: 4

### e9095a025f6dbf39641ff990
- question_type: `multi-session`
- question: How many musical instruments do I currently own?
- gold: I currently own 4 musical instruments. I've had the Fender Stratocaster electric guitar for 5 years, the Yamaha FG800 acoustic guitar for 8 years, the 5-piece Pearl Export drum set for an unspecified amount of time, and the Korg B1 piano for 3 years.
- v86 prediction: 4
- v87 prediction: 3

### 5662691a4bc7b9290f5727a8
- question_type: `multi-session`
- question: How much total money did I spend on attending workshops in the last four months?
- gold: $720
- v86 prediction: 720
- v87 prediction: 500

### b29ecee4bbd616d18f051048
- question_type: `multi-session`
- question: How many different museums or galleries did I visit in December?
- gold: 0. You did not mention visitng any museum in December
- v86 prediction: The provided information is not enough to answer the question: No evidence of any museum or gallery visits in December
- v87 prediction: The provided information is not enough to answer the question: No information about visits to museums or galleries in December

### e9b0f742a1e2300420a4ca02
- question_type: `multi-session`
- question: What is the total distance of the hikes I did on two consecutive weekends?
- gold: 8 miles
- v86 prediction: 8 miles
- v87 prediction: 5 miles

### 34b46e8aabe038118cec7681
- question_type: `multi-session`
- question: What was the approximate increase in Instagram followers I experienced in two weeks?
- gold: 100
- v86 prediction: 100
- v87 prediction: 350

### 128a1895ab851f148bbea790
- question_type: `multi-session`
- question: How many plants did I initially plant for tomatoes and chili peppers?
- gold: The information provided is not enough. You mentioned planting 5 plants for tomatoes but you did not mention chili peppers.
- v86 prediction: The provided information is not enough to answer the question: Information about initial chili pepper plants is not provided
- v87 prediction: The provided information is not enough to answer the question: initial plants for chili peppers

### 2976f637e5d717258b993c04
- question_type: `temporal-reasoning`
- question: I mentioned participating in a sports event two weeks ago. What was the event?
- gold: The company's annual charity soccer tournament.
- v86 prediction: The event was the company's annual charity soccer tournament.
- v87 prediction: The provided information is not enough to answer the question: No memory confirms a sports event from exactly two weeks ago (2023-06-03)

### 2a18e972b47c27c2c1f2fdb8
- question_type: `temporal-reasoning`
- question: How long have I been working before I started my current job at NovaTech?
- gold: 4 years and 9 months
- v86 prediction: 4 years and 9 months
- v87 prediction: The provided information is not enough to determine how long you worked before starting at NovaTech.

### 1f7723fca5c03dfc8ff0e0ca
- question_type: `temporal-reasoning`
- question: How long have I been working before I started my current job at Google?
- gold: The information provided is not enough. From the information provided, You haven't started working at Google yet.
- v86 prediction: The provided information is not enough to determine how long the user has been working before starting their current job at Google.
- v87 prediction: 4 years and 3 months

### 71c309443747c6d8faf4a7d2
- question_type: `temporal-reasoning`
- question: How many days before I bought my iPad did I attend the Holiday Market?
- gold: The information provided is not enough. You mentioned getting the iPhone 13 Pro and attending the market, but you did not mention buying an iPad.
- v86 prediction: The provided information is not enough to answer the question: iPad purchase date
- v87 prediction: 7

### e74a916402e973452dae7af4
- question_type: `knowledge-update`
- question: How many stars do I need to reach the gold level on my Starbucks Rewards app?
- gold: 120
- v86 prediction: 120
- v87 prediction: 125

### 37b842706f89305f735ceb16
- question_type: `knowledge-update`
- question: How long have my parents been staying with me in the US?
- gold: nine months
- v86 prediction: nine months
- v87 prediction: six months

### bfed71c5f7001160a920c1c8
- question_type: `knowledge-update`
- question: Where do I currently keep my old sneakers?
- gold: in a shoe rack in my closet
- v86 prediction: shoe rack in the closet
- v87 prediction: under the bed

### 4b2d65beb209dbf5f2059c19
- question_type: `single-session-assistant`
- question: I was going through our previous conversation about making a classic French omelette, and I wanted to confirm - how many eggs did you say we need for the recipe?
- gold: 2-3 eggs
- v86 prediction: 2-3 eggs
- v87 prediction: 3

### 7623367fb36a659f5152c676
- question_type: `single-session-assistant`
- question: I was looking back at our previous chat and I wanted to confirm, how many times did the Chiefs play the Jaguars at Arrowhead Stadium?
- gold: The Chiefs played the Jaguars 12 times at Arrowhead Stadium.
- v86 prediction: 12
- v87 prediction: 12
