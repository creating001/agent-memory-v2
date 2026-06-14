# Delta Badcases for stage1_structured_guide_row_features_v78_controlled_lme_s_full_dc4ec2e

Offline-only comparison vs v73. Gold and judge labels are used only after prediction.

## Gains

### 79579c32a1b250cf632b717b
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many years in total did I spend in formal education from high school to the completion of my Master's degree?
- gold: The information provided is not enough. You mentioned 4 years in high school (2010-2014), 2 years at PCC (2014-2016), and 4 years at UCLA (2016-2020). But you didn't mention the number of years you spend getting the Master's degree
- v73: 4
- v78: The provided information is not enough.

### acd33e2950f233611481511a
- question_type: `single-session-preference`
- route: `fact_lookup`
- question: I've been feeling a bit stuck with my paintings lately. Do you have any ideas on how I can find new inspiration?
- gold: The user would prefer responses that build upon their existing sources of inspiration, such as revisiting Instagram art accounts or exploring new techniques from online tutorials. They might also appreciate suggestions that revisit previous themes they found enjoyable, like painting flowers. The user would not prefer generic or vague suggestions for finding inspiration, and would likely appreciate responses that utilize their recent 30-day painting challenge experience.
- v73: Try joining a 30-day painting challenge and explore art on social media platforms like Instagram, especially themed content such as flower paintings, to spark new ideas.
- v78: Try joining a 30-day painting challenge and explore art on social media platforms like Instagram, especially themed content such as flower paintings, to spark new ideas.

### 589b37fd0ba97f533c07aa37
- question_type: `single-session-preference`
- route: `fact_lookup`
- question: I'm planning a trip to Denver soon. Any suggestions on what to do there?
- gold: The user would prefer responses that take into account their previous experience in Denver, specifically their interest in live music and memorable encounter with Brandon Flowers. They might appreciate suggestions that revisit or build upon this experience, such as revisiting the same bar or exploring similar music venues in the area. The user may not prefer general tourist recommendations or activities unrelated to their interest in live music.
- v73: Visit Red Rocks Amphitheater and try nearby BBQ restaurants.
- v78: Visit Red Rocks Amphitheater and try nearby BBQ restaurants.

### fd25f68eeef013c491d86a1c
- question_type: `multi-session`
- route: `list_count`
- question: How many antique items did I inherit or acquire from my family members?
- gold: 5
- v73: 3
- v78: 5 antique items: vintage diamond necklace (grandmother), antique music box (great-aunt), set of depression-era glassware (mom), antique tea set (cousin Rachel), vintage typewriter (dad)

### cdde2a2cdd99eb2b49880db5
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many dinner parties have I attended in the past month?
- gold: three
- v73: 2
- v78: 3

### 35751c9236a608dad7491522
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many years older am I than when I graduated from college?
- gold: 7
- v73: The provided information is not enough.
- v78: 7

### 2152374e46762b936b18b5c5
- question_type: `temporal-reasoning`
- route: `temporal_lookup`
- question: What gardening-related activity did I do two weeks ago?
- gold: planting 12 new tomato saplings
- v73: Using a gardening app to track weather and soil moisture levels
- v78: planted 12 new tomato saplings

### 325a0f2d711df68b798236a3
- question_type: `temporal-reasoning`
- route: `temporal_lookup`
- question: What was the airline that I flied with on Valentine's day?
- gold: American Airlines
- v73: The provided information is not enough.
- v78: American Airlines

### 3f1b0d114b185d2ca9d2dc2d
- question_type: `temporal-reasoning`
- route: `temporal_lookup`
- question: How many days before the 'Rack Fest' did I participate in the 'Turbocharged Tuesdays' event?
- gold: 4 days.
- v73: 10
- v78: 4

### 8c6ec8aa7a13c8b4b8ec3d1a
- question_type: `temporal-reasoning`
- route: `temporal_lookup`
- question: How many months ago did I book the Airbnb in San Francisco?
- gold: Five months ago
- v73: 3
- v78: 5

