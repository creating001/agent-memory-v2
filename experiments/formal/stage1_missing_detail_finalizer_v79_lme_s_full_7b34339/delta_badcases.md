# v79 delta badcases vs v73

只列出预测实际改变的 29 条；judge label 来自离线 DeepSeek，不能进入 prediction。

## 改对：WRONG -> CORRECT (6)

- `42bbbfc59c3c45cd91ee953b` type=`multi-session` route=`temporal_lookup`
  - Q: How many times did I bake egg tarts in the past two weeks?
  - Gold: The information provided is not enough. You did not mention baking egg tarts.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: no mention of baking egg tarts in the past two weeks
- `d00b4949227c41f760b0f64c` type=`multi-session` route=`list_count`
  - Q: How many fish are there in my 30-gallon tank?
  - Gold: The information provided is not enough. You did not mention that you have a 30-gallon tank.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The provided information is about a 20-gallon tank, but the question asks about a 30-gallon tank. No data about fish in a 30-gallon tank is available
- `b6d4bc26da6c5292c4a9645a` type=`multi-session` route=`temporal_lookup`
  - Q: How many days did it take for my iPad case to arrive after I bought it?
  - Gold: The information provided is not enough. You did not mention buying an iPad case.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: iPad case purchase or delivery information
- `fd9c8466eeae910e3c98a97a` type=`multi-session` route=`list_count`
  - Q: How many pages do I have left to read in 'Sapiens'?
  - Gold: The information provided is not enough. You did not mention how many paged do you have left to read in 'Sapiens'.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: Total pages in 'Sapiens' and current page reached in 'Sapiens'
- `128a1895ab851f148bbea790` type=`multi-session` route=`list_count`
  - Q: How many plants did I initially plant for tomatoes and chili peppers?
  - Gold: The information provided is not enough. You mentioned planting 5 plants for tomatoes but you did not mention chili peppers.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: initial plants for chili peppers
- `21d531ffd64bfdf571102b20` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: When did I book the Airbnb in Sacramento?
  - Gold: The information provided is not enough. You only mentioned booking Airbnb in San Francisco.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: location: Sacramento not mentioned in any context; no evidence of Airbnb booking in Sacramento

## 未修复：WRONG -> WRONG (14)

