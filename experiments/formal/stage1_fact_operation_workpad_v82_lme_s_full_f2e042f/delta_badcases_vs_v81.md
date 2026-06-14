# v82 delta badcases vs v81

只列出预测实际改变的样本；judge label 和 gold 只用于离线诊断，不能进入 prediction。

## 总览

- v81 accuracy: 0.790000
- v82 accuracy: 0.786000
- prediction_changed_count: 17
- changed net: -1 (WRONG->CORRECT 1 / CORRECT->WRONG 2)
- unchanged judge variance net: -1

## 改对：WRONG -> CORRECT (1)

- `e9b0f742a1e2300420a4ca02` type=`multi-session` route=`fact_lookup`
  - Q: What is the total distance of the hikes I did on two consecutive weekends?
  - Gold: 8 miles
  - v81: 5 miles
  - v82: 8 miles

## 未修复：WRONG -> WRONG (4)

- `27a28d49af7d327bb9f25309` type=`multi-session` route=`fact_lookup`
  - Q: How much more did I spend on accommodations per night in Hawaii compared to Tokyo?
  - Gold: $270
  - v81: The provided information is not enough to determine the exact amount spent more per night in Hawaii compared to Tokyo.
  - v82: The provided information is not enough to answer the question: The exact cost in Hawaii is not specified, only that it exceeds $300. Without a precise figure, the difference cannot be calculated
- `d3ac1e28c2b1b6a9caf140a6` type=`multi-session` route=`fact_lookup`
  - Q: What is the average GPA of my undergraduate and graduate studies?
  - Gold: 3.83
  - v81: The average GPA of undergraduate studies is 3.86, and the average GPA of graduate studies is 3.8.
  - v82: The average GPA of your undergraduate studies is 3.86, and the average GPA of your graduate studies is 3.8.
- `6b1ef73a6f0aefe0de9818c3` type=`temporal-reasoning` route=`fact_lookup`
  - Q: What is the order of the sports events I watched in January?
  - Gold: First, I attended a NBA game at the Staples Center, then I watched the College Football National Championship game, and finally, I watched the NFL playoffs.
  - v81: 1. Lakers vs. Chicago Bulls game on January 5, 2023; 2. College Football National Championship game on January 15, 2023
  - v82: College Football National Championship game, NFL Divisional Round game
- `11412181e33c0f68f50ad52b` type=`knowledge-update` route=`fact_lookup`
  - Q: What new kitchen gadget did I invest in before getting the Air Fryer?
  - Gold: Instant Pot
  - v81: a high-tech gadget
  - v82: The provided information is not enough to answer the question: No memory explicitly names a kitchen gadget purchased before the Air Fryer

## 保持正确：CORRECT -> CORRECT (10)

- `8f38a58178ff39b854ccbf44` type=`multi-session` route=`fact_lookup`
  - Q: What is the total amount of money I earned from selling my products at the markets?
  - Gold: $495
  - v81: 495
  - v82: $495
- `66458ef717e5c0cd5714a9de` type=`multi-session` route=`fact_lookup`
  - Q: Did I receive a higher percentage discount on my first order from HelloFresh, compared to my first UberEats order?
  - Gold: Yes.
  - v81: Yes
  - v82: Yes, you received a higher percentage discount on your first HelloFresh order (40%) compared to your first UberEats order (20%).
- `be08cd5546ba80a459c181e6` type=`multi-session` route=`fact_lookup`
  - Q: How much more did I have to pay for the trip after the initial quote?
  - Gold: $300
  - v81: 300
  - v82: $300
- `754c7fcd90f79025d3cf38eb` type=`multi-session` route=`fact_lookup`
  - Q: What is the total number of views on my most popular videos on YouTube and TikTok?
  - Gold: 1,998
  - v81: 1,456 views on TikTok and 542 views on YouTube
  - v82: 1998