### 767dc4d1e636373a70a888ac
- question_type: `knowledge-update`
- route: `temporal_lookup`
- question: How many autographed baseballs have I added to my collection in the first three months of collection?
- gold: 15
- v73: 20
- v78: 15

### eb0fc843f6bf85c0091a78e1
- question_type: `single-session-assistant`
- route: `list_count`
- question: I was going through our previous chat and I wanted to clarify something about the prayer of beginners in Tanqueray's Spiritual Life treatise. Can you remind me which chapter of the second part discusses vocal prayer and meditation?
- gold: Chapter 4 of Book 1, titled 'Vocal Prayer and Meditation'.
- v73: Chapter 4 of Book 1
- v78: Chapter 4 of Book 1

## Losses

### 81df9103418e931f73ff48af
- question_type: `single-session-user`
- route: `temporal_lookup`
- question: How long is my daily commute to work?
- gold: 45 minutes each way
- v73: 45 minutes each way
- v78: 45 minutes

### 004224772b616dd627a96a35
- question_type: `single-session-user`
- route: `temporal_lookup`
- question: How much time do I dedicate to practicing violin every day?
- gold: You did not mention this information. You mentioned practing guitar everyday, but not violin.
- v73: The provided information is not enough.
- v78: The provided information is not enough.

### 5a37a93ab3c66f6b71a739ad
- question_type: `multi-session`
- route: `list_count`
- question: How many model kits have I worked on or bought?
- gold: I have worked on or bought five model kits. The scales of the models are: Revell F-15 Eagle (scale not mentioned), Tamiya 1/48 scale Spitfire Mk.V, 1/16 scale German Tiger I tank, 1/72 scale B-29 bomber, and 1/24 scale '69 Camaro.
- v73: 5 model kits: Revell F-15 Eagle, 1/72 scale B-29 bomber, 1/24 scale '69 Camaro, 1/16 scale German Tiger I tank, and Tamiya 1/48 scale Spitfire Mk.V
- v78: 15

### e638d9fede2e6278ca0c1061
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many days did I spend on camping trips in the United States this year?
- gold: 8 days.
- v73: 8
- v78: 3

### 25cafcb56c382cbde1cfcb13
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many weeks did it take me to watch all the Marvel Cinematic Universe movies and the main Star Wars films?
- gold: 3.5 weeks
- v73: 3.5 weeks
- v78: 2 weeks

### 0ae3182c3a2b012937a96b9d
- question_type: `multi-session`
- route: `list_count`
- question: How many hours have I spent playing games in total?
- gold: 140 hours
- v73: 140 hours
- v78: 70 hours

### 3327f6bb9f2b962d1187cd6b
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many times did I bake something in the past two weeks?
- gold: 4
- v73: 4
- v78: 5

### b59facfd1cda07ef6a239647
- question_type: `multi-session`
- route: `list_count`
- question: How many doctor's appointments did I go to in March?
- gold: 2
- v73: 2
- v78: 3

### 1afa4fb00c6e7626e63dca62
- question_type: `multi-session`
- route: `temporal_lookup`
- question: How many pieces of jewelry did I acquire in the last two months?
- gold: 3
- v73: 3
- v78: 2

### cadcc65007e9932edef2d0de
- question_type: `multi-session`
- route: `list_count`
- question: How many bikes did I service or plan to service in March?
- gold: 2
- v73: 2
- v78: 12

### 4be721ae00fda00fbb5ac16b
- question_type: `multi-session`
- route: `list_count`
- question: How many kitchen items did I replace or fix?
- gold: I replaced or fixed five items: the kitchen faucet, the kitchen mat, the toaster, the coffee maker, and the kitchen shelves.
- v73: 5
- v78: 5

### 315bf5c6778d6f6615153e3d
- question_type: `multi-session`
- route: `list_count`
- question: How many magazine subscriptions do I currently have?
- gold: 2
- v73: 2
- v78: 1
