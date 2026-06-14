# v81 delta badcases vs v80

只列出预测实际改变的 20 条；judge label 和 gold 只用于离线诊断，不能进入 prediction。

## 总览

- v80 accuracy: 0.792000
- v81 accuracy: 0.790000
- prediction_changed_count: 20
- changed net: 2 (WRONG->CORRECT 3 / CORRECT->WRONG 1)
- unchanged judge variance net: -3
- update_conflict_guide_applied: 44

## 改对：WRONG -> CORRECT (3)

- `ad7ea131cd126de5fca7057a` type=`multi-session` route=`fact_lookup`
  - Q: What is the total cost of Lola's vet visit and flea medication?
  - Gold: $75
  - v80: The total cost cannot be determined with the provided information because the vet visit cost is not specified in the current context.
  - v81: $75
- `7a09015c87580f2e98c3f5cd` type=`multi-session` route=`fact_lookup`
  - Q: What is the total number of comments on my recent Facebook Live session and my most popular YouTube video?
  - Gold: 33
  - v80: 12 comments on the recent Facebook Live session and 21 comments on the most popular YouTube video
  - v81: The total number of comments on your recent Facebook Live session is 12, and your most popular YouTube video has 21 comments.
- `beb0a3bdb35a23a257132b5e` type=`knowledge-update` route=`current_state`
  - Q: Where did I go on my most recent family trip?
  - Gold: Paris
  - v80: Hawaii
  - v81: Paris

## 未修复：WRONG -> WRONG (3)

- `32ebfa2049ba11bbc89d490c` type=`multi-session` route=`fact_lookup`
  - Q: How much will I save by taking the train from the airport to my hotel instead of a taxi?
  - Gold: $50
  - v80: 40
  - v81: $30
- `8a5fdd7024be02ee912f7516` type=`multi-session` route=`fact_lookup`
  - Q: How much will I save by taking the bus from the airport to my hotel instead of a taxi?
  - Gold: The information provided is not enough. You did not mention how much will the bus take.
  - v80: 50
  - v81: $50
- `f42847e71c4d486a8c6c7c0b` type=`temporal-reasoning` route=`current_state`
  - Q: What is the order of airlines I flew with from earliest to latest before today?
  - Gold: JetBlue, Delta, United, American Airlines
  - v80: American Airlines, United Airlines, Spirit Airlines, JetBlue, Delta
  - v81: American Airlines, Spirit Airlines, United Airlines, JetBlue, Delta

## 保持正确：CORRECT -> CORRECT (13)

- `6dd4d1d64d8dd02fa538b1e5` type=`multi-session` route=`fact_lookup`
  - Q: What is the total cost of the new food bowl, measuring cup, dental chews, and flea and tick collar I got for Max?
  - Gold: $50
  - v80: 50
  - v81: $50
- `cb3b331577047a371a7b032a` type=`multi-session` route=`fact_lookup`
  - Q: What is the difference in price between my luxury boots and the similar pair found at the budget store?
  - Gold: $750
  - v80: 750
  - v81: $750
- `5108082226f35be6c6705761` type=`multi-session` route=`fact_lookup`
  - Q: How much did I save on the designer handbag at TK Maxx?
  - Gold: $300
  - v80: 300
  - v81: $300
- `94993cdfe3581baa3f3f280d` type=`multi-session` route=`fact_lookup`
  - Q: What is the minimum amount I could get if I sold the vintage diamond necklace and the antique vanity?
  - Gold: $5,150
  - v80: 5150
  - v81: $5,150
- `0a84427c98275c48b2acd3dd` type=`multi-session` route=`fact_lookup`
  - Q: What is the total cost of the car cover and detailing spray I purchased?
  - Gold: $140
  - v80: 140
  - v81: $140
- `f685467110dd402bd9d31cc9` type=`multi-session` route=`fact_lookup`
  - Q: What is the total distance I covered in my four road trips?
  - Gold: 3,000 miles
  - v80: 3000
  - v81: 3,000 miles
- `2dde93d290bf6754862f5ff1` type=`multi-session` route=`fact_lookup`
  - Q: What is the total time it takes I to get ready and commute to work?
  - Gold: an hour and a half
  - v80: 1 hour and 30 minutes
  - v81: 90 minutes
- `754c7fcd90f79025d3cf38eb` type=`multi-session` route=`fact_lookup`
  - Q: What is the total number of views on my most popular videos on YouTube and TikTok?
  - Gold: 1,998
  - v80: 1998
  - v81: 1,456 views on TikTok and 542 views on YouTube
- `00c7a05a91938a123f46650c` type=`multi-session` route=`fact_lookup`
  - Q: What is the total amount I spent on gifts for my coworker and brother?
  - Gold: $200
  - v80: 200
  - v81: $200
- `6f693bf5b0ef8f66bb2578cd` type=`multi-session` route=`fact_lookup`
  - Q: What is the total amount I spent on the designer handbag and high-end skincare products?
  - Gold: $1,300
  - v80: 1300
  - v81: $1300
- `1e069e9289cee627a448ce10` type=`temporal-reasoning` route=`fact_lookup`
  - Q: What was the first issue I had with my new car after its first service?
  - Gold: GPS system not functioning correctly
  - v80: GPS system issue
  - v81: The first issue was with the car's GPS system, which failed on March 22nd and was replaced by the dealership.
- `ba57c4f922001033e979f087` type=`knowledge-update` route=`current_state`
  - Q: How many engineers do I lead when I just started my new role as Senior Software Engineer? How many engineers do I lead now?
  - Gold: When you just started your new role as Senior Software Engineer, you led 4 engineers. Now, you lead 5 engineers
  - v80: When you just started, you led 4 engineers. Now, you lead 5 engineers.
  - v81: When you just started your new role as Senior Software Engineer, you led 4 engineers. Now, you lead 5 engineers.
- `21fa5c20b675193587f70ed2` type=`knowledge-update` route=`fact_lookup`
  - Q: Before I purchased the gravel bike, do I have other bikes in addition to my mountain bike and my commuter bike?
  - Gold: Yes. (You have a road bike too.)
  - v80: Yes, before purchasing the gravel bike, the user had a road bike in addition to the mountain bike and commuter bike.
  - v81: Yes, before purchasing the gravel bike, you had a road bike in addition to your mountain bike and commuter bike.

## 回退：CORRECT -> WRONG (1)

- `1f7723fca5c03dfc8ff0e0ca` type=`temporal-reasoning` route=`current_state`
  - Q: How long have I been working before I started my current job at Google?
  - Gold: The information provided is not enough. From the information provided, You haven't started working at Google yet.
  - v80: The provided information is not enough to determine how long the user has been working before starting their current job at Google.
  - v81: The provided information is not enough to determine how long you have been working before starting your current job at Google.