- `7a09015c87580f2e98c3f5cd` type=`multi-session` route=`fact_lookup`
  - Q: What is the total number of comments on my recent Facebook Live session and my most popular YouTube video?
  - Gold: 33
  - v81: The total number of comments on your recent Facebook Live session is 12, and your most popular YouTube video has 21 comments.
  - v82: 12 comments on the recent Facebook Live session and 21 comments on the most popular YouTube video
- `cf838617945ef6dd5954945a` type=`multi-session` route=`fact_lookup`
  - Q: What is the total cost of my recently purchased headphones and the iPad?
  - Gold: The information provided is not enough. You mentioned purchasing a headphone, but you did not mention the iPad.
  - v81: The provided information is not enough to determine the total cost, as the iPad's cost is not mentioned.
  - v82: The provided information is not enough to answer the question: cost of iPad; no mention of iPad purchase or price in any memory context
- `40deaf4d8c42d319e90a5514` type=`temporal-reasoning` route=`fact_lookup`
  - Q: What is the order of the three events: 'I signed up for the rewards program at ShopRite', 'I used a Buy One Get One Free coupon on Luvs diapers at Walmart', and 'I redeemed $12 cashback for a $10 Amazon gift card from Ibotta'?
  - Gold: First, I used a Buy One Get One Free coupon on Luvs diapers at Walmart. Then, I redeemed $12 cashback for a $10 Amazon gift card from Ibotta. Finally, I signed up for the rewards program at ShopRite.
  - v81: 1. I used a Buy One Get One Free coupon on Luvs diapers at Walmart (2023-04-01), 2. I redeemed $12 cashback for a $10 Amazon gift card from Ibotta (2023-04-10), 3. I signed up for the rewards program at ShopRite (2023-04-15)
  - v82: 1. I used a Buy One Get One Free coupon on Luvs diapers at Walmart. 2. I redeemed $12 cashback for a $10 Amazon gift card from Ibotta. 3. I signed up for the rewards program at ShopRite.
- `4bf2ae911b43d202c626a73d` type=`temporal-reasoning` route=`fact_lookup`
  - Q: Who graduated first, second and third among Emma, Rachel and Alex?
  - Gold: Emma graduated first, followed by Rachel and then Alex.
  - v81: First: Emma, Second: Rachel, Third: Alex
  - v82: Emma graduated first, Rachel second, and Alex third.
- `21fa5c20b675193587f70ed2` type=`knowledge-update` route=`fact_lookup`
  - Q: Before I purchased the gravel bike, do I have other bikes in addition to my mountain bike and my commuter bike?
  - Gold: Yes. (You have a road bike too.)
  - v81: Yes, before purchasing the gravel bike, you had a road bike in addition to your mountain bike and commuter bike.
  - v82: Yes, before purchasing the gravel bike, the user had a road bike in addition to the mountain bike and commuter bike.
- `8b9b60767b8d7d8f7b79b33a` type=`single-session-assistant` route=`fact_lookup`
  - Q: I remember you told me about the refining processes at CITGO's three refineries earlier. Can you remind me what kind of processes are used at the Lake Charles Refinery?
  - Gold: Atmospheric distillation, fluid catalytic cracking (FCC), alkylation, and hydrotreating.
  - v81: Atmospheric distillation, Fluid catalytic cracking (FCC), Alkylation, Hydrotreating
  - v82: atmospheric distillation, fluid catalytic cracking (FCC), alkylation, hydrotreating

## 回退：CORRECT -> WRONG (2)

- `1e069e9289cee627a448ce10` type=`temporal-reasoning` route=`fact_lookup`
  - Q: What was the first issue I had with my new car after its first service?
  - Gold: GPS system not functioning correctly
  - v81: The first issue was with the car's GPS system, which failed on March 22nd and was replaced by the dealership.
  - v82: The first issue was with the car's GPS system.
- `6eb23a13d4004c3cfd395d74` type=`knowledge-update` route=`fact_lookup`
  - Q: Where did Rachel move to after her recent relocation?
  - Gold: the suburbs
  - v81: the suburbs
  - v82: The provided information is not enough to answer the question: The specific suburb Rachel moved to is not mentioned in any memory, so the exact destination cannot be determined