- `995a370e23572760a2fdf6f3` type=`multi-session` route=`temporal_lookup`
  - Q: What time did I go to bed on the day before I had a doctor's appointment?
  - Gold: 2 AM
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: Bedtime on May 17, 2023 (the day before the doctor's appointment) is not mentioned in any memory
- `2a27a0337e415cc76e0b82b3` type=`multi-session` route=`list_count`
  - Q: How many properties did I view before making an offer on the townhouse in the Brookside neighborhood?
  - Gold: I viewed four properties before making an offer on the townhouse in the Brookside neighborhood. The reasons I didn't make an offer on them were: the kitchen of the bungalow needed serious renovation, the property in Ceda
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The total number of properties viewed before the Brookside townhouse offer is not explicitly stated. Multiple viewings are implied but not quantified
- `b29ecee4bbd616d18f051048` type=`multi-session` route=`list_count`
  - Q: How many different museums or galleries did I visit in December?
  - Gold: 0. You did not mention visitng any museum in December
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No information about visits to museums or galleries in December
- `32f0df330fed5b12b138734e` type=`single-session-preference` route=`fact_lookup`
  - Q: I've been having trouble with the battery life on my phone lately. Any tips?
  - Gold: The user would prefer responses that build upon their previous mention of purchasing a portable power bank, such as suggestions on how to optimize its use, like ensuring it's fully charged before use. They might also app
  - v73: The provided information is not enough to answer the question.
  - v79: The provided information is not enough to answer the question: no relevant tips or advice on improving phone battery life
- `b9688f9e7305880c8b79b001` type=`multi-session` route=`temporal_lookup`
  - Q: How many years will I be when my friend Rachel gets married?
  - Gold: 33
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The user's current age or birth year is not provided, making it impossible to calculate their age in 2023
- `aadf2bbaa815bd532a6b2a99` type=`multi-session` route=`temporal_lookup`
  - Q: What time did I reach the clinic on Monday?
  - Gold: 9:00 AM
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The time the user reached the clinic on Monday is not specified in any memory context
- `35751c9236a608dad7491522` type=`multi-session` route=`temporal_lookup`
  - Q: How many years older am I than when I graduated from college?
  - Gold: 7
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: Current age or graduation year to compute the difference in years
- `da21b04c638eb0f5c3b5f842` type=`multi-session` route=`list_count`
  - Q: What was the page count of the two novels I finished in January and March?
  - Gold: 856
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No memory provides the page count of a novel finished in January or March
- `3f61bd57092f90507c37fbeb` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: How many days ago did I attend a baking class at a local culinary school when I made my friend's birthday cake?
  - Gold: 21 days. 22 days (including the last day) is also acceptable.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No memory confirms both the baking class at a local culinary school and the birthday cake being made on the same day. The required event is not fully supported
- `dbfe13e18e9d7d354d881b9b` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: How many weeks in total do I spent on reading 'The Nightingale' and listening to 'Sapiens: A Brief History of Humankind' and 'The Power'?
  - Gold: 2 weeks for 'The Nightingale', 4 weeks for 'Sapiens: A Brief History of Humankind', and 2 weeks for 'The Power', so a total of 8 weeks.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No explicit total duration in weeks is provided; the context lacks a direct statement of total weeks spent on the activities
- `38395512ed74d379096ac16f` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: How many weeks have I been taking sculpting classes when I invested in my own set of sculpting tools?
  - Gold: 3
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The duration of sculpting classes at the time of tool purchase (2023-03-04) is not explicitly stated. The only duration provided (6 weeks) is from the start date, not the purchase date. No other ev
- `043303ed21aae98eeeba9d0e` type=`temporal-reasoning` route=`fact_lookup`
  - Q: I received a piece of jewelry last Saturday from whom?
  - Gold: my aunt
  - v73: unknown
  - v79: The provided information is not enough to answer the question: source of the jewelry received last Saturday
- `325a0f2d711df68b798236a3` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: What was the airline that I flied with on Valentine's day?
  - Gold: American Airlines
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: specific airline flown on Valentine's Day (2023-02-14)
- `047fc041db62b22233bcc704` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: I mentioned an investment for a competition four weeks ago? What did I buy?
  - Gold: I got my own set of sculpting tools.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No mention of a specific investment or purchase made for the competition in the provided memory context

## 保持正确：CORRECT -> CORRECT (9)

- `10396ccd71e93950af629a7d` type=`single-session-user` route=`fact_lookup`
  - Q: What is the name of my hamster?
  - Gold: You did not mention this information. You mentioned your cat Luna but not your hamster.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: hamster name
- `e0f32d2f588af132dcfec445` type=`single-session-user` route=`fact_lookup`
  - Q: What did I bake for my uncle's birthday party?
  - Gold: You did not mention this information. You mentioned baking for your niece's birthday party but not your uncle's
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No memory mentions baking for an uncle's birthday party
- `201171d2c2ac14a0b41dd400` type=`single-session-user` route=`temporal_lookup`
  - Q: How long was I in Korea for?
  - Gold: You did not mention this information. You mentioned staying in Japan, but not in Korea.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No confirmed visit to Korea or duration of stay mentioned
- `004224772b616dd627a96a35` type=`single-session-user` route=`temporal_lookup`
  - Q: How much time do I dedicate to practicing violin every day?
  - Gold: You did not mention this information. You mentioned practing guitar everyday, but not violin.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No information about violin practice duration is available in the memory context
- `45ccdf8947da04d80402bb2e` type=`multi-session` route=`temporal_lookup`
  - Q: How many days did I spend in total traveling in Hawaii and in Seattle?
  - Gold: The information provided is not enough. You mentioned traveling for 10 days in Hawaii but did not mention abything about the trip to Seattle.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: duration of Hawaii trip and any mention of Seattle
- `71c309443747c6d8faf4a7d2` type=`temporal-reasoning` route=`temporal_lookup`
  - Q: How many days before I bought my iPad did I attend the Holiday Market?
  - Gold: The information provided is not enough. You mentioned getting the iPhone 13 Pro and attending the market, but you did not mention buying an iPad.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The date of the iPad purchase is not provided in the context, making it impossible to calculate the number of days between the Holiday Market and the iPad purchase
- `29b6493e3be5226d857ed549` type=`temporal-reasoning` route=`list_count`
  - Q: Which project did I start first, the Ferrari model or the Porsche 991 Turbo S model?
  - Gold: The information provided is not enough. You did not mention starting the Porsche 991 Turbo S model.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: The start date of the Porsche 991 Turbo S model is not provided in the memory context
- `11f7ec1390eca9fb4c56a6ad` type=`knowledge-update` route=`list_count`
  - Q: How many Italian restaurants have I tried in my city?
  - Gold: The information provided is not enough. You mentioned trying Korean restaurants but not Italian restaurants.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: No mention of Italian restaurants or related experiences in the memory context
- `7aca5175762d0438ea896589` type=`knowledge-update` route=`temporal_lookup`
  - Q: How many autographed football have I added to my collection in the first three months of collection?
  - Gold: The information provided is not enough. You mentioned collecting autographed baseball but not football.
  - v73: The provided information is not enough.
  - v79: The provided information is not enough to answer the question: no mention of autographed footballs in the context

## 回退：CORRECT -> WRONG (0)

无。

